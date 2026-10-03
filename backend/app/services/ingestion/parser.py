import csv
import hashlib
import io
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.services.ingestion.ocr import OCRProvider, DisabledOCRProvider
from app.services.ingestion.schema_mapper import SchemaMapper

logger = logging.getLogger(__name__)


class FileParser:
    """
    Multi-format file parser handling CSV, XLSX (via openpyxl), and PDF (via pdfplumber + OCR).
    """

    def __init__(
        self,
        schema_mapper: Optional[SchemaMapper] = None,
        ocr_provider: Optional[OCRProvider] = None,
    ):
        self.schema_mapper = schema_mapper or SchemaMapper()
        self.ocr_provider = ocr_provider or DisabledOCRProvider()

    def parse(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "",
    ) -> Tuple[List[Dict[str, Any]], str, int]:
        """
        Parses file bytes into standardized mapped records.
        Returns: (records, sha256_hash, row_count)
        """
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        ext = Path(filename).suffix.lower()

        if ext in [".csv", ".txt"] or "csv" in content_type:
            raw_records = self._parse_csv(file_bytes)
        elif ext in [".xlsx", ".xls"] or "spreadsheet" in content_type or "excel" in content_type:
            raw_records = self._parse_xlsx(file_bytes)
        elif ext in [".pdf"] or "pdf" in content_type:
            raw_records = self._parse_pdf(file_bytes)
        else:
            # Fallback: attempt CSV first, then openpyxl
            try:
                raw_records = self._parse_csv(file_bytes)
            except Exception:
                raw_records = self._parse_xlsx(file_bytes)

        mapped_records = self.schema_mapper.map_records(raw_records)
        return mapped_records, file_hash, len(mapped_records)

    def _parse_csv(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Parses CSV with encoding detection and delimiter sniffing."""
        text = None
        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            text = file_bytes.decode("utf-8", errors="replace")

        # Determine delimiter
        sample = text[:2048]
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            if ";" in sample and sample.count(";") > sample.count(","):
                delimiter = ";"
            elif "\t" in sample and sample.count("\t") > sample.count(","):
                delimiter = "\t"

        f = io.StringIO(text)
        reader = csv.DictReader(f, delimiter=delimiter)
        records: List[Dict[str, Any]] = []
        for row in reader:
            if any(str(v).strip() for v in row.values() if v is not None):
                records.append({str(k).strip(): v for k, v in row.items() if k is not None})
        return records

    def _parse_xlsx(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Parses Excel XLSX files using openpyxl."""
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet = wb.active
        if sheet is None:
            return []

        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return []

        headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(header_row)]
        records: List[Dict[str, Any]] = []

        for row in rows_iter:
            if not any(row):
                continue
            row_dict = {}
            for h, val in zip(headers, row):
                row_dict[h] = val
            records.append(row_dict)

        return records

    def _parse_pdf(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Parses PDF using pdfplumber with table extraction and OCR fallback."""
        import pdfplumber

        records: List[Dict[str, Any]] = []
        extracted_text_chunks = []

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    headers = [str(h).strip() if h else f"col_{idx}" for idx, h in enumerate(table[0])]
                    for row in table[1:]:
                        if not any(row):
                            continue
                        row_dict = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                        records.append(row_dict)

                page_text = page.extract_text()
                if page_text:
                    extracted_text_chunks.append(page_text)

        full_text = "\n".join(extracted_text_chunks).strip()

        # If table extraction yielded no records or text is sparse, try OCR if available
        if not records and len(full_text) < 50:
            ocr_text = self.ocr_provider.extract_text(file_bytes)
            if ocr_text:
                full_text = ocr_text

        # If we have extracted text and still no tabular records, parse regex fields
        if not records and full_text:
            parsed_record = self._extract_invoice_fields_from_text(full_text)
            if parsed_record:
                records.append(parsed_record)

        return records

    def _extract_invoice_fields_from_text(self, text: str) -> Dict[str, Any]:
        """Regex-based fallback extraction of key invoice fields from unstructured text."""
        record: Dict[str, Any] = {}

        # 1. Invoice Number
        inv_match = re.search(r"(?:invoice|inv|bill)\s*(?:no|num|number|#)?[:.\s]+([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
        if inv_match:
            record["invoice_number"] = inv_match.group(1).strip()

        # 2. Date
        date_match = re.search(r"(?:date|dated)[:.\s]+([0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4})", text, re.IGNORECASE)
        if date_match:
            record["invoice_date"] = date_match.group(1).strip()

        # 3. Total / Amount
        total_match = re.search(r"(?:total|grand\s+total|amount\s+due)[:.\s]+(?:[$₹€]|USD|INR)?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
        if total_match:
            record["total_amount"] = total_match.group(1).replace(",", "").strip()

        # 4. Tax
        tax_match = re.search(r"(?:tax|gst|vat)[:.\s]+(?:[$₹€]|USD|INR)?\s*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
        if tax_match:
            record["tax_amount"] = tax_match.group(1).replace(",", "").strip()

        # 5. Vendor
        vendor_match = re.search(r"(?:from|vendor|supplier|company)[:.\s]+([A-Za-z0-9\s.,&'-]{3,50})", text, re.IGNORECASE)
        if vendor_match:
            record["vendor_name"] = vendor_match.group(1).strip().split("\n")[0]

        return record

