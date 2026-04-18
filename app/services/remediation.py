from app.services.analysis import client
from app.services.analysis import parse_llm_output


async def generate_remediation_plan(bias_findings: dict):
    try:    
        prompt = f"""
        You are an AI Remediation Expert. 
        Based on these bias findings: {bias_findings}
        
        Provide specific remediation actions and counter-factual examples for the groups identified.
        
        You MUST return the result as a STRICT JSON array of objects, where each object has EXACTLY these fields:
        - "priority": one of ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        - "action": A short title for the action
        - "description": A detailed description including any counter-factual examples (how the text SHOULD look)
        - "steps": An array of strings containing step-by-step instructions
        
        Example format:
        [
          {{
            "priority": "HIGH",
            "action": "Address Age Bias in Job Description",
            "description": "The description uses terms like 'digital native' which implicitly excludes older candidates. Counter-factual: 'Seeking candidates proficient in modern digital tools'.",
            "steps": ["Remove age-coded language", "Add inclusive EEO statement"]
          }}
        ]
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
        return {    
            "remediation_plan": parsed_output,
        }

    except Exception as e:
        return {
            "error": "Bias profiling failed",
            "details": str(e)
        }