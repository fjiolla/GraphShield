import fitz  # PyMuPDF
from docx import Document
from io import BytesIO
import shutil

# Try to import OCR dependencies — they are optional
_OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    # Robust check: verify the tesseract binary actually exists on PATH
    if shutil.which("tesseract") is not None:
        pytesseract.get_tesseract_version()
        _OCR_AVAILABLE = True
except Exception:
    pass  # Tesseract not installed; fall back to text-only extraction


def extract_text_from_pdf_hybrid(file_content: bytes) -> str:
    doc = fitz.open(stream=file_content, filetype="pdf")
    final_text = ""

    for page in doc:
        text = page.get_text().strip()

        if _OCR_AVAILABLE and len(text) <= 50:
            # Only run OCR when the page is image-based (little/no extractable text)
            try:
                from PIL import Image as _Image
                pix = page.get_pixmap()
                img = _Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img, config="--oem 3 --psm 6").strip()
                combined = ocr_text if ocr_text else text
            except Exception:
                # OCR failed at runtime (binary issue, format error, etc.) — use native text
                combined = text
        else:
            combined = text

        final_text += combined + "\n"

    return final_text.strip()


async def extract_text_from_file(file_content: bytes, file_type: str) -> str:

    if file_type == "application/pdf":
        return extract_text_from_pdf_hybrid(file_content)

    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])

    elif file_type == "text/plain":
        return file_content.decode("utf-8")

    else:
        raise ValueError("Unsupported file type")