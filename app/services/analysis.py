from groq import Groq
from app.core.config import settings
import re
import json

nlp = None
_NLP_AVAILABLE = False

def get_nlp():
    global nlp, _NLP_AVAILABLE
    if nlp is None:
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            _NLP_AVAILABLE = True
        except Exception:
            # Model not installed — NER will be skipped, LLM still runs on raw text
            _NLP_AVAILABLE = False
    return nlp if _NLP_AVAILABLE else None

def clean_llm_output(output: str):
    output = re.sub(r"```json", "", output)
    output = re.sub(r"```", "", output)    
    return output.strip()

def parse_llm_output(output: str):
    try:
        cleaned = clean_llm_output(output)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {
            "error": "Invalid JSON from LLM",
            "raw_output": output,
            "details": str(e)
        }

client = Groq(api_key=settings.GROQ_API_KEY)

async def perform_dynamic_bias_profiling(text: str):
    try:
        nlp_model = get_nlp()
        if nlp_model is not None:
            doc = nlp_model(text[:10000])
            entities = [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
            ]
            total_mentions = len(entities)
        else:
            # spaCy model unavailable — skip NER, LLM will analyse raw text
            entities = []
            total_mentions = 0

        prompt = f"""
            You are an expert AI system specialized in bias detection, social analysis, and linguistic interpretation.

            Your goal is to perform deep analysis of the provided TEXT using the given ENTITIES.

            ----------------------------------------
            ANALYSIS INSTRUCTIONS
            ----------------------------------------

            You must:

            1. Identify ALL demographic or social groups mentioned in the text.
            - These may include explicit groups (e.g., "women", "engineers")
            - Also detect implicit groups (e.g., "young people", "immigrants")

            2. For EACH identified group, provide a "primary_keyword":
            - This MUST be a 1-2 word identifier that appears EXACTLY in the TEXT (e.g., "Dalit", "Women", "Metro").
            - This is critical for mathematical string-matching verification.

            3. For EACH identified group:
            - Extract associated:
                • adjectives (e.g., "lazy", "intelligent")
                • roles (e.g., "leaders", "workers")
                • actions (e.g., "dominate", "struggle")
                • contextual phrases that describe the group

            4. Detect the TYPE OF BIAS:
            - Explicit bias (clearly stated)
            - Implicit bias (subtle, implied, stereotypical)

            5. Assign a bias category:
            - Age, Gender, Profession, Ethnicity, Religion, Socioeconomic, Education, or Other.

            6. Determine sentiment toward the group:
            - Positive, Negative, Neutral, or Mixed.

            7. Assign a bias intensity score:
            - Float value between 0 and 1 (0 = no bias, 1 = extreme bias).

            8. Provide a short justification based ONLY on the given text.

            ----------------------------------------
            OUTPUT FORMAT (STRICT JSON)
            ----------------------------------------

            Return ONLY valid JSON in the following structure:

            {{
            "groups": [
                {{
                "group_name": "string",
                "primary_keyword": "string",
                "bias_category": "string",
                "bias_type": "explicit | implicit",
                "sentiment": "positive | negative | neutral | mixed",
                "bias_intensity": float,
                "descriptors": ["string", "string"],
                "evidence": ["exact phrase from text"],
                "justification": "short explanation based on text"
                }}
            ],
            "summary": {{
                "overall_bias": "low | medium | high",
                "dominant_bias_category": "string",
                "notes": "brief summary of bias patterns"
            }}
            }}

            ----------------------------------------
            STRICT RULES
            ----------------------------------------

            - Output MUST be valid JSON.
            - The "primary_keyword" MUST be present in the TEXT for string matching.
            - Do NOT include explanations outside JSON.
            - Do NOT add markdown code blocks (e.g., ```json).
            - Do NOT hallucinate groups not supported by text.

            ----------------------------------------
            INPUT DATA
            ----------------------------------------

            ENTITIES:
            {entities}

            TEXT:
            {text[:10000]}
        """

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  
            messages=[
                {"role": "system", "content": "You are a bias detection AI. Output strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        output = response.choices[0].message.content
        parsed_output = parse_llm_output(output)
        # doc may be undefined if NLP was skipped — use word count as denominator
        doc_len = len(doc) if 'doc' in dir() and doc is not None else max(len(text.split()), 1)
        return {    
            "dynamic_profile": parsed_output,
            "metadata": {
                "document_complexity": "High" if total_mentions > 50 else "Standard",
                "entity_density": total_mentions / doc_len,
                "ner_model": "spacy_en_core_web_sm" if total_mentions > 0 else "none",
                "llm_model": "llama3_groq",
                "total_entities": total_mentions
            }
        }

    except Exception as e:
        return {
            "error": "Bias profiling failed",
            "details": str(e)
        }