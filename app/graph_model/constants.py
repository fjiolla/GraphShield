"""
Constants and configurations for the graph bias pipeline.
"""

# Fairness thresholds
DEMOGRAPHIC_PARITY_THRESHOLD = 0.8
EQUALIZED_ODDS_THRESHOLD = 0.1
DISPARATE_IMPACT_THRESHOLD = 0.8
HOMOPHILY_THRESHOLD = 0.6
DEGREE_DISPARITY_THRESHOLD = 1.5
PAGERANK_DISPARITY_THRESHOLD = 1.5

# Score ranges for 0-100 normalization
SCORE_FAIL_BELOW = 60
SCORE_WARN_BELOW = 80

# Supported file extensions
GML_EXTENSIONS = [".gml"]
CSV_EXTENSIONS = [".csv"]
JSONLD_EXTENSIONS = [".json", ".jsonld"]
MODEL_EXTENSIONS_CLASSICAL = [".pkl", ".joblib"]
MODEL_EXTENSIONS_PYTORCH = [".pt", ".pth"]

# LLM config
GEMINI_MODEL = "gemini-pro"
GROQ_MODEL = "llama3-8b-8192" # Or llama-3-70b-8192
