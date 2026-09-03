import pytest
from dotenv import load_dotenv

from src import database

load_dotenv()

@pytest.fixture(scope="session")
def conn():
    """Banco em memória criado uma única vez para toda a sessão de testes."""
    return database.build_database()
