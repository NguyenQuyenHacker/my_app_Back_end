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
    """Return the list of available Knowledge Bases (table name and description only)."""
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


# =========================
# HYBRID SEARCH CONFIG
# =========================
TOP_K = 3            # số chunk cuối cùng trả về cho agent
FETCH_K = 10         # số ứng viên lấy ra từ mỗi nhánh (vector / keyword) trước khi gộp
RRF_K = 60           # hằng số Reciprocal Rank Fusion (chuẩn = 60)
FTS_CONFIG = "simple"  # text search config của Postgres (simple: không stemming, hợp tiếng Việt)


def _keyword_search(table_name: str, query: str, limit: int) -> list[dict]:
    """Full-text search (BM25-style) trực tiếp trên cột `content` bằng Postgres FTS.

    Chạy được trên bảng vector hiện có mà KHÔNG cần thêm cột tsvector/GIN index
    (tính to_tsvector on-the-fly). Trả về list dict theo thứ tự liên quan giảm dần.
    """
    # plainto_tsquery AND tất cả token → câu hỏi tự nhiên ("...là bao nhiêu?")
    # gần như không khớp. Đổi '&' thành '|' để thành OR query: khớp bất kỳ từ,
    # rồi ts_rank tự xếp chunk khớp nhiều từ quan trọng lên đầu.
    sql = text(
        f'''
        WITH q AS (
            SELECT replace(plainto_tsquery(:cfg, :q)::text, '&', '|')::tsquery AS tsq
        )
        SELECT content, langchain_metadata
        FROM "{SCHEMA_NAME}"."{table_name}", q
        WHERE q.tsq IS NOT NULL
          AND to_tsvector(:cfg, content) @@ q.tsq
        ORDER BY ts_rank(to_tsvector(:cfg, content), q.tsq) DESC
        LIMIT :lim
        '''
    )
    with _sa_engine.connect() as conn:
        rows = conn.execute(
            sql, {"cfg": FTS_CONFIG, "q": query, "lim": limit}
        ).fetchall()
    return [{"content": r[0], "metadata": r[1] or {}} for r in rows]


def _reciprocal_rank_fusion(
    ranked_lists: list[list[dict]], k: int, rrf_k: int = RRF_K
) -> list[dict]:
    """Gộp nhiều danh sách đã xếp hạng thành một bằng RRF.

    Điểm mỗi item = tổng 1/(rrf_k + rank) qua từng list. Khóa gộp = nội dung chunk.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            key = item["content"]
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            items.setdefault(key, item)
    ordered = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [items[key] for key in ordered[:k]]


@tool
def retrieve_context(query: str, kb_table_name: str) -> str:
    """Retrieve relevant context from a specific vector database to help answer the question. You must call list_available_knowledge_bases first to obtain kb_table_name."""
    # --- Nhánh 1: vector (semantic) search ---
    try:
        vector_store = get_vector_store(kb_table_name)
        vector_docs = vector_store.similarity_search(query, k=FETCH_K)
        vector_results = [
            {"content": d.page_content, "metadata": d.metadata} for d in vector_docs
        ]
    except Exception as e:
        return f"Lỗi khi truy xuất vector database bảng '{kb_table_name}': {str(e)}"

    # --- Nhánh 2: keyword (full-text) search ---
    # Lỗi FTS không được làm hỏng cả tool — vẫn fallback về kết quả vector.
    try:
        keyword_results = _keyword_search(kb_table_name, query, FETCH_K)
    except Exception:
        keyword_results = []

    # --- Gộp 2 nhánh bằng RRF ---
    docs = _reciprocal_rank_fusion([vector_results, keyword_results], k=TOP_K)

    if not docs:
        return f"Không tìm thấy tài liệu liên quan trong bảng {kb_table_name}."

    blocks = []
    for i, doc in enumerate(docs, start=1):
        meta = doc["metadata"] or {}
        file_name = meta.get("file_name", "unknown")
        chunk_index = meta.get("chunk_index", "unknown")
        content = (doc["content"] or "").strip()
        blocks.append(f"[Nguồn {i}] file={file_name}, chunk={chunk_index}\n{content}")

    return "\n\n".join(blocks)
