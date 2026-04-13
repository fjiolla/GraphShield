from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.localextraction import extract_text_from_file
from app.services.report_generator import generate_narrative_report
from app.services.white_box_audit import WhiteBoxAuditor

router = APIRouter()
auditor = WhiteBoxAuditor()

@router.post("/audit-user-model")
async def audit_user_model(
    model_file: UploadFile = File(...), 
    data_file: UploadFile = File(...)
):
    
    if not model_file.filename.endswith(('.pt', '.pth')):
        raise HTTPException(status_code=400, detail="Please upload a PyTorch model file (.pt or .pth)")

    try:
        data_content = await data_file.read()
        test_text = await extract_text_from_file(data_content, data_file.content_type)

        model_bytes = await model_file.read()
        user_model = auditor.load_user_model(model_bytes)

        results = await auditor.run_audit(user_model, test_text[:1000])

        human_report = await generate_narrative_report(
            results["token_attributions"], 
            data_file.filename
        )
        return {
            "model_filename": model_file.filename,
            "data_filename": data_file.filename,
            "audit_report": {
                "internal_weights_analysis": results["token_attributions"],
                "math_integrity_delta": results["convergence_delta"]
            },
            "human_readable_report": human_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dynamic Audit Failed: {str(e)}")