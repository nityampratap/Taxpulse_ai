import re
from typing import Any, Dict, List, Optional


class SchemaMapper:
    """
    Normalizes input table headers into standardized enterprise canonical schema fields.
    """

    COLUMN_ALIASES: Dict[str, List[str]] = {
        "invoice_number": [
            "invoice_number",
            "invoice_no",
            "invoiceno",
            "inv_no",
            "inv_num",
            "invno",
            "bill_no",
            "bill_number",
            "reference",
            "reference_id",
            "ref_no",
            "doc_number",
            "document_no",
        ],
        "vendor_name": [
            "vendor_name",
            "vendor",
            "supplier",
            "supplier_name",
            "merchant",
            "counterparty",
            "counterparty_name",
            "party_name",
            "payee",
        ],
        "invoice_date": [
            "invoice_date",
            "inv_date",
            "date",
            "bill_date",
            "document_date",
            "trans_date",
            "transaction_date",
            "posting_date",
        ],
        "due_date": [
            "due_date",
            "payment_due_date",
            "due",
            "expiry_date",
        ],
        "subtotal": [
            "subtotal",
            "taxable_amount",
            "taxable_value",
            "base_amount",
            "net_amount",
            "line_subtotal",
        ],
        "tax_amount": [
            "tax_amount",
            "tax",
            "gst",
            "gst_amount",
            "vat",
            "vat_amount",
            "sales_tax",
        ],
        "total_amount": [
            "total_amount",
            "total",
            "amount",
            "gross_amount",
            "invoice_total",
            "final_amount",
            "amount_paid",
        ],
        "currency": [
            "currency",
            "curr",
            "iso_currency",
        ],
        "tax_identifier": [
            "tax_identifier",
            "gstin",
            "vat_no",
            "tin",
            "pan",
            "ein",
        ],
        "ground_truth_label": [
            "ground_truth_label",
            "label",
            "gt_label",
            "test_label",
        ],
    }

    def __init__(self, custom_aliases: Optional[Dict[str, List[str]]] = None):
        self.aliases = dict(self.COLUMN_ALIASES)
        if custom_aliases:
            for k, v in custom_aliases.items():
                self.aliases.setdefault(k, []).extend(v)

        # Precompute reverse lookup map with normalized key names
        self._reverse_map: Dict[str, str] = {}
        for canonical, aliases in self.aliases.items():
            for alias in aliases:
                norm_alias = self._normalize_header(alias)
                self._reverse_map[norm_alias] = canonical

    @staticmethod
    def _normalize_header(header: str) -> str:
        """Strip spaces, punctuation, convert to lowercase."""
        if not header:
            return ""
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(header).strip().lower())
        return cleaned

    def map_field_name(self, raw_header: str) -> Optional[str]:
        """Resolves a raw column header to its canonical field name if known."""
        norm = self._normalize_header(raw_header)
        return self._reverse_map.get(norm)

    def map_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a single dictionary row from arbitrary keys to canonical fields."""
        mapped: Dict[str, Any] = {}
        for raw_k, raw_v in raw_record.items():
            canonical_k = self.map_field_name(raw_k)
            if canonical_k:
                mapped[canonical_k] = raw_v
            else:
                # Retain unmapped fields in raw_fields
                if "extra" not in mapped:
                    mapped["extra"] = {}
                mapped["extra"][raw_k] = raw_v
        return mapped

    def map_records(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maps an entire list of row dictionaries."""
        return [self.map_record(rec) for rec in raw_records]

