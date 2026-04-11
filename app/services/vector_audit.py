from sentence_transformers import SentenceTransformer, util
import torch
import re

model = SentenceTransformer('all-MiniLM-L6-v2')

async def verify_contextual_bias(text: str, discovered_groups: list):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
    
    audit_results = []

    for group in discovered_groups:
        group_name = group['group_name']
        descriptors = group['descriptors']
        keyword = group.get('primary_keyword', group['group_name']).lower()
        search_terms = [keyword] + [d.lower() for d in group.get('descriptors', [])]
        
        group_indices = [
            i for i, s in enumerate(sentences) 
            if any(term in s.lower() for term in search_terms)
        ]   
            
        if not group_indices:
            continue
            
        group_context_embeddings = sentence_embeddings[group_indices]
        group_profile_vector = torch.mean(group_context_embeddings, dim=0)
        
        bias_anchor_vectors = model.encode(descriptors, convert_to_tensor=True)

        proximity_scores = util.cos_sim(group_profile_vector, bias_anchor_vectors)
        mean_proximity = torch.mean(proximity_scores).item()

        audit_results.append({
            "group": group_name,
            "contextual_proximity_score": round(mean_proximity, 4),
            "evidence_count": len(group_indices),
            "mathematical_weight": "Strong" if mean_proximity > 0.5 else "Moderate"
        })

    return audit_results