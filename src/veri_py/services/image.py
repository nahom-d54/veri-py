"""Image receipt detection and optional auto-verification service."""

from __future__ import annotations

import base64

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ParsedChatCompletion

from ..core.config import VerifierSettings
from ..exceptions import ConfigurationError
from ..models import (
    ImageAutoVerifyResult,
    ImageDetectionResult,
    ImageErrorResult,
    ImageForwardResult,
    ReceiptType,
)
from .cbe import CBEService
from .telebirr import TelebirrService


class ImageService:
    """Analyze receipt images and optionally auto-verify detected references."""

    def __init__(
        self,
        settings: VerifierSettings,
        cbe_service: CBEService,
        telebirr_service: TelebirrService,
    ) -> None:
        self.settings = settings
        self.cbe_service = cbe_service
        self.telebirr_service = telebirr_service
        self._openai_async: AsyncOpenAI | None = None
        self._openai_sync: OpenAI | None = None

    def _async_openai_client(self) -> AsyncOpenAI:
        if self._openai_async is None:
            self._openai_async = AsyncOpenAI(
                api_key=self._openai_key(),
                base_url=self.settings.openai_base_url,
            )
        return self._openai_async

    def _sync_openai_client(self) -> OpenAI:
        if self._openai_sync is None:
            self._openai_sync = OpenAI(
                api_key=self._openai_key(),
                base_url=self.settings.openai_base_url,
            )
        return self._openai_sync

    async def verify(
        self,
        image_bytes: bytes,
        *,
        auto_verify: bool = False,
        account_suffix: str | None = None,
    ) -> ImageAutoVerifyResult | ImageForwardResult | ImageErrorResult:
        """Analyze image asynchronously and optionally auto-verify."""
        try:
            detection = await self._detect_async(image_bytes)
        except Exception as exc:
            return ImageErrorResult(error="Failed to detect receipt type from image.", details=str(exc))

        return await self._route_async(detection, auto_verify=auto_verify, account_suffix=account_suffix)

    def verify_sync(
        self,
        image_bytes: bytes,
        *,
        auto_verify: bool = False,
        account_suffix: str | None = None,
    ) -> ImageAutoVerifyResult | ImageForwardResult | ImageErrorResult:
        """Analyze image synchronously and optionally auto-verify."""
        try:
            detection = self._detect_sync(image_bytes)
        except Exception as exc:
            return ImageErrorResult(error="Failed to detect receipt type from image.", details=str(exc))

        return self._route_sync(detection, auto_verify=auto_verify, account_suffix=account_suffix)

    async def _detect_async(self, image_bytes: bytes) -> ImageDetectionResult:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{encoded}"
        prompt = self._vision_prompt()
        completion = await self._async_openai_client().beta.chat.completions.parse(
            model=self.settings.openai_vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            response_format=ImageDetectionResult,
        )
        return self._parsed_or_raise(completion)

    def _detect_sync(self, image_bytes: bytes) -> ImageDetectionResult:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{encoded}"
        prompt = self._vision_prompt()
        completion = self._sync_openai_client().beta.chat.completions.parse(
            model=self.settings.openai_vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            response_format=ImageDetectionResult,
        )
        return self._parsed_or_raise(completion)

    @staticmethod
    def _parsed_or_raise(completion: ParsedChatCompletion[ImageDetectionResult]) -> ImageDetectionResult:
        msg = completion.choices[0].message
        refusal = getattr(msg, "refusal", None)
        if refusal:
            raise ValueError(str(refusal))
        parsed = getattr(msg, "parsed", None)
        if parsed is None:
            raise ValueError("Invalid OCR response")
        if isinstance(parsed, ImageDetectionResult):
            return parsed
        return ImageDetectionResult.model_validate(parsed)

    @staticmethod
    def _vision_prompt() -> str:
        return (
            "You are a payment receipt analyzer. Based on the uploaded image, determine:\n"
            "- If the receipt was issued by Telebirr or the Commercial Bank of Ethiopia (CBE).\n"
            "- If it's a CBE receipt, extract the transaction ID (usually starts with 'FT').\n"
            "- If it's a Telebirr receipt, extract the transaction number (usually starts with 'CE').\n\n"
            "Fill the structured fields accordingly."
        )

    def _openai_key(self) -> str:
        if not self.settings.openai_api_key:
            raise ConfigurationError("VERI_OPENAI_API_KEY is required for image verification")
        return self.settings.openai_api_key

    async def _route_async(
        self,
        detection: ImageDetectionResult,
        *,
        auto_verify: bool,
        account_suffix: str | None,
    ) -> ImageAutoVerifyResult | ImageForwardResult | ImageErrorResult:
        if detection.type == ReceiptType.TELEBIRR and detection.transaction_number:
            if auto_verify:
                telebirr_details = await self.telebirr_service.verify(detection.transaction_number)
                return ImageAutoVerifyResult(
                    type=ReceiptType.TELEBIRR,
                    reference=detection.transaction_number,
                    details=telebirr_details,
                )

            return ImageForwardResult(
                type=ReceiptType.TELEBIRR,
                reference=detection.transaction_number,
                forward_to="/verify-telebirr",
            )

        if detection.type == ReceiptType.CBE and detection.transaction_id:
            if auto_verify:
                if not account_suffix:
                    return ImageErrorResult(
                        error="Account suffix is required for CBE verification in autoVerify mode",
                    )
                cbe_details = await self.cbe_service.verify(detection.transaction_id, account_suffix)
                return ImageAutoVerifyResult(
                    type=ReceiptType.CBE,
                    reference=detection.transaction_id,
                    details=cbe_details,
                )

            return ImageForwardResult(
                type=ReceiptType.CBE,
                reference=detection.transaction_id,
                forward_to="/verify-cbe",
                accountSuffix="required_from_user",
            )

        return ImageErrorResult(error="Unknown or unrecognized receipt type")

    def _route_sync(
        self,
        detection: ImageDetectionResult,
        *,
        auto_verify: bool,
        account_suffix: str | None,
    ) -> ImageAutoVerifyResult | ImageForwardResult | ImageErrorResult:
        if detection.type == ReceiptType.TELEBIRR and detection.transaction_number:
            if auto_verify:
                telebirr_details = self.telebirr_service.verify_sync(detection.transaction_number)
                return ImageAutoVerifyResult(
                    type=ReceiptType.TELEBIRR,
                    reference=detection.transaction_number,
                    details=telebirr_details,
                )

            return ImageForwardResult(
                type=ReceiptType.TELEBIRR,
                reference=detection.transaction_number,
                forward_to="/verify-telebirr",
            )

        if detection.type == ReceiptType.CBE and detection.transaction_id:
            if auto_verify:
                if not account_suffix:
                    return ImageErrorResult(
                        error="Account suffix is required for CBE verification in autoVerify mode",
                    )
                cbe_details = self.cbe_service.verify_sync(detection.transaction_id, account_suffix)
                return ImageAutoVerifyResult(
                    type=ReceiptType.CBE,
                    reference=detection.transaction_id,
                    details=cbe_details,
                )

            return ImageForwardResult(
                type=ReceiptType.CBE,
                reference=detection.transaction_id,
                forward_to="/verify-cbe",
                accountSuffix="required_from_user",
            )

        return ImageErrorResult(error="Unknown or unrecognized receipt type")
