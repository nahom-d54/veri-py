"""Typed request/response models for verification services."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class VerifyResult(BaseModel):
    """TS-compatible CBE/Abyssinia result contract."""

    success: bool
    payer: str | None = None
    payerAccount: str | None = None
    receiver: str | None = None
    receiverAccount: str | None = None
    amount: float | None = None
    date: datetime | None = None
    reference: str | None = None
    reason: str | None = None
    error: str | None = None


class DashenVerifyResult(BaseModel):
    """TS-compatible Dashen receipt model."""

    success: bool
    senderName: str | None = None
    senderAccountNumber: str | None = None
    transactionChannel: str | None = None
    serviceType: str | None = None
    narrative: str | None = None
    receiverName: str | None = None
    phoneNo: str | None = None
    institutionName: str | None = None
    transactionReference: str | None = None
    transferReference: str | None = None
    transactionDate: datetime | None = None
    transactionAmount: float | None = None
    serviceCharge: float | None = None
    exciseTax: float | None = None
    vat: float | None = None
    penaltyFee: float | None = None
    incomeTaxFee: float | None = None
    interestFee: float | None = None
    stampDuty: float | None = None
    discountAmount: float | None = None
    total: float | None = None
    error: str | None = None


class MpesaVerifyResult(BaseModel):
    """TS-compatible M-Pesa verification model."""

    success: bool
    payerName: str | None = None
    payerAccount: str | None = None
    receiverName: str | None = None
    receiverAccount: str | None = None
    transactionId: str | None = None
    receiptNo: str | None = None
    paymentDate: datetime | None = None
    amount: float | None = None
    serviceFee: float | None = None
    vat: float | None = None
    error: str | None = None


class TelebirrReceipt(BaseModel):
    """TS-compatible Telebirr receipt model."""

    payerName: str = ""
    payerTelebirrNo: str = ""
    creditedPartyName: str = ""
    creditedPartyAccountNo: str = ""
    transactionStatus: str = ""
    receiptNo: str = ""
    paymentDate: str = ""
    settledAmount: str = ""
    serviceFee: str = ""
    serviceFeeVAT: str = ""
    totalPaidAmount: str = ""
    bankName: str = ""


class CBEBirrReceipt(BaseModel):
    """TS-compatible CBE Birr receipt model."""

    customerName: str = ""
    debitAccount: str = ""
    creditAccount: str = ""
    receiverName: str = ""
    orderId: str = ""
    transactionStatus: str = ""
    reference: str = ""
    receiptNumber: str = ""
    transactionDate: str = ""
    amount: str = ""
    paidAmount: str = ""
    serviceCharge: str = ""
    vat: str = ""
    totalPaidAmount: str = ""
    paymentReason: str = ""
    paymentChannel: str = ""


class CBEBirrError(BaseModel):
    """Error shape returned by CBE Birr verifier when parsing/fetching fails."""

    success: Literal[False] = False
    error: str


class ReceiptType(StrEnum):
    """Supported image-detected receipt types."""

    TELEBIRR = "telebirr"
    CBE = "cbe"


class ImageDetectionResult(BaseModel):
    """Structured vision model output for receipt type and reference fields."""

    type: ReceiptType
    transaction_id: str | None = None
    transaction_number: str | None = None


class ImageForwardResult(BaseModel):
    """Response shape when auto-verify is disabled."""

    type: ReceiptType
    reference: str
    forward_to: str
    accountSuffix: str | None = None


class ImageAutoVerifyResult(BaseModel):
    """Response shape when auto-verify is enabled and succeeds."""

    verified: Literal[True] = True
    type: ReceiptType
    reference: str
    details: VerifyResult | TelebirrReceipt | None


class ImageErrorResult(BaseModel):
    """Error response for image verification flows."""

    success: Literal[False] = False
    error: str
    details: str | None = None


class CBERequest(BaseModel):
    """Typed input contract for CBE verification."""

    reference: str = Field(min_length=12, max_length=12)
    accountSuffix: str = Field(min_length=8, max_length=8, pattern=r"^\d{8}$")


class AbyssiniaRequest(BaseModel):
    """Typed input contract for Abyssinia verification."""

    reference: str = Field(min_length=12, max_length=12)
    suffix: str = Field(min_length=5, max_length=5, pattern=r"^\d{5}$")


class TelebirrRequest(BaseModel):
    """Typed input contract for Telebirr verification."""

    reference: str = Field(min_length=10, max_length=32)


class DashenRequest(BaseModel):
    """Typed input contract for Dashen verification."""

    reference: str = Field(min_length=8, max_length=64)


class MpesaRequest(BaseModel):
    """Typed input contract for M-Pesa verification."""

    reference: str = Field(min_length=6, max_length=64)


class CBEBirrRequest(BaseModel):
    """Typed input contract for CBE Birr verification."""

    receiptNumber: str = Field(min_length=10, max_length=32)
    phoneNumber: str = Field(pattern=r"^251\d{9}$")
    apiKey: str = Field(min_length=6)
