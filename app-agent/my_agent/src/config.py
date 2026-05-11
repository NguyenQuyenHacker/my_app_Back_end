import os
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
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file config.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Đi ngược lên 1 cấp (vào folder my_agent) rồi vào prompts
    prompt_path = os.path.join(os.path.dirname(current_dir), "prompts", "system_prompt.md")
    
    try:
        print(f"DEBUG: Attempting to load prompt from: {prompt_path}")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"DEBUG: Prompt file found. Size: {len(content)} bytes.")
                return content
        else:
            print(f"Warning: Prompt file not found at {prompt_path}")
    except Exception as e:
        print(f"Warning: Could not load system_prompt.md: {e}")
    
    return "You are an intelligent assistant."

system_prompt_content = load_system_prompt()
# Force reload 4
