from langchain_text_splitters import RecursiveCharacterTextSplitter

def _split_documents(documents, chunk_size: int, chunk_overlap: int):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return text_splitter.split_documents(documents)
