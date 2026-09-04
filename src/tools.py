"""Definição das ferramentas (tools) do agente."""

import json

from langchain.tools import tool

from src import database, rag

@tool
def search_products(term: str = "") -> str:
    """Busca produtos disponíveis em estoque por termo (categoria, nome ou descrição).

    Use para perguntas sobre "tem X?", "quais [categoria]?", "produtos de [marca]?",
    disponibilidade e catálogo. A busca é feita de forma flexível: corresponde ao
    termo no NOME do produto, no NOME da CATEGORIA ou na DESCRIÇÃO (case-insensitive),
    e só retorna produtos com status='active' e ajustes em estoque.

    Entrada: um termo (ex.: "ukulele", "teclado", "violão", "Takamine", "guitarra").
    Se vazio, retorna os primeiros produtos disponíveis.
    """
    conn = database.db_connection()

    def describe(rows):
        nome_cat = {r[0]: r[1] for r in conn.execute("SELECT category_id, name FROM categories")}
        out = []
        for r in rows:
            out.append({
                "name": r[0],
                "price_brl": r[1],
                "stock_quantity": r[2],
                "category": nome_cat.get(r[3], ""),
            })
        return out

    base = """
        SELECT p.name, p.price_brl, p.stock_quantity, p.category_id
        FROM products p
        WHERE p.status='active' AND p.stock_quantity > 0
    """
    clean_term = term.strip()
    if clean_term:
        # Busca por nome, categoria ou descrição
        # para robustez, o termo é normalizado com LOWER e buscado em LOWER(coluna).
        sql = base + """
            AND (LOWER(p.name) LIKE '%' || ? || '%'
                 OR LOWER(p.description) LIKE '%' || ? || '%'
                 OR p.category_id IN (
                     SELECT category_id FROM categories WHERE LOWER(name) LIKE '%' || ? || '%'
                 ))
            ORDER BY p.price_brl LIMIT 25
        """
        normalized = clean_term.lower()
        cursor = conn.execute(sql, (normalized, normalized, normalized))
    else:
        cursor = conn.execute(base + " ORDER BY p.price_brl LIMIT 10")

    rows = cursor.fetchall()
    if not rows:
        return json.dumps({"sem_resultados": True, "dados": []})
    return json.dumps({"sem_resultados": False, "dados": describe(rows)}, ensure_ascii=False, default=str)

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


@tool
def query_policy(subject: str) -> str:
    """Consulta o manual de políticas da loja e retorna os trechos relevantes ao tema.

    Use para dúvidas sobre regras, horários, formas de pagamento, trocas e
    devoluções, prazos de entrega/frete, garantia, contato, telefone, endereço, e-mail e políticas diversas.
    """
    index = rag.get_policy_index()
    docs = rag.retrieve_policy(index, subject, k=4)
    if not docs:
        return "Nenhum trecho de política encontrado para o tema informado."
    return "\n\n".join(f"[Trecho relevante]\n{doc.page_content}" for doc in docs)


TOOLS = [list_tables, schema_tables, run_sql, query_policy, search_products]

def table_descriptions() -> str:
    """Texto auxiliar descritivo das tabelas, injetado no prompt para ajudar a LLM."""
    return (
        "- customers: customer_id, name, phone, email, city\n"
        "- categories: category_id, name, description\n"
        "- products: product_id, price_brl, name, category_id, description, "
        "stock_quantity, status (active/discontinued/coming_soon), specs, created_at\n"
        "- orders: order_id, customer_id, order_date, status (delivered/shipped/"
        "confirmed/pending/cancelled), total_brl, payment_method, tracking_code, "
        "estimated_delivery, notes\n"
        "- order_items: order_id, quantity, product_id\n"
        "- promotions: promotion_id, product_id, discount_percent, description, "
        "is_active (1=ativa)"
    )
