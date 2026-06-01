import sqlite3
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "album.sqlite3"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
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
    for selecao in selections:
        name = selecao["name"]
        group = selecao.get("group") or "Sem grupo"
        group_rows.append((group, name))
        for numero in range(1, tamanho + 1):
            rows.append((name, group, numero, 0))
    with get_connection() as conn:
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
        conn.commit()
        return conn.total_changes


def prune_selections(names: List[str]) -> int:
    if not names:
        return 0
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


def fetch_album() -> List[Dict]:
    with get_connection() as conn:
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

    return list(selections_map.values())


def update_quantity(selecao: str, numero: int, delta: int) -> int:
    with get_connection() as conn:
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
        conn.executemany(
            """
            INSERT OR IGNORE INTO album (selecao, grupo, numero_figurinha, quantidade)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return conn.total_changes
