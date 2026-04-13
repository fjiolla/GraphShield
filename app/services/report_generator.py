from app.services.analysis import  parse_llm_output , client

async def generate_narrative_report(token_attributions: list, filename: str):
    top_tokens = sorted(token_attributions, key=lambda x: abs(x['weight_contribution']), reverse=True)[:10]
    
    
    prompt = f"""
    You are a Professional AI Ethics Auditor. I have performed a White-Box Audit on a hiring model.
    The model was tested using the file: {filename}.
    
    Here are the Top 10 Mathematical Weight Contributions found inside the model's layers:
    {top_tokens}
    
    Your Task:
    1. Summarize WHY these specific tokens are causing the model to flag bias.
    2. Explain what a 'Negative' or 'Positive' weight means in this context.
    3. Provide a 'Human-Readable Verdict' (e.g., 'The model is heavily biased toward educational pedigree').
    4. Provide one 'Remediation Advice' for the developer.

    Keep the tone professional, objective, and easy for a non-technical manager to understand.
    """
    
    
    response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  
            messages=[
                {"role": "system", "content": "You are a Professional AI Ethics Auditor. Output strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
    )

    output = response.choices[0].message.content
    parsed_output = parse_llm_output(output)
    return parsed_output 