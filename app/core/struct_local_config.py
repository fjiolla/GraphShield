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


BASE_DIR = Path(__file__).resolve().parent.parent.parent
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


GROQ_MODEL_NAME: str = "llama-3.3-70b-versatile"
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