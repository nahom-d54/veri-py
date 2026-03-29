"""Telebirr HTML/JSON parsing helpers."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from ..models import TelebirrReceipt


def parse_telebirr_html(html: str) -> TelebirrReceipt:
    """Extract Telebirr receipt fields from HTML content."""
    soup = BeautifulSoup(html, "html.parser")

    settled_amount = _extract_settled_amount_regex(html) or _get_next_cell_text(
        soup,
        "የተከፈለው መጠን/Settled Amount",
    )
    service_fee = _extract_service_fee_regex(html) or _get_next_cell_text(
        soup,
        "የአገልግሎት ክፍያ/Service fee",
    )

    credited_party_name = _extract_with_regex(html, "የገንዘብ ተቀባይ ስም/Credited Party name") or _get_next_cell_text(
        soup,
        "የገንዘብ ተቀባይ ስም/Credited Party name",
    )
    credited_party_account_no = _extract_with_regex(
        html,
        "የገንዘብ ተቀባይ ቴሌብር ቁ./Credited party account no",
    ) or _get_next_cell_text(soup, "የገንዘብ ተቀባይ ቴሌብር ቁ./Credited party account no")

    bank_name = ""
    bank_account_number_raw = _extract_with_regex(
        html,
        "የባንክ አካውንት ቁጥር/Bank account number",
    ) or _get_next_cell_text(soup, "የባንክ አካውንት ቁጥር/Bank account number")

    if bank_account_number_raw:
        bank_name = credited_party_name
        bank_match = re.search(r"(\d+)\s+(.*)", bank_account_number_raw)
        if bank_match:
            credited_party_account_no = bank_match.group(1).strip()
            credited_party_name = bank_match.group(2).strip()

    return TelebirrReceipt(
        payerName=_extract_with_regex(html, "የከፋይ ስም/Payer Name") or _get_next_cell_text(soup, "የከፋይ ስም/Payer Name"),
        payerTelebirrNo=_extract_with_regex(html, "የከፋይ ቴሌብር ቁ./Payer telebirr no.") or _get_next_cell_text(soup, "የከፋይ ቴሌብር ቁ./Payer telebirr no."),
        creditedPartyName=credited_party_name,
        creditedPartyAccountNo=credited_party_account_no,
        transactionStatus=_extract_with_regex(html, "የክፍያው ሁኔታ/transaction status") or _get_next_cell_text(soup, "የክፍያው ሁኔታ/transaction status"),
        receiptNo=_extract_receipt_no_regex(html) or _get_next_cell_text(soup, "የክፍያ ቁጥር/Receipt No."),
        paymentDate=_extract_date_regex(html) or _get_next_cell_text(soup, "የክፍያ ቀን/Payment date"),
        settledAmount=settled_amount,
        serviceFee=service_fee,
        serviceFeeVAT=_extract_with_regex(html, "የአገልግሎት ክፍያ ተ.እ.ታ/Service fee VAT") or _get_next_cell_text(soup, "የአገልግሎት ክፍያ ተ.እ.ታ/Service fee VAT"),
        totalPaidAmount=_extract_with_regex(html, "ጠቅላላ የተከፈለ/Total Paid Amount") or _get_next_cell_text(soup, "ጠቅላላ የተከፈለ/Total Paid Amount"),
        bankName=bank_name,
    )


def parse_telebirr_json(payload: dict[str, Any]) -> TelebirrReceipt | None:
    """Parse Telebirr JSON payload returned by fallback proxy."""
    if not payload or not payload.get("success") or "data" not in payload:
        return None

    data = payload.get("data", {})
    return TelebirrReceipt(
        payerName=str(data.get("payerName", "")),
        payerTelebirrNo=str(data.get("payerTelebirrNo", "")),
        creditedPartyName=str(data.get("creditedPartyName", "")),
        creditedPartyAccountNo=str(data.get("creditedPartyAccountNo", "")),
        transactionStatus=str(data.get("transactionStatus", "")),
        receiptNo=str(data.get("receiptNo", "")),
        paymentDate=str(data.get("paymentDate", "")),
        settledAmount=str(data.get("settledAmount", "")),
        serviceFee=str(data.get("serviceFee", "")),
        serviceFeeVAT=str(data.get("serviceFeeVAT", "")),
        totalPaidAmount=str(data.get("totalPaidAmount", "")),
        bankName=str(data.get("bankName", "")),
    )


def is_valid_telebirr_receipt(receipt: TelebirrReceipt | None) -> bool:
    """Check for essential Telebirr fields."""
    if receipt is None:
        return False
    return bool(receipt.receiptNo and receipt.payerName and receipt.transactionStatus)


def _extract_settled_amount_regex(html: str) -> str:
    patterns = [
        r"የተከፈለው\s+መጠን/Settled\s+Amount.*?</td>\s*<td[^>]*>\s*(\d+(?:\.\d{2})?\s+Birr)",
        r"<tr[^>]*>.*?የተከፈለው\s+መጠን/Settled\s+Amount.*?<td[^>]*>\s*(\d+(?:\.\d{2})?\s+Birr)",
        r"Settled\s+Amount.*?(\d+(?:\.\d{2})?\s+Birr)",
        r"የክፍያ\s+ዝርዝር/Transaction\s+details.*?<tr[^>]*>.*?<td[^>]*>\s*[^<]*</td>\s*<td[^>]*>\s*[^<]*</td>\s*<td[^>]*>\s*(\d+(?:\.\d{2})?\s+Birr)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


def _extract_service_fee_regex(html: str) -> str:
    pattern = r"የአገልግሎት\s+ክፍያ/Service\s+fee(?!\s+ተ\.እ\.ታ).*?</td>\s*<td[^>]*>\s*(\d+(?:\.\d{2})?\s+Birr)"
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_receipt_no_regex(html: str) -> str:
    pattern = r"<td[^>]*class=\"[^\"]*receipttableTd[^\"]*receipttableTd2[^\"]*\"[^>]*>\s*([A-Z0-9]+)\s*</td>"
    match = re.search(pattern, html, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_date_regex(html: str) -> str:
    match = re.search(r"(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})", html)
    return match.group(1).strip() if match else ""


def _extract_with_regex(html: str, label_pattern: str, value_pattern: str = r"([^<]+)") -> str:
    escaped = re.escape(label_pattern)
    pattern = rf"{escaped}.*?</td>\s*<td[^>]*>\s*{value_pattern}"
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"<[^>]*>", "", match.group(1)).strip()


def _get_next_cell_text(soup: BeautifulSoup, label: str) -> str:
    label_cell = None
    for td in soup.find_all("td"):
        if label in td.get_text(strip=True):
            label_cell = td
            break

    if not label_cell:
        return ""

    sibling = label_cell.find_next_sibling("td")
    return sibling.get_text(strip=True) if sibling else ""
