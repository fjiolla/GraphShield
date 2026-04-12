from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.localextraction import extract_text_from_file
from app.services.analysis import perform_dynamic_bias_profiling
from app.services.vector_audit import verify_contextual_bias
from app.services.remediation import generate_remediation_plan

router = APIRouter()

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    valid_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, TXT, or DOCX.")

    try:
        content = await file.read()
        extracted_text = await extract_text_from_file(
            content,
            file.content_type
        )
        print("File validation doen!!")
        bias_results = await perform_dynamic_bias_profiling(extracted_text)

        if "groups" in bias_results["dynamic_profile"]:
            quantitative_audit = await verify_contextual_bias(
                extracted_text, 
                bias_results["dynamic_profile"]["groups"]
            )
        else:
            quantitative_audit = []
        print("first setp is doen!!!")    

        recommendation = await generate_remediation_plan(bias_results["dynamic_profile"])
        return {
            "filename": file.filename,
            "audit_metadata": {
                "engine_v": "2.0-contextual",
                "status": "Verified"
            },
            "findings": {
                "qualitative_analysis": bias_results,
                "quantitative_verification": quantitative_audit
            },
            "recommendation": recommendation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    