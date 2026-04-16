import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

os.environ["GOOGLE_API_KEY"] = "AIzaSyCE5nj-w477uODkLcNxPVSPFm8T6sG-UUo"



def get_embedding_model():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )
