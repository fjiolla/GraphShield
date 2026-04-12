# """
# struct_local_config.py
# Configuration module for Zero-Cost Bias Detection Pipeline.
# Loads Gemini API key from .env and initializes the google-generativeai client.
# Designed for future migration to Google Cloud (GCP) with minimal changes.
# """

# import os
# import logging
# from pathlib import Path
# from dotenv import load_dotenv
# # import google.genai as genai
# import google.generativeai as genai

# # ─────────────────────────────────────────────
# # Logging
# # ─────────────────────────────────────────────
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
# )
# struct_logger = logging.getLogger("struct_local_config")

# # ─────────────────────────────────────────────
# # Load environment variables
# # ─────────────────────────────────────────────
# BASE_DIR = Path(__file__).resolve().parent
# while BASE_DIR.name != "bias-audit-backend" and BASE_DIR.parent != BASE_DIR:
#     BASE_DIR = BASE_DIR.parent

# _ENV_PATH = BASE_DIR / ".env"
# load_dotenv(dotenv_path=_ENV_PATH)
# load_dotenv(dotenv_path=_ENV_PATH)

# GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# if not GOOGLE_API_KEY:
#     struct_logger.warning(
#         "GOOGLE_API_KEY not found in environment. "
#         "Gemini-dependent modules will fail. "
#         "Set GOOGLE_API_KEY in your .env file."
#     )

# # ─────────────────────────────────────────────
# # SQLite / BigQuery paths
# # Future Migration: Replace SQLITE_DB_PATH with BigQuery dataset reference.
# # ─────────────────────────────────────────────
# DATA_DIR: str = str(BASE_DIR / "data")
# SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "local_vault.db")
# os.makedirs(DATA_DIR, exist_ok=True)

# # ─────────────────────────────────────────────
# # Gemini model settings
# # ─────────────────────────────────────────────
# GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
# GEMINI_SAMPLE_LIMIT: int = 50          # rows sent to Gemini for semantic analysis
# GEMINI_MAX_OUTPUT_TOKENS: int = 2048
# GEMINI_TEMPERATURE: float = 0.2        # low temperature for deterministic JSON output

# # ─────────────────────────────────────────────
# # Initialize Gemini client
# # ─────────────────────────────────────────────
# def struct_init_gemini() -> genai.GenerativeModel:
#     """
#     Configure and return a Gemini GenerativeModel instance.

#     Returns:
#         genai.GenerativeModel: Ready-to-use model instance.

#     Raises:
#         EnvironmentError: If GOOGLE_API_KEY is not set.
#     """
#     if not GOOGLE_API_KEY:
#         raise EnvironmentError(
#             "GOOGLE_API_KEY is missing. "
#             "Add it to your .env file before running Gemini-dependent modules."
#         )

#     genai.configure(api_key=GOOGLE_API_KEY)

#     generation_config = genai.types.GenerationConfig(
#         temperature=GEMINI_TEMPERATURE,
#         max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
#     )

#     model = genai.GenerativeModel(
#         model_name=GEMINI_MODEL_NAME,
#         generation_config=generation_config,
#     )

#     struct_logger.info("Gemini client initialized with model: %s", GEMINI_MODEL_NAME)
#     return model


# # ─────────────────────────────────────────────
# # Singleton model instance (lazy)
# # ─────────────────────────────────────────────
# _struct_gemini_model: genai.GenerativeModel | None = None


# def struct_get_gemini_model() -> genai.GenerativeModel:
#     """
#     Return a cached Gemini model instance (initializes on first call).

#     Returns:
#         genai.GenerativeModel
#     """
#     global _struct_gemini_model
#     if _struct_gemini_model is None:
#         _struct_gemini_model = struct_init_gemini()
#     return _struct_gemini_model


# # ─────────────────────────────────────────────
# # GCP Migration Stubs
# # Uncomment and configure when migrating to Google Cloud.
# # ─────────────────────────────────────────────
# # GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
# # GCP_DATASET_ID: str = os.getenv("GCP_DATASET_ID", "bias_audit_dataset")
# # GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "bias-audit-uploads")
# #
# # def struct_init_bigquery():
# #     from google.cloud import bigquery
# #     return bigquery.Client(project=GCP_PROJECT_ID)
# #
# # def struct_init_gcs():
# #     from google.cloud import storage
# #     return storage.Client(project=GCP_PROJECT_ID)

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
struct_logger = logging.getLogger("struct_local_config")


BASE_DIR = Path(__file__).resolve().parent
while BASE_DIR.name != "GSC" and BASE_DIR.parent != BASE_DIR:
    BASE_DIR = BASE_DIR.parent

_ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    struct_logger.warning(
        "GROQ_API_KEY not found. Groq-dependent modules will fail."
    )

DATA_DIR: str = str(BASE_DIR / "data")
SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "local_vault.db")
os.makedirs(DATA_DIR, exist_ok=True)


GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"
GROQ_TEMPERATURE: float = 0.2


def struct_init_groq() -> Groq:
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    client = Groq(api_key=GROQ_API_KEY)
    struct_logger.info("Groq client initialized with model: %s", GROQ_MODEL_NAME)
    return client


_struct_groq_client: Groq | None = None


def struct_get_groq_client() -> Groq:
    global _struct_groq_client
    if _struct_groq_client is None:
        _struct_groq_client = struct_init_groq()
    return _struct_groq_client