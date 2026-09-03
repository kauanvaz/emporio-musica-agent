import pytest
from src import database


@pytest.fixture(scope="session")
def conn():
    """Banco em memória criado uma única vez para toda a sessão de testes."""
    return database.build_database()
