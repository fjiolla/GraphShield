from google import genai
from google.genai import types   
from app.core.config import settings

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

async def extract_text_from_file(file_content: bytes, file_type: str) -> str:
    prompt = "Extract all text from this document accurately. Do not summarize."
    print("Sending document to Gemini for text extraction...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[
            prompt,
            types.Part.from_bytes(   
                data=file_content,
                mime_type=file_type
            )
        ]
    )

    if not response.text:
        raise ValueError("Gemini failed to extract text from the document.")

    return response.text