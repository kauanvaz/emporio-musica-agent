"""Conversão dos CSVs para um banco SQLite e acesso seguro aos dados"""

import json
import os
from pathlib import Path

import pandas as pd
import sqlite3

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

_CSV_COLUMNS: dict[str, list[str]] = {
    "customers": ["customer_id", "name", "phone", "email", "city"],
    "categories": ["category_id", "name", "description"],
    "products": [
        "product_id", "price_brl", "name", "category_id", "description",
        "stock_quantity", "status", "specs", "created_at",
    ],
    "orders": [
        "order_id", "customer_id", "order_date", "status", "total_brl",
        "payment_method", "tracking_code", "estimated_delivery", "notes",
    ],
    "order_items": ["order_id", "quantity", "product_id"],
    "promotions": [
        "promotion_id", "product_id", "discount_percent", "description", "is_active",
    ],
}

# Lista dos commandos perigosos NÃO permitidos em consultas geradas pela LLM
_FORBIDDEN_STATEMENTS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE", "ATTACH"}


def _normalize(csv_path: Path) -> pd.DataFrame:
    """Lê um CSV e ajusta tipos básicos para facilitar as queries do agente."""
    df = pd.read_csv(csv_path, encoding="utf-8")
    # Conserta o "specs" que vem como JSON string em products.
    for col in df.columns:
        if col in {"price_brl", "total_brl", "discount_percent", "stock_quantity"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif col in {"is_active"}:
            df[col] = df[col].astype(int)
    return df


def build_database(db_path: str | None = None) -> sqlite3.Connection:
    """
    Converte todos os CSVs de ``data/`` para tabelas SQLite.

    Se ``db_path`` for None, cria um banco **em memória** (ideal para o agente,
    que não precisa persistir o catálogo). Caso contrário grava em arquivo
    (útil para inspecao/depuração com um cliente SQL).
    """
    param = db_path or ":memory:"
    conn = sqlite3.connect(param)
    for table, columns in _CSV_COLUMNS.items():
        csv_file = DATA_DIR / f"{table}.csv"
        df = _normalize(csv_file)
        df.to_sql(table, conn, if_exists="replace", index=False)

    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    """Retorna os nomes das tabelas do banco."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    return [row[0] for row in cur.fetchall()]


def table_schema(conn: sqlite3.Connection, table: str) -> str:
    """Retorna o SQL de criação da tabela (schema) + amostra de 3 linhas."""
    cur = conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,))
    row = cur.fetchone()
    schema = row[0] if row else f"Tabela '{table}' não encontrada."
    sample = conn.execute(f'SELECT * FROM "{table}" LIMIT 3;').fetchall()
    return f"{schema}\n/* Amostra (3 linhas): {sample} */"


def run_select_query(conn: sqlite3.Connection, query: str) -> str:
    """Executa uma query SELECT de forma segura e retorna o resultado em JSON.

    **Defesa em código (ponto destacado no desafio):** não confiamos cegamente
    no SQL gerado pelo LLM. Antes de executar, verificamos se a query contém
    alguma palavra-chave de escrita/destruição e bloqueamos a execução. Assim,
    mesmo que o modelo ignore o prompt de sistema, o banco não é alterado.
    """
    
    query_clean = " ".join(query.strip().split())

    # Impede múltiplos statements
    if ";" in query_clean.rstrip(";"):
        return json.dumps({"erro": "Apenas uma declaração por consulta é permitida."})

    upper = query_clean.upper()
    for keyword in _FORBIDDEN_STATEMENTS:
        # Palavras proibidas como início/parte de statement
        if keyword in upper:
            return json.dumps({"erro": f"Comando '{keyword}' não é permitido por motivos de segurança."})

    try:
        cursor = conn.execute(query_clean)
        
        # Limita o total de linhas retornadas para proteger o contexto.
        rows = cursor.fetchmany(50)
        columns = [d[0] for d in cursor.description]
        payload = [dict(zip(columns, row)) for row in rows]
        
        if not payload:
            return json.dumps({"dados": []}, ensure_ascii=False)
        return json.dumps(payload, ensure_ascii=False, default=str)
    except Exception as exc:
        return json.dumps({"erro": f"Erro ao executar a query: {exc}"})


_DB_CACHE: sqlite3.Connection | None = None

def db_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco"""
    global _DB_CACHE
    if _DB_CACHE is None:
        _DB_CACHE = build_database()
    return _DB_CACHE