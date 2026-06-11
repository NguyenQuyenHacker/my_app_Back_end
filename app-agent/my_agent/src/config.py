import os
from datetime import date

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY")

GOOGLE_API_KEY_FALLBACK_1 = os.getenv("GOOGLE_API_KEY_FALLBACK_1") or GOOGLE_API_KEY
GOOGLE_API_KEY_FALLBACK_2 = os.getenv("GOOGLE_API_KEY_FALLBACK_2") or GOOGLE_API_KEY

VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
if not VECTOR_DB_URL:
    raise RuntimeError("Missing required environment variable: VECTOR_DB_URL")

SCHEMA_NAME = os.getenv("VECTOR_SCHEMA_NAME", "public")


embedding_service = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY,
)


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
    thinking_budget=256,  
)

llm_fallback_1 = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY_FALLBACK_1,
    thinking_budget=256,
)

llm_fallback_2 = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY_FALLBACK_2,
    thinking_budget=256,
)


def load_system_prompt() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(os.path.dirname(current_dir), "prompts", "system_prompt.md")

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"System prompt not found at {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()  

    from my_agent.src.bank_codes import bank_list_for_prompt
    content = content.replace("{{BANK_LIST}}", bank_list_for_prompt())
    content = content.replace("{{TODAY}}", date.today().isoformat())
    return content


system_prompt_content = load_system_prompt()
