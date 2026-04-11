import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from docx import Document
from io import BytesIO


def extract_text_from_pdf_hybrid(file_content: bytes) -> str:
    doc = fitz.open(stream=file_content, filetype="pdf")
    final_text = ""

    for page in doc:
        text = page.get_text().strip()
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        ocr_text = pytesseract.image_to_string(
            img, config="--oem 3 --psm 6"
        ).strip()

        if len(text) > 50:
            combined = text
            if len(ocr_text) > 10:
                combined += "\n" + ocr_text
        else:
            combined = ocr_text
        final_text += combined + "\n"

    return final_text


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