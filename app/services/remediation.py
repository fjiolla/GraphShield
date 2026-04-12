from app.services.analysis import client
from app.services.analysis import parse_llm_output


async def generate_remediation_plan(bias_findings: dict):
    try:    
        prompt = f"""
        You are an AI Remediation Expert. 
        Based on these bias findings: {bias_findings}
        
        1. For each group, provide a specific 'Remediation Action'.
        2. Generate a 'Counter-factual Example' (how the text SHOULD look to be fair).
        3. Suggest a 'Synthetic Data Ratio' (e.g., 'Increase sample size of Group X by 25%').
        4. Provide a 'Governance Tip' for the management team.
        
        Return the result as a STRICT JSON object.
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