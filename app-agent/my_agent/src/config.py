import os
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# =========================
# CONFIG
# =========================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY")

VECTOR_DB_URL = os.getenv(
    "VECTOR_DB_URL",
    "postgresql+psycopg://fastapi_user:123456@host.docker.internal:5434/banking_db",
)

SCHEMA_NAME = os.getenv("VECTOR_SCHEMA_NAME", "public")


# =========================
# EMBEDDING
# =========================
embedding_service = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY,
)


# =========================
# MODEL (LLM)
# =========================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
)


# =========================
# LOAD SYSTEM PROMPT
# =========================
def load_system_prompt() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(os.path.dirname(current_dir), "prompts", "system_prompt.md")

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"System prompt not found at {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Inject các placeholder data
    from my_agent.src.bank_codes import bank_list_for_prompt
    content = content.replace("{{BANK_LIST}}", bank_list_for_prompt())
    content = content.replace("{{TODAY}}", date.today().isoformat())
    return content


system_prompt_content = load_system_prompt()
