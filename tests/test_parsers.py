from veri_py.parsers.pdf import parse_cbe_receipt_text
from veri_py.parsers.telebirr import parse_telebirr_html


def test_parse_cbe_receipt_text_success() -> None:
    raw_text = (
        "Payer: JOHN DOE Account: ****1234 "
        "Receiver: JANE SHOP Account: ****9988 "
        "Reason / Type of service: Invoice Payment "
        "Transferred Amount: 1,234.00 ETB "
        "Reference No. (VAT Invoice No): FT2513001V2G "
        "Payment Date & Time: 05/18/2025, 08:21:13 PM"
    )
    result = parse_cbe_receipt_text(raw_text)

    assert result.success is True
    assert result.reference == "FT2513001V2G"
    assert result.amount == 1234.00
    assert result.payer == "John Doe"


def test_parse_telebirr_html_extracts_essential_fields() -> None:
    html = """
    <table>
      <tr><td>የከፋይ ስም/Payer Name</td><td>Abel Demo</td></tr>
      <tr><td>የከፋይ ቴሌብር ቁ./Payer telebirr no.</td><td>251911111111</td></tr>
      <tr><td>የክፍያው ሁኔታ/transaction status</td><td>Successful</td></tr>
      <tr><td>የክፍያ ቁጥር/Receipt No.</td><td>CE2513001XYT</td></tr>
      <tr><td>የክፍያ ቀን/Payment date</td><td>18-05-2025 21:11:00</td></tr>
      <tr><td>የተከፈለው መጠን/Settled Amount</td><td>100.00 Birr</td></tr>
      <tr><td>የአገልግሎት ክፍያ/Service fee</td><td>2.00 Birr</td></tr>
      <tr><td>የአገልግሎት ክፍያ ተ.እ.ታ/Service fee VAT</td><td>0.30 Birr</td></tr>
      <tr><td>ጠቅላላ የተከፈለ/Total Paid Amount</td><td>102.30 Birr</td></tr>
    </table>
    """

    result = parse_telebirr_html(html)
    assert result.payerName == "Abel Demo"
    assert result.receiptNo == "CE2513001XYT"
    assert result.transactionStatus == "Successful"
