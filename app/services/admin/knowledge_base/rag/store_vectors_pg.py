from sqlmodel import Session
from sqlalchemy import inspect
from langchain_postgres import PGEngine, PGVectorStore
from app.db.database import DATABASE_URL_ADMIN
from app.utils.embedding_utils import get_embedding_model

def init_and_store_vectors(session: Session, table_name: str, split_docs: list):
    """Khởi tạo table và thêm chunks vào PGVector database."""
    
    embedding_model = get_embedding_model()
    vector_size = len(embedding_model.embed_query("hello world"))

    # Kiểm tra bảng đã tồn tại chưa bằng chính session hiện có (Clean & SQLModel style)
    if not inspect(session.bind).has_table(table_name):
        # Nếu chưa có thì dùng lệnh khởi tạo qua PGEngine
        pg_engine = PGEngine.from_connection_string(
            url=DATABASE_URL_ADMIN,
            connect_args={"prepare_threshold": 0},
        )
        pg_engine.init_vectorstore_table(
            table_name=table_name,
            vector_size=vector_size,
        )

    # Khởi tạo Vector Store
    pg_engine = PGEngine.from_connection_string(
        url=DATABASE_URL_ADMIN,
        connect_args={"prepare_threshold": 0},
    )
    vector_store = PGVectorStore.create_sync(
        engine=pg_engine,
        table_name=table_name,
        embedding_service=embedding_model,
    )

    vector_store.add_documents(split_docs)
