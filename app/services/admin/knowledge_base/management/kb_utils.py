from sqlalchemy import MetaData, Table
from sqlmodel import Session

def get_chunk_table(session: Session, table_name: str) -> Table:
    metadata = MetaData()
    return Table(
        table_name,
        metadata,
        autoload_with=session.get_bind(),
    )
