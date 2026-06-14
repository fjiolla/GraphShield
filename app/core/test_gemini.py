import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Tell me a 1 sentence joke.",
    config=types.GenerateContentConfig(
        system_instruction="You are a funny bot.",
        temperature=0.2,
    )
)

print("Gemini response:")
print(response.text)
