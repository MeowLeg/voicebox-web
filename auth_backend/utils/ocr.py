import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(lang='ch')
        logger.info("PaddleOCR initialized")
    return _ocr


def extract_text(image_path: str | Path) -> str:
    """Extract text from a single image using PaddleOCR.

    Returns the extracted text as a single string, with lines joined by newlines.
    """
    ocr = _get_ocr()
    results = ocr.ocr(str(image_path))

    if not results or not results[0]:
        return ''

    lines = []
    for line_info in results[0]:
        text = line_info[1][0]
        if text and text.strip():
            lines.append(text.strip())

    return '\n'.join(lines)


def extract_text_from_images(image_paths: list[str | Path]) -> list[dict]:
    """Extract text from multiple images.

    Returns a list of dicts with image name and extracted text.
    """
    results = []
    for path in image_paths:
        path = Path(path)
        try:
            text = extract_text(path)
            results.append({
                'image': path.name,
                'text': text,
            })
            logger.info(f"OCR done: {path.name} → {len(text)} chars")
        except Exception as e:
            logger.error(f"OCR failed for {path.name}: {e}")
            results.append({
                'image': path.name,
                'text': '',
                'error': str(e),
            })
    return results
