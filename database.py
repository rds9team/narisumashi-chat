import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any

DEFAULT_DB_PATH = os.environ.get("DB_PATH", "settings.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                log_webhook_url TEXT,
                log_enabled INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()


def get_guild_setting(guild_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def set_guild_webhook(guild_id: int, webhook_url: str, db_path: str = DEFAULT_DB_PATH) -> None:
    now = datetime.now().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT guild_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute(
                "UPDATE guild_settings SET log_webhook_url = ?, log_enabled = 1, updated_at = ? WHERE guild_id = ?",
                (webhook_url, now, guild_id),
            )
        else:
            cursor.execute(
                "INSERT INTO guild_settings (guild_id, log_webhook_url, log_enabled, created_at, updated_at) VALUES (?, ?, 1, ?, ?)",
                (guild_id, webhook_url, now, now),
            )
        conn.commit()


def remove_guild_webhook(guild_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    now = datetime.now().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT guild_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE guild_settings SET log_webhook_url = NULL, updated_at = ? WHERE guild_id = ?",
                (now, guild_id),
            )
            conn.commit()
            return True
        return False


def set_guild_log_enabled(guild_id: int, enabled: bool, db_path: str = DEFAULT_DB_PATH) -> None:
    now = datetime.now().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT guild_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        exists = cursor.fetchone()
        val = 1 if enabled else 0
        if exists:
            cursor.execute(
                "UPDATE guild_settings SET log_enabled = ?, updated_at = ? WHERE guild_id = ?",
                (val, now, guild_id),
            )
        else:
            cursor.execute(
                "INSERT INTO guild_settings (guild_id, log_webhook_url, log_enabled, created_at, updated_at) VALUES (?, NULL, ?, ?, ?)",
                (guild_id, val, now, now),
            )
        conn.commit()
