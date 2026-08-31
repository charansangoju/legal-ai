from ai_engine.rag.retrieval import retrieve
from ai_engine.rag.generator import generate_answer

def answer(text: str, question: str, api_key: str = None) -> str:
    chunks = retrieve(text, question, k=5)
    return generate_answer(question, chunks, full_text=text, user_api_key=api_key)

