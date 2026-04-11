from fastapi import APIRouter, UploadFile, File, HTTPException
# from app.services.extraction import extract_text_from_file
from app.services.localextraction import extract_text_from_file

router = APIRouter()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    valid_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, TXT, or DOCX.")

    try:
        content = await file.read()
        # extracted_text = await extract_text_from_file(content, file.content_type) gemini call to extract text from file
        extracted_text = await extract_text_from_file(
            content,
            file.content_type
        )
        return {
            "filename": file.filename,
            "status": "Extraction Successful",
            "content_length": len(extracted_text),
            "extracted_content_preview": extracted_text[:500] + "..."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))