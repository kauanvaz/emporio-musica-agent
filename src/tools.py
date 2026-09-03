"""Definição das ferramentas (tools) do agente."""

from langchain.tools import tool

from src import database

@tool
def list_tables() -> str:
    """Lista os nomes das tabelas disponíveis no banco de dados da loja.

    Use esta ferramenta antes de qualquer consulta para conhecer as tabelas
    (customers, categories, products, orders, order_items, promotions).
    Entrada: nenhuma. Saída: lista separada por vírgula.
    """
    return ", ".join(database.list_tables(database.db_connection()))


@tool
def schema_tables(table_names: str) -> str:
    """Retorna o schema (colunas e tipos) das tabelas informadas.

    Entrada: nomes de tabelas separados por vírgula (ex.: "products, promotions").
    Saída: DDL de criação + uma amostra de 3 linhas de cada tabela.
    Use esta ferramenta quando não souber as colunas exatas para montar a query.
    """
    conn = database.db_connection()
    parts = [database.table_schema(conn, name.strip()) for name in table_names.split(",") if name.strip()]
    return "\n\n".join(parts)


@tool
def run_sql(query: str) -> str:
    """Executa uma consulta SQL somente-leitura e retorna o resultado em JSON.

    Use para obter dados concretos: produtos, preços, disponibilidade/estoque,
    status de pedidos, promoções ativas, dados de clientes.
    Regras importantes:
      - Apenas SELECT é permitido (escritas são bloqueadas).
      - Escreva SQL válido para SQLite.
      - Use tabelas e colunas descobertas com as ferramentas list_tables/schema_tables.
    """
    return database.run_select_query(database.db_connection(), query)
