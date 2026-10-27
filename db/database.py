"""Подключение к SQLite-базе данных проекта и создание её структуры."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "workout_app.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path=None) -> sqlite3.Connection:
    """Открыть соединение с базой и включить проверку внешних ключей.

    По умолчанию используется файл DB_PATH. SQLite не контролирует внешние
    ключи, пока для соединения не выполнено PRAGMA foreign_keys = ON.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Создать таблицы по sql/schema.sql (безопасно при повторном запуске)."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
