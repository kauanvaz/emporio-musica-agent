"""Pipeline RAG para o manual de políticas da Empório da Música."""
import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

POLICIES_PDF = Path(os.getenv("POLICIES_PDF", "data/políticas_da_loja.pdf"))
INDEX_DIR = Path(".cache") / "policy_index"

_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 100
_TOP_K = 4


def _build_policy_index() -> FAISS:
    """Carrega o PDF e constrói o índice vetorial FAISS"""
    loader = PyPDFLoader(str(POLICIES_PDF))
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=_CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)

    embeddings = OpenAIEmbeddings()
    index = FAISS.from_documents(chunks, embeddings)
    return index


def get_policy_index() -> FAISS:
    """Retorna o índice, carregando do cache em disco se existir"""
    if (INDEX_DIR / "index.faiss").exists():
        # Carrega do cache sem precisar re-embeddar o PDF
        model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        embeddings = OpenAIEmbeddings(model=model_name)
        return FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)

    index = _build_policy_index()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index.save_local(str(INDEX_DIR))
    return index


def retrieve_policy(index: FAISS, subject: str, k: int = _TOP_K) -> list:
    """Retorna os trechos do manual mais relevantes ao tema informado"""
    return index.similarity_search(subject, k=k)
