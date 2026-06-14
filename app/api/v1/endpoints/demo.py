"""
Demo Mode — Pre-computed audit results for instant demonstrations.
Returns realistic bias audit results without requiring file uploads or API calls.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


DEMO_DATASET_AUDIT = {
    "bias_detected": True,
    "risk_level": "High",
    "summary": "Significant gender-based bias detected in hiring decisions. Female candidates are 37% less likely to be approved compared to male candidates with equivalent qualifications.",
    "findings": [
        "Disparate Impact Ratio for Gender (Female): 0.63 — BELOW the 80% threshold",
        "Statistical Parity Difference: -0.22 indicating systematic disadvantage for female applicants",
        "Proxy correlation detected: 'department' column correlates 0.78 with gender",
        "Age group 25-35 shows amplified bias (DIR = 0.51 for female candidates)",
        "Education level does not mitigate bias — persists across all education categories"
    ],
    "recommendations": [
        "Remove or blind the 'department' column which acts as a gender proxy",
        "Apply reweighing pre-processing to balance approval rates across gender groups",
        "Implement threshold adjustment: lower decision boundary for disadvantaged group by 0.12",
        "Conduct intersectional audit across Gender × Age × Education combinations",
        "Establish ongoing monitoring with monthly DIR recalculation"
    ],
    "dataset_overview": {
        "table_name": "hiring_decisions_2024",
        "total_rows": 32561,
        "total_columns": 15,
        "sensitive_columns": ["sex", "race", "native.country"],
        "target_columns": ["income"],
        "proxy_columns": ["occupation", "relationship", "marital.status"]
    },
    "bias_metrics": {
        "disparate_impact_ratio_gender": 0.63,
        "statistical_parity_difference": -0.22,
        "equal_opportunity_difference": -0.18,
        "predictive_parity_ratio": 0.71,
        "theil_index": 0.34
    },
    "metrics_summary": {
        "sex": {
            "Male": {"count": 21790, "positive_rate": 0.31, "approval_count": 6755},
            "Female": {"count": 10771, "positive_rate": 0.11, "approval_count": 1185}
        },
        "race": {
            "White": {"count": 27816, "positive_rate": 0.26, "approval_count": 7230},
            "Black": {"count": 3124, "positive_rate": 0.12, "approval_count": 375},
            "Asian-Pac-Islander": {"count": 1039, "positive_rate": 0.27, "approval_count": 281},
            "Other": {"count": 582, "positive_rate": 0.14, "approval_count": 81}
        }
    },
    "column_explanations": {
        "sex": {
            "type": "Sensitive",
            "reason": "Direct demographic attribute — legally protected characteristic under Title VII and EU AI Act",
            "bias_risk": "HIGH — approval rates differ by 20 percentage points between groups"
        },
        "race": {
            "type": "Sensitive",
            "reason": "Protected characteristic under civil rights legislation globally",
            "bias_risk": "HIGH — Black applicants face 14% lower positive rate than White applicants"
        },
        "occupation": {
            "type": "Proxy",
            "reason": "Strongly correlated with gender (r=0.78) — acts as indirect discriminator",
            "bias_risk": "MEDIUM — removing this feature reduces gender DIR gap by 40%"
        },
        "relationship": {
            "type": "Proxy",
            "reason": "Encodes marital/family status which correlates with gender roles",
            "bias_risk": "MEDIUM — 'Husband'/'Wife' categories create gender signal"
        },
        "income": {
            "type": "Target",
            "reason": "Binary outcome variable representing the decision being audited",
            "bias_risk": "N/A — this is the outcome we're measuring fairness against"
        }
    }
}


DEMO_DOCUMENT_AUDIT = {
    "filename": "Hiring_Bias_Across_Indian_Cities.pdf",
    "audit_metadata": {
        "engine_v": "2.0-contextual",
        "status": "Verified"
    },
    "findings": {
        "qualitative_analysis": {
            "dynamic_profile": {
                "groups": [
                    {
                        "group_name": "Dalit / Scheduled Caste Candidates",
                        "primary_keyword": "Dalit",
                        "bias_category": "Ethnicity",
                        "bias_type": "explicit",
                        "sentiment": "negative",
                        "bias_intensity": 0.85,
                        "descriptors": ["underqualified", "quota beneficiaries", "less competent"],
                        "evidence": ["Dalit candidates were systematically rated lower despite matching qualifications"],
                        "justification": "Document explicitly discusses disparate treatment of SC/ST candidates in metro city hiring panels"
                    },
                    {
                        "group_name": "Women in Technical Roles",
                        "primary_keyword": "Women",
                        "bias_category": "Gender",
                        "bias_type": "implicit",
                        "sentiment": "negative",
                        "bias_intensity": 0.72,
                        "descriptors": ["less technical", "culture fit concerns", "attrition risk"],
                        "evidence": ["Female engineers received 23% fewer callbacks for senior positions"],
                        "justification": "Implicit assumptions about technical competence and retention risk applied to women candidates"
                    },
                    {
                        "group_name": "Candidates from Tier-2 Cities",
                        "primary_keyword": "Metro",
                        "bias_category": "Socioeconomic",
                        "bias_type": "implicit",
                        "sentiment": "mixed",
                        "bias_intensity": 0.58,
                        "descriptors": ["communication gaps", "adaptability concerns"],
                        "evidence": ["Candidates from non-metro backgrounds rated lower on 'culture fit' criteria"],
                        "justification": "Location-based assumptions used as proxy for soft skills assessment"
                    }
                ],
                "summary": {
                    "overall_bias": "high",
                    "dominant_bias_category": "Ethnicity",
                    "notes": "Document reveals systematic caste-based discrimination in Indian corporate hiring, compounded by gender and regional biases"
                }
            },
            "metadata": {
                "document_complexity": "High",
                "entity_density": 0.032,
                "ner_model": "spacy_en_core_web_sm",
                "llm_model": "gemini-2.0-flash",
                "total_entities": 47
            }
        },
        "quantitative_verification": [
            {
                "group": "Dalit",
                "keyword_frequency": 34,
                "co_occurring_negative_terms": 12,
                "sentiment_score": -0.67,
                "bias_confirmed": True
            },
            {
                "group": "Women",
                "keyword_frequency": 28,
                "co_occurring_negative_terms": 8,
                "sentiment_score": -0.43,
                "bias_confirmed": True
            },
            {
                "group": "Metro",
                "keyword_frequency": 15,
                "co_occurring_negative_terms": 4,
                "sentiment_score": -0.21,
                "bias_confirmed": True
            }
        ]
    },
    "recommendation": {
        "immediate_actions": [
            "Remove caste-identifiable information from initial screening stages",
            "Implement blind resume review for first-round evaluations",
            "Replace subjective 'culture fit' criteria with structured competency assessments"
        ],
        "systemic_changes": [
            "Mandatory bias awareness training for hiring panels",
            "Diverse interview panel composition requirements",
            "Regular third-party auditing of hiring funnel conversion rates by demographic group"
        ],
        "monitoring": [
            "Track callback rates segmented by caste, gender, and origin city",
            "Set up automated alerts when any group's conversion rate drops below 80% of the majority group",
            "Quarterly intersectional fairness reports to leadership"
        ]
    }
}


DEMO_MODEL_AUDIT = {
    "job_id": "demo-model-001",
    "status": "completed",
    "model_format_detected": "sklearn_pickle",
    "protected_column": "caste",
    "target_column": "approved",
    "total_predictions": 500,
    "verdict": {
        "is_model_biased": True,
        "bias_verdict": "BIASED",
        "bias_confidence": "High",
        "verdict_reason": "Model shows strong caste-based discrimination. SC/ST applicants face 62% higher rejection rate even with equivalent credit scores and income levels.",
        "flagged_metrics_count": 4,
        "worst_group": "SC",
        "worst_disparate_impact_ratio": 0.38
    },
    "bias_metrics": {
        "disparate_impact_ratio": {"General": 1.0, "OBC": 0.61, "SC": 0.38},
        "statistical_parity_difference": {"General": 0.0, "OBC": -0.19, "SC": -0.42},
        "equal_opportunity_difference": {"General": 0.0, "OBC": -0.15, "SC": -0.38},
        "false_positive_rate_ratio": {"General": 1.0, "OBC": 1.2, "SC": 1.8}
    },
    "shap_top_features": [
        {"feature": "caste", "importance": 0.34},
        {"feature": "credit_score", "importance": 0.28},
        {"feature": "income", "importance": 0.22},
        {"feature": "loan_amount", "importance": 0.11},
        {"feature": "age", "importance": 0.05}
    ],
    "counterfactual_example": {
        "original": {"age": 34, "caste": "SC", "income": 55000, "credit_score": 720, "loan_amount": 400000, "prediction": "REJECTED"},
        "counterfactual": {"age": 34, "caste": "General", "income": 55000, "credit_score": 720, "loan_amount": 400000, "prediction": "APPROVED"},
        "explanation": "Simply changing the caste from SC to General — with ALL other features identical — flips the model's decision from REJECTED to APPROVED. This is direct evidence of discriminatory decision-making."
    },
    "ai_narrative": [
        {
            "title": "Executive Summary",
            "content": "This loan approval model exhibits severe caste-based discrimination. Scheduled Caste (SC) applicants are systematically denied loans at rates 62% higher than General category applicants with identical financial profiles. The model has learned historical bias patterns from training data and amplifies them in predictions."
        },
        {
            "title": "Key Findings",
            "content": "1) Caste is the single most important feature (SHAP importance: 0.34), exceeding even credit score. 2) A counterfactual analysis proves direct discrimination: changing only the caste field from SC to General flips rejections to approvals. 3) OBC applicants face moderate bias (DIR: 0.61), while SC applicants face extreme bias (DIR: 0.38)."
        },
        {
            "title": "Regulatory Risk",
            "content": "This model violates India's constitutional prohibition on caste discrimination (Article 15), the Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, and would fail compliance under the EU AI Act's high-risk AI system requirements for credit scoring."
        }
    ],
    "governance": {
        "bias_scorecard": [
            {"metric_name": "Disparate Impact Ratio", "group": "SC", "score": 19, "raw_value": 0.38, "flagged": True},
            {"metric_name": "Disparate Impact Ratio", "group": "OBC", "score": 51, "raw_value": 0.61, "flagged": True},
            {"metric_name": "Statistical Parity Difference", "group": "SC", "score": 8, "raw_value": -0.42, "flagged": True},
            {"metric_name": "Equal Opportunity Difference", "group": "SC", "score": 12, "raw_value": -0.38, "flagged": True}
        ],
        "overall_fairness_score": 22,
        "audit_trail_id": "demo-trail-001",
        "remediation_plan": [
            {
                "priority": "CRITICAL",
                "action": "Remove Protected Attribute",
                "description": "Remove 'caste' as a direct input feature immediately",
                "steps": ["Drop caste column from feature set", "Retrain model without caste", "Validate DIR improves above 0.8"]
            },
            {
                "priority": "HIGH",
                "action": "Apply Fairlearn Mitigation",
                "description": "Use exponentiated gradient reduction to enforce demographic parity constraint",
                "steps": ["Install fairlearn", "Wrap model with ExponentiatedGradient", "Set DemographicParity constraint", "Retrain with constraint"]
            },
            {
                "priority": "HIGH",
                "action": "Audit Training Data",
                "description": "Historical lending data likely encodes decades of caste discrimination",
                "steps": ["Analyze approval rates in training data by caste", "Apply reweighing to balance historical bias", "Consider collecting new unbiased data"]
            }
        ],
        "pdf_export_ready": True
    },
    "timestamp": "2025-01-15T10:30:00Z"
}


DEMO_GRAPH_AUDIT = {
    "run_id": "demo-graph-001",
    "status": "success",
    "scorecard": {
        "timestamp": "2025-01-15T11:00:00Z",
        "graph_metadata": {
            "node_count": 100,
            "edge_count": 450,
            "is_directed": False
        },
        "protected_attribute": "group",
        "groups_found": ["Group A", "Group B"],
        "universal_metrics": {
            "demographic_parity": {"raw_value": 0.32, "score": 32, "status": "FAIL", "per_group": {"Group A": 0.72, "Group B": 0.40}},
            "equalized_odds": {"raw_value": 0.25, "score": 45, "status": "FAIL", "per_group": {"Group A": 0.85, "Group B": 0.60}},
            "disparate_impact": {"raw_value": 0.56, "score": 28, "status": "FAIL", "per_group": {"Group A": 1.0, "Group B": 0.56}},
            "predictive_parity": {"raw_value": 0.78, "score": 72, "status": "WARN", "per_group": {"Group A": 0.88, "Group B": 0.69}},
            "per_group_metrics": {
                "Group A": {"count": 50, "positive_rate": 0.72, "accuracy": 0.85, "tpr": 0.88, "fpr": 0.12},
                "Group B": {"count": 50, "positive_rate": 0.40, "accuracy": 0.62, "tpr": 0.60, "fpr": 0.35}
            }
        },
        "structural_metrics": {
            "degree_disparity": {"raw_value": 0.45, "score": 35, "status": "FAIL", "per_group": {"Group A": 12.3, "Group B": 6.8}},
            "pagerank_disparity": {"raw_value": 0.38, "score": 42, "status": "FAIL", "per_group": {"Group A": 0.015, "Group B": 0.008}},
            "clustering_disparity": {"raw_value": 0.22, "score": 68, "status": "WARN", "per_group": {"Group A": 0.45, "Group B": 0.35}},
            "homophily_coefficient": {"raw_value": 0.82, "score": 18, "status": "FAIL", "per_group": {"Group A": 0.85, "Group B": 0.79}},
            "prediction_centrality_correlation": {"raw_value": 0.67, "score": 33, "status": "FAIL", "per_group": {"Group A": 0.72, "Group B": 0.45}}
        },
        "global_explanation": {
            "top_bias_drivers": [
                {"factor": "High Homophily", "description": "Nodes predominantly connect within their own group (coefficient: 0.82), creating information silos that disadvantage minority group in prediction tasks", "severity": "high"},
                {"factor": "Degree Disparity", "description": "Group A nodes have 81% more connections on average, giving them disproportionate influence in graph-based models", "severity": "high"},
                {"factor": "Centrality-Prediction Correlation", "description": "High correlation (0.67) between node centrality and positive predictions suggests the model rewards network position over individual merit", "severity": "medium"}
            ],
            "summary": "This graph exhibits severe structural bias. High homophily (0.82) creates echo chambers where Group B nodes are isolated from positive-prediction clusters. Combined with degree disparity, Group B faces systemic disadvantage regardless of individual features."
        },
        "overall_score": 35,
        "overall_status": "FAIL",
        "key_findings": [
            "Group B receives positive predictions at only 56% the rate of Group A",
            "Network structure alone accounts for ~45% of prediction disparity",
            "Homophily coefficient of 0.82 indicates near-complete group segregation",
            "Removing network features would improve fairness by estimated 40%"
        ],
        "top_risk_groups": ["Group B"]
    },
    "gemini_report": {
        "summary": "Critical structural bias detected in this social network graph. Group B nodes are systematically disadvantaged due to high homophily (0.82) and degree disparity, resulting in 56% lower positive prediction rates compared to Group A.",
        "bias_found": "Group B faces compounded disadvantage: fewer connections (avg 6.8 vs 12.3), lower centrality, and isolation from positive-prediction clusters. The model amplifies structural inequality into prediction inequality.",
        "likely_causes": "1) Training data reflects historical network formation patterns that segregated groups. 2) Graph neural network architecture propagates majority-group signals through dense intra-group connections. 3) Features derived from network position (PageRank, degree) encode group membership as proxy.",
        "remediation": "1) Apply FairWalk or CrossWalk to generate debiased node embeddings. 2) Add cross-group edges through recommendation diversification. 3) Use adversarial debiasing to remove protected attribute signal from embeddings. 4) Implement Fairlearn's ExponentiatedGradient with DemographicParity constraint on the downstream classifier.",
        "severity_assessment": "HIGH",
        "regulatory_note": "Under the EU AI Act (Article 10), high-risk AI systems must use training data that is sufficiently representative. This graph's structural bias would require documented mitigation measures and ongoing monitoring under Article 9 risk management requirements."
    },
    "warnings": []
}


@router.get("/dataset-audit")
async def demo_dataset_audit():
    """Returns pre-computed dataset audit results for demo purposes."""
    return JSONResponse(content=DEMO_DATASET_AUDIT)


@router.get("/document-audit")
async def demo_document_audit():
    """Returns pre-computed document audit results for demo purposes."""
    return JSONResponse(content=DEMO_DOCUMENT_AUDIT)


@router.get("/model-audit")
async def demo_model_audit():
    """Returns pre-computed ML model audit results for demo purposes."""
    return JSONResponse(content=DEMO_MODEL_AUDIT)


@router.get("/graph-audit")
async def demo_graph_audit():
    """Returns pre-computed graph model audit results for demo purposes."""
    return JSONResponse(content=DEMO_GRAPH_AUDIT)


@router.get("/all")
async def demo_all():
    """Returns all demo audits at once for the overview demo mode."""
    return JSONResponse(content={
        "dataset_audit": DEMO_DATASET_AUDIT,
        "document_audit": DEMO_DOCUMENT_AUDIT,
        "model_audit": DEMO_MODEL_AUDIT,
        "graph_audit": DEMO_GRAPH_AUDIT,
    })
