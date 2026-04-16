import os
import sys
import asyncio
from typing import Optional

from sqlalchemy import create_engine, text
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_postgres import PGVectorStore, PGEngine

# =========================
# WINDOWS EVENT LOOP
# =========================
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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
# LAZY VECTOR STORE
# =========================
_vector_stores: dict[str, PGVectorStore] = {}


def get_vector_store(table_name: str) -> PGVectorStore:
    global _vector_stores

    if table_name not in _vector_stores:
        engine = PGEngine.from_connection_string(VECTOR_DB_URL)

        _vector_stores[table_name] = PGVectorStore.create_sync(
            engine=engine,
            table_name=table_name,
            schema_name=SCHEMA_NAME,
            embedding_service=embedding_service,
        )

    return _vector_stores[table_name]


# =========================
# TOOLS
# =========================
@tool
def list_available_knowledge_bases() -> str:
    """Trả về danh sách các Knowledge Base có sẵn (chỉ bao gồm Tên bảng và Mô tả)."""
    try:
        engine = create_engine(VECTOR_DB_URL)
        with engine.connect() as conn:
            query = text("SELECT table_name, description FROM knowledge_bases WHERE is_active = true")
            result = conn.execute(query).fetchall()
        
        if not result:
            return "Hiện tại không có Knowledge Base nào đang hoạt động."
            
        blocks = ["Danh sách các Knowledge Base hiện có:"]
        for row in result:
            t_name, desc = row
            desc_text = desc if desc else "Không có mô tả"
            blocks.append(f"- Tên bảng (table_name): '{t_name}' | Mô tả: '{desc_text}'")
            
        return "\n".join(blocks)
    except Exception as e:
        return f"Lỗi khi lấy danh sách Knowledge Base: {str(e)}"


@tool
def retrieve_context(query: str, kb_table_name: str) -> str:
    """Truy xuất context liên quan từ một vector database cụ thể để hỗ trợ trả lời câu hỏi. Bạn phải gọi list_available_knowledge_bases trước để lấy kb_table_name."""
    try:
        vector_store = get_vector_store(kb_table_name)
        docs = vector_store.similarity_search(query, k=2)
    except Exception as e:
        return f"Lỗi khi truy xuất vector database bảng '{kb_table_name}': {str(e)}"

    if not docs:
        return f"Không tìm thấy tài liệu liên quan trong bảng {kb_table_name}."

    blocks = []
    for i, doc in enumerate(docs, start=1):
        file_name = doc.metadata.get("file_name", "unknown")
        chunk_index = doc.metadata.get("chunk_index", "unknown")
        content = doc.page_content.strip()

        blocks.append(
            f"[Nguồn {i}] file={file_name}, chunk={chunk_index}\n{content}"
        )

    return "\n\n".join(blocks)


# =========================
# MODEL
# =========================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=GOOGLE_API_KEY,
)


# =========================
# GRAPH
# =========================
graph = create_agent(
    model=llm,
    tools=[list_available_knowledge_bases, retrieve_context],
    system_prompt=(
        "You are an intelligent assistant with access to multiple knowledge bases. "
        "When asked a question, ALWAYS use the `list_available_knowledge_bases` tool first to find the most relevant table, "
        "unless you already know which table to use. "
        "Then, use the `retrieve_context` tool with the appropriate `kb_table_name` to find the answer. "
        "If the retrieved context does not contain relevant information, say that you don't know."
    ),
)