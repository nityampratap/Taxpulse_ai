import io
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class OCRProvider(ABC):
    """Abstract interface for Optical Character Recognition providers."""

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        """Extract plain text from image or document bytes."""
        pass


class DisabledOCRProvider(OCRProvider):
    """Default no-op OCR provider when OCR is disabled or unavailable."""

    def extract_text(self, file_bytes: bytes) -> str:
        logger.debug("OCR extraction requested but DisabledOCRProvider is active.")
        return ""


class TesseractOCRProvider(OCRProvider):
    """Optional OCR implementation powered by pytesseract."""

    def __init__(self, tesseract_cmd: str | None = None):
        self.tesseract_cmd = tesseract_cmd

    def extract_text(self, file_bytes: bytes) -> str:
        try:
            from PIL import Image
            import pytesseract
        except ImportError as e:
            logger.warning("pytesseract or Pillow not installed. OCR fallback returning empty string: %s", e)
            return ""

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        try:
            image = Image.open(io.BytesIO(file_bytes))
            return pytesseract.image_to_string(image)
        except Exception as e:
            logger.error("Tesseract OCR extraction failed: %s", e)
            return ""

