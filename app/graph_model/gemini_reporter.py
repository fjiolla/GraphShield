"""
LLM Reporter module using Groq API (as a substitute for Gemini).
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

def get_domain_context(domain: str) -> str:
    """Return domain-specific context string for prompt."""
    contexts = {
        'social_network': 'social media recommendation graph',
        'fraud_detection': 'financial transaction and fraud mapping graph',
        'knowledge_graph': 'semantic knowledge graph',
        'hiring': 'hiring and candidate network graph',
        'lending': 'lending and credit decision graph',
        'healthcare': 'healthcare patient network graph',
        'recommendation': 'recommendation system graph',
        'generic': 'general network graph'
    }
    return contexts.get(domain, contexts['generic'])

def _build_condensed_scorecard(scorecard: dict) -> str:
    """
    Build a short summary of the scorecard to keep prompt small.
    Groq's smaller models struggle with very large prompts.
    """
    lines = []
    lines.append(f"Overall Score: {scorecard.get('overall_score')}/100 ({scorecard.get('overall_status')})")
    lines.append(f"Protected Attribute: {scorecard.get('protected_attribute')}")
    lines.append(f"Groups: {scorecard.get('groups_found')}")
    lines.append(f"Nodes: {scorecard.get('graph_metadata', {}).get('node_count')}, Edges: {scorecard.get('graph_metadata', {}).get('edge_count')}")
    
    # Universal metrics
    um = scorecard.get("universal_metrics", {})
    for k in ["demographic_parity", "equalized_odds", "disparate_impact", "predictive_parity"]:
        m = um.get(k, {})
        if m.get("raw_value") is not None:
            lines.append(f"{k}: {m['raw_value']:.4f} (score {m.get('score')}, {m.get('status')})")

    # Per group
    pg = um.get("per_group_metrics", {})
    for g, data in pg.items():
        lines.append(f"Group '{g}': count={data.get('count')}, positive_rate={data.get('positive_rate')}, accuracy={data.get('accuracy')}")
    
    # Structural metrics
    sm = scorecard.get("structural_metrics", {})
    for k, m in sm.items():
        if isinstance(m, dict) and m.get("raw_value") is not None:
            lines.append(f"{k}: {m['raw_value']:.4f} (score {m.get('score')}, {m.get('status')})")

    # Key findings
    kf = scorecard.get("key_findings", [])
    for f in kf:
        lines.append(f"Finding: {f}")

    return "\n".join(lines)

def build_gemini_prompt(scorecard: dict, domain: str = None) -> str:
    """Build a concise, structured prompt for LLM generation."""
    domain_ctx = get_domain_context(domain)
    condensed = _build_condensed_scorecard(scorecard)
    
    prompt = f"""You are an AI fairness auditor. Analyze this bias audit of a {domain_ctx}.

DATA:
{condensed}

Respond with ONLY a valid JSON object using these exact keys:
{{
  "summary": "2-3 sentence overview of the audit results",
  "bias_found": "what specific bias exists and which groups are affected",
  "likely_causes": "structural vs model vs data causes",
  "remediation": "3-4 specific actionable fixes",
  "severity_assessment": "LOW or MEDIUM or HIGH or CRITICAL",
  "regulatory_note": "relevant regulations for {domain_ctx}"
}}

Keep each value as a single short paragraph. No nested objects. No line breaks inside values."""
    return prompt

def call_gemini_api(prompt: str) -> str:
    """
    Call Groq API (implemented per latest user instruction instead of Gemini API).
    The Gemini implementation is preserved in comments for reference.
    """
    # === GEMINI IMPLEMENTATION (COMMENTED OUT) ===
    # import google.generativeai as genai
    # try:
    #     genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    #     model = genai.GenerativeModel("gemini-pro")
    #     response = model.generate_content(prompt)
    #     return response.text
    # except Exception as e:
    #     logger.error(f"Gemini API Error: {e}")
    #     raise
    # =============================================
    
    # === GROQ IMPLEMENTATION ===
    try:
        from groq import Groq
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found. Returning fallback.")
            return '{"summary": "[HARDCODED] Fallback summary due to missing API key."}'
            
        client = Groq(api_key=groq_api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON-only responder. Output valid JSON with no markdown, no comments, no trailing commas."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        # Try to extract partial response from the error if available
        error_str = str(e)
        if "failed_generation" in error_str:
            return _extract_from_failed_generation(error_str)
        return '{"summary": "[HARDCODED] Fallback summary due to LLM API failure."}'

def _extract_from_failed_generation(error_str: str) -> str:
    """
    When Groq returns a json_validate_failed error, the error message
    contains a 'failed_generation' key with partial JSON. Try to salvage it.
    """
    try:
        # Find the failed_generation content
        start = error_str.find("'failed_generation': '")
        if start == -1:
            start = error_str.find('"failed_generation": "')
        if start == -1:
            return '{"summary": "[HARDCODED] Could not extract from failed generation."}'
        
        # Extract and try to fix common JSON issues
        raw = error_str[start:]
        # Find the JSON-like content
        brace_start = raw.find('{')
        if brace_start == -1:
            return '{"summary": "[HARDCODED] No JSON found in failed generation."}'
        
        raw = raw[brace_start:]
        # Try to find matching closing brace
        depth = 0
        end = 0
        for i, ch in enumerate(raw):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        if end > 0:
            candidate = raw[:end]
            # Clean up escaped newlines
            candidate = candidate.replace('\\n', ' ').replace('\n', ' ')
            parsed = json.loads(candidate)
            return json.dumps(parsed)
    except Exception:
        pass
    
    return '{"summary": "[HARDCODED] Failed to recover from malformed LLM output."}'

def parse_gemini_response(response_text: str) -> dict:
    """Parse JSON response from LLM."""
    try:
        return json.loads(response_text)
    except Exception:
        logger.warning("Failed to parse LLM response to JSON format.")
        return {"summary": response_text}

def generate_bias_report(scorecard: dict, domain: str = None) -> dict:
    """Call LLM API with scorecard data."""
    prompt = build_gemini_prompt(scorecard, domain)
    raw_response = call_gemini_api(prompt)
    return parse_gemini_response(raw_response)

if __name__ == "__main__":
    # Smoke test
    print(generate_bias_report({"overall_score": 85, "overall_status": "PASS"}, "generic"))
