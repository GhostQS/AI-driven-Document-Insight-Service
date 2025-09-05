import io
import os
from typing import Union

import fitz  # PyMuPDF
import easyocr
from PIL import Image
import numpy as np

# Lazy global reader for EasyOCR to avoid re-init cost
_EASY_READER = None

def _get_easy_reader():
    global _EASY_READER
    if _EASY_READER is None:
        # English by default, can extend via env EASYOCR_LANGS="en,fr,de"
        langs = os.getenv("EASYOCR_LANGS", "en").split(",")
        _EASY_READER = easyocr.Reader(langs, gpu=os.getenv("EASYOCR_GPU", "false").lower()=="true")
    return _EASY_READER


def _is_pdf(filename: str) -> bool:
    return filename.lower().endswith(".pdf")


def _is_image(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"])


def extract_text_from_pdf(file_like: io.BytesIO) -> str:
    file_like.seek(0)
    text_parts = []
    with fitz.open(stream=file_like.read(), filetype="pdf") as doc:
        for page in doc:
            # Try direct text extraction
            page_text = page.get_text("text") or ""
            if page_text.strip():
                text_parts.append(page_text)
            else:
                # Fallback to OCR by rasterizing page
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text_parts.append(extract_text_from_image(img))
    return "\n\n".join(text_parts)


def extract_text_from_image(image_or_file: Union[Image.Image, io.BytesIO]) -> str:
    reader = _get_easy_reader()
    if isinstance(image_or_file, Image.Image):
        img = np.array(image_or_file)
    else:
        image_or_file.seek(0)
        img = np.array(Image.open(image_or_file).convert("RGB"))
    results = reader.readtext(img, detail=0, paragraph=True)
    return "\n".join(results)


def extract_text_from_file(file_like: io.BytesIO, filename: str) -> str:
    if _is_pdf(filename):
        return extract_text_from_pdf(file_like)
    if _is_image(filename):
        return extract_text_from_image(file_like)
    raise ValueError(f"Unsupported file type for {filename}. Allowed: PDF or images.")
