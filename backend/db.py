import json
import os
from pathlib import Path
from typing import Dict, List

DB_URL = os.getenv("DATABASE_URL") or os.getenv("ALBUM_DB_URL")
USE_POSTGRES = bool(DB_URL and DB_URL.startswith("postgres"))

if USE_POSTGRES:
    import psycopg
    from psycopg.rows import dict_row
else:
    import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("ALBUM_DB_PATH", BASE_DIR / "album.sqlite3"))
SELECTIONS_PATH = BASE_DIR / "data" / "selections.json"


def get_connection():
    if USE_POSTGRES:
        return psycopg.connect(DB_URL, row_factory=dict_row)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS album (
                        id SERIAL PRIMARY KEY,
                        selecao TEXT NOT NULL,
                        grupo TEXT NOT NULL DEFAULT 'Sem grupo',
                        numero_figurinha INTEGER NOT NULL,
                        quantidade INTEGER DEFAULT 0,
                        UNIQUE (selecao, numero_figurinha)
                    )
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE album
                    ADD COLUMN IF NOT EXISTS grupo TEXT NOT NULL DEFAULT 'Sem grupo'
                    """
                )
            conn.commit()
            return

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS album (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selecao TEXT NOT NULL,
                grupo TEXT NOT NULL DEFAULT 'Sem grupo',
                numero_figurinha INTEGER NOT NULL,
                quantidade INTEGER DEFAULT 0,
                UNIQUE (selecao, numero_figurinha)
            )
            """
        )
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(album)").fetchall()
        }
        if "grupo" not in columns:
            conn.execute(
                "ALTER TABLE album ADD COLUMN grupo TEXT NOT NULL DEFAULT 'Sem grupo'"
            )
        conn.commit()


def seed_db(selections: List[Dict], tamanho: int = 20) -> int:
    if not selections:
        return 0
    rows = []
    group_rows = []
    range_rows = []
    for selecao in selections:
        name = selecao["name"]
        group = selecao.get("group") or "Sem grupo"
        start = int(selecao.get("start") or 1)
        end = selecao.get("end")
        if end is None:
            size = int(selecao.get("size") or tamanho)
            end = start + size - 1
        else:
            end = int(end)
        group_rows.append((group, name))
        range_rows.append((name, start, end))
        for numero in range(start, end + 1):
            rows.append((name, group, numero, 0))

    with get_connection() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO album (selecao, grupo, numero_figurinha, quantidade)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (selecao, numero_figurinha) DO NOTHING
                    """,
                    rows,
                )
                insert_count = cur.rowcount
                cur.executemany(
                    """
                    UPDATE album
                    SET grupo = %s
                    WHERE selecao = %s
                    """,
                    group_rows,
                )
                update_count = cur.rowcount
                cur.executemany(
                    """
                    DELETE FROM album
                    WHERE selecao = %s AND (numero_figurinha < %s OR numero_figurinha > %s)
                    """,
                    range_rows,
                )
                delete_count = cur.rowcount
            conn.commit()
            return insert_count + update_count + delete_count

        conn.executemany(
            """
            INSERT OR IGNORE INTO album (selecao, grupo, numero_figurinha, quantidade)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        conn.executemany(
            """
            UPDATE album
            SET grupo = ?
            WHERE selecao = ?
            """,
            group_rows,
        )
        conn.executemany(
            """
            DELETE FROM album
            WHERE selecao = ? AND (numero_figurinha < ? OR numero_figurinha > ?)
            """,
            range_rows,
        )
        conn.commit()
        return conn.total_changes


def prune_selections(names: List[str]) -> int:
    if not names:
        return 0
    if USE_POSTGRES:
        placeholders = ",".join(["%s"] * len(names))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM album
                    WHERE selecao NOT IN ({placeholders})
                    """,
                    names,
                )
                count = cur.rowcount
            conn.commit()
            return count

    placeholders = ",".join(["?"] * len(names))
    with get_connection() as conn:
        conn.execute(
            f"""
            DELETE FROM album
            WHERE selecao NOT IN ({placeholders})
            """,
            names,
        )
        conn.commit()
        return conn.total_changes


def load_selection_order() -> List[str]:
    if not SELECTIONS_PATH.exists():
        return []
    with SELECTIONS_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        return []
    order = []
    for item in data:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
        elif isinstance(item, str):
            name = item.strip()
        else:
            name = ""
        if name:
            order.append(name)
    return order


def has_data() -> bool:
    with get_connection() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM album LIMIT 1")
                return cur.fetchone() is not None

        row = conn.execute("SELECT 1 FROM album LIMIT 1").fetchone()
        return row is not None


def fetch_album() -> List[Dict]:
    with get_connection() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT selecao, grupo, numero_figurinha, quantidade
                    FROM album
                    ORDER BY selecao, numero_figurinha
                    """
                )
                rows = cur.fetchall()
        else:
            rows = conn.execute(
                """
                SELECT selecao, grupo, numero_figurinha, quantidade
                FROM album
                ORDER BY selecao, numero_figurinha
                """
            ).fetchall()

    selections_map: Dict[str, Dict] = {}
    for row in rows:
        item = selections_map.setdefault(
            row["selecao"],
            {"name": row["selecao"], "group": row["grupo"], "stickers": []},
        )
        item["stickers"].append(
            {"number": row["numero_figurinha"], "quantity": row["quantidade"]}
        )

    order = load_selection_order()
    order_index = {name: idx for idx, name in enumerate(order)}
    ordered = [selections_map[name] for name in order if name in selections_map]
    extras = [
        item
        for name, item in selections_map.items()
        if name not in order_index
    ]
    extras.sort(key=lambda item: item["name"])

    return ordered + extras


def update_quantity(selecao: str, numero: int, delta: int) -> int:
    with get_connection() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT quantidade FROM album
                    WHERE selecao = %s AND numero_figurinha = %s
                    """,
                    (selecao, numero),
                )
                row = cur.fetchone()

                if row is None:
                    raise ValueError("Sticker not found")

                new_quantity = max(0, row["quantidade"] + delta)
                cur.execute(
                    """
                    UPDATE album
                    SET quantidade = %s
                    WHERE selecao = %s AND numero_figurinha = %s
                    """,
                    (new_quantity, selecao, numero),
                )
            conn.commit()
            return new_quantity

        row = conn.execute(
            """
            SELECT quantidade FROM album
            WHERE selecao = ? AND numero_figurinha = ?
            """,
            (selecao, numero),
        ).fetchone()

        if row is None:
            raise ValueError("Sticker not found")

        new_quantity = max(0, row["quantidade"] + delta)
        conn.execute(
            """
            UPDATE album
            SET quantidade = ?
            WHERE selecao = ? AND numero_figurinha = ?
            """,
            (new_quantity, selecao, numero),
        )
        conn.commit()
        return new_quantity


def create_selection(name: str, group: str, tamanho: int = 20) -> int:
    rows = [(name, group, numero, 0) for numero in range(1, tamanho + 1)]
    with get_connection() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO album (selecao, grupo, numero_figurinha, quantidade)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (selecao, numero_figurinha) DO NOTHING
                    """,
                    rows,
                )
                count = cur.rowcount
            conn.commit()
            return count

        conn.executemany(
            """
            INSERT OR IGNORE INTO album (selecao, grupo, numero_figurinha, quantidade)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return conn.total_changes
