"""Pipeline RAG para o manual de políticas da Empório da Música."""
import os
from pathlib import Path
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

POLICIES_PDF = Path(os.getenv("POLICIES_PDF", "data/políticas_da_loja.pdf"))
INDEX_DIR = Path(".cache") / "policy_index"

_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 100
_TOP_K = 4

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def _get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def _normalize_text(texto: str) -> str:
    """Normaliza o texto extraído do PDF.

    O PyPDFLoader frequentemente quebra em cada palavra,
    o que degrada o retrieval por embeddings por fragmentar os trechos.
    Essa função reconstrói o texto contínuo, colapsando
    espaços e quebras de linha em um espaço simples.
    """
    return re.sub(r"\s+", " ", texto).strip()


def _build_policy_index() -> FAISS:
    """Carrega o PDF e constrói o índice vetorial FAISS"""
    loader = PyPDFLoader(str(POLICIES_PDF))
    pages = loader.load()
    
    # Normaliza o texto de cada página antes de dividir em chunks.
    for page in pages:
        page.page_content = _normalize_text(page.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=_CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)

    embeddings = _get_embeddings()
    index = FAISS.from_documents(chunks, embeddings)
    return index


def get_policy_index() -> FAISS:
    """Retorna o índice, carregando do cache em disco se existir"""
    if (INDEX_DIR / "index.faiss").exists():
        # Carrega do cache sem precisar re-embeddar o PDF
        
        embeddings = _get_embeddings()
        return FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)

    index = _build_policy_index()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index.save_local(str(INDEX_DIR))
    return index


def retrieve_policy(index: FAISS, subject: str, k: int = _TOP_K) -> list:
    """Retorna os trechos do manual mais relevantes ao tema informado"""
    return index.similarity_search(subject, k=k)
