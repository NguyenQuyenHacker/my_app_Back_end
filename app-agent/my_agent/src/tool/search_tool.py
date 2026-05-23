# app-agent/my_agent/src/tool/search_tool.py
from sqlalchemy import create_engine, text
from langchain.tools import tool
from langchain_postgres import PGVectorStore, PGEngine

from my_agent.src.config import VECTOR_DB_URL, SCHEMA_NAME, embedding_service

# =========================
# SHARED ENGINES (module-level singletons)
# =========================
_sa_engine = create_engine(VECTOR_DB_URL, pool_pre_ping=True)
_pg_engine: PGEngine | None = None
_vector_stores: dict[str, PGVectorStore] = {}


def _get_pg_engine() -> PGEngine:
    global _pg_engine
    if _pg_engine is None:
        _pg_engine = PGEngine.from_connection_string(VECTOR_DB_URL)
    return _pg_engine


def get_vector_store(table_name: str) -> PGVectorStore:
    if table_name not in _vector_stores:
        _vector_stores[table_name] = PGVectorStore.create_sync(
            engine=_get_pg_engine(),
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
        with _sa_engine.connect() as conn:
            query = text("SELECT table_name, description FROM knowledge_bases WHERE is_active = true")
            result = conn.execute(query).fetchall()
    except Exception as e:
        return f"Lỗi khi lấy danh sách Knowledge Base: {str(e)}"

    if not result:
        return "Hiện tại không có Knowledge Base nào đang hoạt động."

    blocks = ["Danh sách các Knowledge Base hiện có:"]
    for t_name, desc in result:
        desc_text = desc if desc else "Không có mô tả"
        blocks.append(f"- Tên bảng (table_name): '{t_name}' | Mô tả: '{desc_text}'")

    return "\n".join(blocks)


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
        blocks.append(f"[Nguồn {i}] file={file_name}, chunk={chunk_index}\n{content}")

    return "\n\n".join(blocks)
