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

            # Save to bytes for PaddleOCR
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)

            # Run OCR
            result = self.ocr.ocr(img_byte_arr.getvalue(), cls=True)

            if not result or not result[0]:
                return ""

            # Extract text from result
            extracted_lines = []
            for line in result[0]:
                if line and len(line) > 1:
                    text = line[1][0]  # Get the text content
                    extracted_lines.append(text)

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
            result = self.ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return ""

            # Extract text from result
            extracted_lines = []
            for line in result[0]:
                if line and len(line) > 1:
                    text = line[1][0]
                    extracted_lines.append(text)

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
