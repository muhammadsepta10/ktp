import logging
from paddleocr import PaddleOCR
from PIL import Image
import io
from typing import Optional
from app.config import settings

# Disable PaddleOCR verbose logging
logging.getLogger("ppocr").setLevel(logging.WARNING)


class OcrService:
    def __init__(self, lang: str = None):
        self.lang = lang or settings.OCR_LANGUAGE
        self._ocr = None

    @property
    def ocr(self) -> PaddleOCR:
        if self._ocr is None:
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
            )
        return self._ocr

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes.

        Args:
            image_bytes: Image file content as bytes

        Returns:
            Extracted text as a single string

        Raises:
            ValueError: If image is invalid or OCR fails
        """
        try:
            # Validate image
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()

            # Re-open image after verify (verify() closes the file)
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Save to temp file for PaddleOCR (bytes input not reliable)
            import tempfile
            import os as temp_os
            
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                image.save(tmp, format="PNG")
                tmp_path = tmp.name
            
            try:
                # Run OCR with file path
                result = self.ocr.ocr(tmp_path)
            finally:
                # Cleanup temp file
                temp_os.unlink(tmp_path)

            if not result:
                return ""

            # Extract text from result - handle different result structures
            extracted_lines = []
            
            # Handle list of pages (result is list of pages, each page is list of lines)
            pages = result if isinstance(result, list) else [result]
            
            for page in pages:
                if not page:
                    continue
                for line in page:
                    if not line:
                        continue
                    # Handle different line formats
                    # Format 1: [[box], (text, confidence)]
                    # Format 2: {'text': ..., 'confidence': ...}
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                            extracted_lines.append(str(text_info[0]))
                        elif isinstance(text_info, str):
                            extracted_lines.append(text_info)
                    elif isinstance(line, dict) and 'text' in line:
                        extracted_lines.append(line['text'])

            return "\n".join(extracted_lines)

        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")

    def extract_text_from_path(self, image_path: str) -> str:
        """
        Extract text from image file path.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as a single string

        Raises:
            ValueError: If image is invalid or OCR fails
        """
        try:
            result = self.ocr.ocr(image_path)

            if not result:
                return ""

            # Extract text from result - handle different result structures
            extracted_lines = []
            
            # Handle list of pages
            pages = result if isinstance(result, list) else [result]
            
            for page in pages:
                if not page:
                    continue
                for line in page:
                    if not line:
                        continue
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        text_info = line[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                            extracted_lines.append(str(text_info[0]))
                        elif isinstance(text_info, str):
                            extracted_lines.append(text_info)
                    elif isinstance(line, dict) and 'text' in line:
                        extracted_lines.append(line['text'])

            return "\n".join(extracted_lines)

        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")


# Singleton instance
_ocr_service: Optional[OcrService] = None


def get_ocr_service() -> OcrService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OcrService()
    return _ocr_service
