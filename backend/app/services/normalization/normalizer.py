import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Union


CORPORATE_SUFFIXES = [
    r"\bpvt\b",
    r"\bprivate\b",
    r"\bltd\b",
    r"\blimited\b",
    r"\binc\b",
    r"\bincorporated\b",
    r"\bcorp\b",
    r"\bcorporation\b",
    r"\bllc\b",
    r"\bllp\b",
    r"\bgmbh\b",
    r"\bco\b",
    r"\bcompany\b",
    r"\bservices\b",
    r"\bsolutions\b",
    r"\benterprises\b",
    r"\bglobal\b",
    r"\bsystems\b",
    r"\bindustrial\b",
]

_SUFFIX_REGEX = re.compile(
    r"(" + "|".join(CORPORATE_SUFFIXES) + r")[.\s,]*$",
    re.IGNORECASE,
)


def normalize_invoice_number(raw_num: Optional[str]) -> str:
    """
    Standardize invoice reference numbers by removing dashes, spaces, and punctuation,
    converting to uppercase. E.g., 'INV-2048' -> 'INV2048', 'inv 2048' -> 'INV2048'.
    """
    if not raw_num:
        return ""
    # Strip common leading noise prefixes like REF/ or INV:
    cleaned = re.sub(r"^(?:ref/|reference/|doc/|#)+", "", str(raw_num).strip(), flags=re.IGNORECASE)
    # Remove non-alphanumeric characters
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", cleaned)
    return cleaned.upper()


def normalize_vendor_name(raw_name: Optional[str]) -> str:
    """
    Standardizes vendor legal names: lowercase, strip punctuation, strip corporate suffixes,
    and collapse extra whitespace. E.g., 'ABC Supplies, Inc.' -> 'abc supplies'.
    """
    if not raw_name:
        return ""
    name = str(raw_name).strip().lower()
    # Remove punctuation
    name = re.sub(r"[^\w\s]", " ", name)
    # Remove corporate suffixes iteratively
    prev = None
    while prev != name:
        prev = name
        name = _SUFFIX_REGEX.sub("", name).strip()
    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name).strip()
    return name


def normalize_date(raw_date: Any) -> Optional[date]:
    """
    Parses various date and timestamp representations into a standardized datetime.date object.
    Supports ISO (YYYY-MM-DD), DD/MM/YYYY, MM/DD/YYYY, and datetime instances.
    """
    if raw_date is None or raw_date == "":
        return None
    if isinstance(raw_date, date) and not isinstance(raw_date, datetime):
        return raw_date
    if isinstance(raw_date, datetime):
        return raw_date.date()

    s = str(raw_date).strip()
    # Remove time component if present
    s = s.split("T")[0].split(" ")[0]

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue

    return None


def normalize_amount(raw_amount: Any) -> Decimal:
    """
    Converts currency strings or numeric representations into Decimal(18, 4).
    Strips symbols ($, ₹, €, £, INR, USD) and comma separators.
    """
    if raw_amount is None:
        return Decimal("0.0000")
    if isinstance(raw_amount, Decimal):
        return raw_amount.quantize(Decimal("0.0001"))
    if isinstance(raw_amount, (int, float)):
        return Decimal(str(raw_amount)).quantize(Decimal("0.0001"))

    s = str(raw_amount).strip()
    # Strip currency symbols and letters
    cleaned = re.sub(r"[^\d.-]", "", s)
    if not cleaned or cleaned == "-":
        return Decimal("0.0000")

    try:
        return Decimal(cleaned).quantize(Decimal("0.0001"))
    except InvalidOperation:
        return Decimal("0.0000")


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Applies all normalization rules to a mapped invoice or transaction record."""
    normalized = dict(record)

    if "invoice_number" in normalized:
        raw_inv = str(normalized["invoice_number"])
        normalized["invoice_number"] = raw_inv
        normalized["normalized_number"] = normalize_invoice_number(raw_inv)

    if "vendor_name" in normalized:
        raw_vendor = str(normalized["vendor_name"])
        normalized["vendor_name"] = raw_vendor
        normalized["normalized_vendor"] = normalize_vendor_name(raw_vendor)

    if "invoice_date" in normalized:
        normalized["invoice_date"] = normalize_date(normalized["invoice_date"])

    if "due_date" in normalized:
        normalized["due_date"] = normalize_date(normalized["due_date"])

    for amt_field in ["subtotal", "tax_amount", "total_amount", "amount", "amount_paid"]:
        if amt_field in normalized and normalized[amt_field] is not None:
            normalized[amt_field] = normalize_amount(normalized[amt_field])

    return normalized

