"""PDF extraction and provider-specific parser functions."""

from __future__ import annotations

import io
import re

from pypdf import PdfReader

from ..models import CBEBirrReceipt, DashenVerifyResult, MpesaVerifyResult, VerifyResult
from .common import normalize_whitespace, parse_amount, parse_datetime_flexible, title_case


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return normalize_whitespace(text)


def parse_cbe_receipt_text(raw_text: str) -> VerifyResult:
    """Parse CBE receipt text into TS-compatible VerifyResult."""
    payer_name = _match_group(raw_text, r"Payer\s*:?\s*(.*?)\s+Account")
    receiver_name = _match_group(raw_text, r"Receiver\s*:?\s*(.*?)\s+Account")

    account_matches = re.findall(r"Account\s*:?\s*([A-Z0-9]?\*{4}\d{4})", raw_text, flags=re.IGNORECASE)
    payer_account = account_matches[0] if len(account_matches) >= 1 else None
    receiver_account = account_matches[1] if len(account_matches) >= 2 else None

    reason = _match_group(
        raw_text,
        r"Reason\s*/\s*Type of service\s*:?\s*(.*?)\s+Transferred Amount",
    )
    amount_text = _match_group(raw_text, r"Transferred Amount\s*:?\s*([\d,]+\.\d{2})\s*ETB")
    reference = _match_group(raw_text, r"Reference No\.?\s*\(VAT Invoice No\)\s*:?\s*([A-Z0-9]+)")
    date_raw = _match_group(raw_text, r"Payment Date & Time\s*:?\s*([\d/,: ]+[APM]{2})")

    amount = parse_amount(amount_text)
    date = parse_datetime_flexible(date_raw)

    result = VerifyResult(
        success=bool(payer_name and payer_account and receiver_name and receiver_account and amount is not None and date is not None and reference),
        payer=title_case(payer_name),
        payerAccount=payer_account,
        receiver=title_case(receiver_name),
        receiverAccount=receiver_account,
        amount=amount,
        date=date,
        reference=reference,
        reason=reason,
    )

    if not result.success:
        result.error = "Could not extract all required fields from PDF."
    return result


def parse_dashen_receipt_text(raw_text: str) -> DashenVerifyResult:
    """Parse Dashen receipt text into TS-compatible DashenVerifyResult."""
    sender_name = _match_group(raw_text, r"Sender\s*Name\s*:?\s*(.*?)\s+(?:Sender\s*Account|Account)")
    sender_account = _match_group(raw_text, r"Sender\s*Account\s*(?:Number)?\s*:?\s*([A-Z0-9\*\-]+)")
    tx_channel = _match_group(raw_text, r"Transaction\s*Channel\s*:?\s*(.*?)\s+(?:Service|Type)")
    service_type = _match_group(raw_text, r"Service\s*Type\s*:?\s*(.*?)\s+(?:Narrative|Description)")
    narrative = _match_group(raw_text, r"Narrative\s*:?\s*(.*?)\s+(?:Receiver|Phone)")
    receiver_name = _match_group(raw_text, r"Receiver\s*Name\s*:?\s*(.*?)\s+(?:Phone|Institution)")
    phone_no = _match_group(raw_text, r"Phone\s*(?:No\.?|Number)?\s*:?\s*([\+\d\-\s]+)")
    institution_name = _match_group(raw_text, r"Institution\s*Name\s*:?\s*(.*?)\s+(?:Transaction|Reference)")
    tx_ref = _match_group(raw_text, r"Transaction\s*Reference\s*:?\s*([A-Z0-9\-]+)")
    transfer_ref = _match_group(raw_text, r"Transfer\s*Reference\s*:?\s*([A-Z0-9\-]+)")
    date_raw = _match_group(
        raw_text,
        r"Transaction\s*Date\s*(?:&\s*Time)?\s*:?\s*([\d/\-,: ]+(?:[APM]{2})?)",
    )

    transaction_amount = _extract_amount(raw_text, r"Transaction\s*Amount\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    service_charge = _extract_amount(raw_text, r"Service\s*Charge\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    excise_tax = _extract_amount(raw_text, r"Excise\s*Tax\s*(?:\(15%\))?\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    vat = _extract_amount(raw_text, r"VAT\s*(?:\(15%\))?\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    penalty_fee = _extract_amount(raw_text, r"Penalty\s*Fee\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    income_tax_fee = _extract_amount(raw_text, r"Income\s*Tax\s*Fee\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    interest_fee = _extract_amount(raw_text, r"Interest\s*Fee\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    stamp_duty = _extract_amount(raw_text, r"Stamp\s*Duty\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    discount_amount = _extract_amount(raw_text, r"Discount\s*Amount\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")
    total = _extract_amount(raw_text, r"Total\s*(?:ETB|Birr)?\s*([\d,]+\.?\d*)")

    success = bool(tx_ref and transaction_amount is not None)

    return DashenVerifyResult(
        success=success,
        senderName=title_case(sender_name),
        senderAccountNumber=sender_account,
        transactionChannel=tx_channel,
        serviceType=service_type,
        narrative=narrative,
        receiverName=title_case(receiver_name),
        phoneNo=phone_no,
        institutionName=title_case(institution_name),
        transactionReference=tx_ref,
        transferReference=transfer_ref,
        transactionDate=parse_datetime_flexible(date_raw),
        transactionAmount=transaction_amount,
        serviceCharge=service_charge,
        exciseTax=excise_tax,
        vat=vat,
        penaltyFee=penalty_fee,
        incomeTaxFee=income_tax_fee,
        interestFee=interest_fee,
        stampDuty=stamp_duty,
        discountAmount=discount_amount,
        total=total,
        error=None if success else "Could not extract required fields (Transaction Reference and Amount) from PDF.",
    )


def parse_mpesa_receipt_text(raw_text: str) -> MpesaVerifyResult:
    """Parse M-Pesa receipt text into TS-compatible MpesaVerifyResult."""
    payer_name = _match_group(
        raw_text,
        r"PAYER NAME\s+(.*?)\s+(?:PAYER PHONE|00\d+|Addis Ababa|\+251|የከፋይ ስም)",
    )
    payer_phone = _match_group(raw_text, r"PAYER PHONE NUMBER\s+(\d+)")
    transaction_id = _match_group(raw_text, r"TRANSACTION ID\s+([A-Z0-9]+)")
    receipt_no = _match_group(raw_text, r"RECEIPT NO.*?([A-Z0-9]{10,})(?:202\d)")
    amount_text = _match_group(raw_text, r"TOTAL\s+([\d,]+\.\d{2})")
    service_fee_text = _match_group(raw_text, r"([\d,]+\.\d{2})\s*Birr\s*/\s*SERVICE FEE")
    vat_text = _match_group(raw_text, r"SERVICE FEE\s*/\s*([\d,]+\.\d{2})\s*.*?\+ 15% VAT")
    date_raw = _match_group(raw_text, r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})")
    receiver_name = _match_group(raw_text, r"RECEIVER NAME.*?(?:የተቀባዩ ቢዝነስ ስም)?\s+([A-Za-z\s]+?)\s+/")
    receiver_phone = _match_group(raw_text, r"RECEIVER NUMBER\s+(\d+)")

    if not receiver_phone:
        receiver_phone = _match_group(raw_text, r"TOTAL\s+[\d,]+\.\d{2}\s+(\d{9,12})")

    if payer_name:
        payer_name = re.sub(r"\d+.*", "", payer_name).strip()

    vat = parse_amount(vat_text)
    if vat is None and service_fee_text and re.search(r"/ \+ 15% VAT", raw_text):
        vat = 0.0

    return MpesaVerifyResult(
        success=True,
        payerName=title_case(payer_name),
        payerAccount=payer_phone,
        receiverName=title_case(receiver_name),
        receiverAccount=receiver_phone,
        transactionId=transaction_id,
        receiptNo=receipt_no,
        paymentDate=parse_datetime_flexible(date_raw),
        amount=parse_amount(amount_text),
        serviceFee=parse_amount(service_fee_text),
        vat=vat,
    )


def parse_cbebirr_receipt_text(pdf_text: str) -> CBEBirrReceipt | None:
    """Parse CBE Birr receipt text into TS-compatible CBEBirrReceipt."""
    customer_name = _match_group(pdf_text, r"Sub city:[\s\n]+([A-Z\s]+?)[\s\n]+Wereda/kebele:") or ""

    debit_account_match = re.search(
        r"Debit Account\s*(Org Account|[\s\S]*?)(?=\s*Credit Account)",
        pdf_text,
        flags=re.IGNORECASE,
    )
    debit_account = debit_account_match.group(1).replace("\n", " ").strip() if debit_account_match else ""

    credit_account = _match_group(pdf_text, r"Credit Account\s*([\s\S]*?)(?=\s*Receiver Name)") or ""
    receiver_name = _match_group(pdf_text, r"Receiver Name\s*([\s\S]*?)(?=\s*Order ID)") or ""
    order_id = _match_group(pdf_text, r"Order ID\s*([A-Z0-9]+)") or ""
    tx_status = _match_group(pdf_text, r"Transaction Status\s*([a-zA-Z]+)") or ""

    ref_match = re.search(
        r"Reference[\s:]*([\s\S]*?)(?=\s*(?:Transaction Details|Receipt Number|የኢትዮጵያ|Commercial Bank))",
        pdf_text,
        flags=re.IGNORECASE,
    )
    reference = ref_match.group(1).replace("\n", " ").strip() if ref_match else ""
    reference = re.sub(r"^[\s:]+|[\s:]+$", "", reference)

    receipt_data_match = re.search(r"([A-Z0-9]{10})(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})([\d.]+)", pdf_text)
    receipt_number = receipt_data_match.group(1) if receipt_data_match else ""
    transaction_date = receipt_data_match.group(2) if receipt_data_match else ""
    amount = receipt_data_match.group(3) if receipt_data_match else ""

    financial_match = re.search(r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+Paid amount", pdf_text)
    paid_amount = financial_match.group(1) if financial_match else ""
    service_charge = financial_match.group(2) if financial_match else ""
    vat = financial_match.group(3) if financial_match else ""
    total_paid_amount = financial_match.group(4) if financial_match else ""

    payment_match = re.search(r"Payment Channel[\s\n]+([^\n]+)[\s\n]+([^\n]+)[\s\n]+([^\n]+)", pdf_text, flags=re.IGNORECASE)
    payment_reason = payment_match.group(2).strip() if payment_match else ""
    payment_channel = payment_match.group(3).strip() if payment_match else ""

    parsed = CBEBirrReceipt(
        customerName=customer_name,
        debitAccount=debit_account,
        creditAccount=credit_account,
        receiverName=receiver_name,
        orderId=order_id,
        transactionStatus=tx_status,
        reference=reference,
        receiptNumber=receipt_number,
        transactionDate=transaction_date,
        amount=amount,
        paidAmount=paid_amount,
        serviceCharge=service_charge,
        vat=vat,
        totalPaidAmount=total_paid_amount,
        paymentReason=payment_reason,
        paymentChannel=payment_channel,
    )

    if not parsed.customerName and not parsed.receiptNumber and not parsed.amount:
        return None

    return parsed


def _match_group(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).replace("\n", " ").strip()


def _extract_amount(text: str, pattern: str) -> float | None:
    matched = _match_group(text, pattern)
    return parse_amount(matched)
