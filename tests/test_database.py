import json
from src import database


def test_tabelas_criadas(conn):
    tabelas = database.list_tables(conn)
    assert {"customers", "categories", "products", "orders",
            "order_items", "promotions"} <= set(tabelas)


def test_consulta_violoes_ate_600(conn):
    res = json.loads(database.run_select_query(
        conn,
        "SELECT name, price_brl FROM products WHERE category_id=5 AND price_brl<=600",
    ))
    assert res
    assert all(r["price_brl"] <= 600 for r in res)


def test_bloqueia_delete(conn):
    res = json.loads(database.run_select_query(conn, "DELETE FROM products WHERE product_id=1"))
    assert "erro" in res


def test_bloqueia_multiplos_statements(conn):
    res = json.loads(database.run_select_query(conn, "SELECT 1; DROP TABLE products"))
    assert "erro" in res
    # garante que a tabela continua existindo
    assert "products" in database.list_tables(conn)


def test_bloqueia_drop_embutido(conn):
    res = json.loads(database.run_select_query(conn, "SELECT * FROM products WHERE 1=1 DROP"))
    assert "erro" in res


def test_schema_retorna_ddl(conn):
    schema = database.table_schema(conn, "products")
    assert "CREATE TABLE" in schema
