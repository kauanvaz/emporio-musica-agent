import pytest
from src import rag


@pytest.fixture(scope="session")
def index():
    return rag.get_policy_index()


def test_index_has_documents(index):
    assert index.index.ntotal > 0


def test_retrieve_devolucao(index):
    docs = rag.retrieve_policy(index, "política de troca e devolução", k=3)
    assert docs


def test_retrieve_horario(index):
    docs = rag.retrieve_policy(index, "horário de funcionamento", k=3)
    texto = " ".join(doc.page_content for doc in docs).lower()
    assert "hor" in texto or "funcionamento" in texto
