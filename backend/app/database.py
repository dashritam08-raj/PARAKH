"""
PARAKH - SQLite database layer

Step 2: persistent inspection + authentication database.

Uses Python's built-in sqlite3 module, so no new database package is required.

Tables:
    - inspections
    - users
    - sessions
"""

from pathlib import Path

import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATA_DIR / "parakh.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with safe defaults for the PARAKH backend.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    # Foreign-key enforcement.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    # WAL improves concurrent read/write behavior
    # for this local application.
    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    return connection


def init_database() -> None:
    """
    Create the PARAKH database schema if it does not already exist.

    Safe to call every time the backend starts.
    """

    connection = get_connection()

    try:

        connection.executescript(
            """
            -- ========================================================
            -- INSPECTIONS
            -- ========================================================

            CREATE TABLE IF NOT EXISTS inspections (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                inspection_id TEXT NOT NULL UNIQUE,

                filename TEXT,

                status TEXT,

                overall_status TEXT,

                compliance_score REAL,

                product_name TEXT,

                brand TEXT,

                inspector_decision TEXT,

                inspector_name TEXT,

                inspector_remarks TEXT,

                decision_timestamp TEXT,

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL,

                analysis_json TEXT NOT NULL
            );


            CREATE INDEX IF NOT EXISTS idx_inspections_created_at
                ON inspections(created_at);


            CREATE INDEX IF NOT EXISTS idx_inspections_overall_status
                ON inspections(overall_status);


            CREATE INDEX IF NOT EXISTS idx_inspections_product_name
                ON inspections(product_name);


            CREATE INDEX IF NOT EXISTS idx_inspections_inspector_decision
                ON inspections(inspector_decision);


            -- ========================================================
            -- USERS
            -- ========================================================

            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                email TEXT NOT NULL UNIQUE,

                password_hash TEXT NOT NULL,

                role TEXT NOT NULL DEFAULT 'INSPECTOR',

                is_active INTEGER NOT NULL DEFAULT 1,

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL
            );


            CREATE INDEX IF NOT EXISTS idx_users_email
                ON users(email);


            CREATE INDEX IF NOT EXISTS idx_users_role
                ON users(role);


            -- ========================================================
            -- SESSIONS
            -- ========================================================

            CREATE TABLE IF NOT EXISTS sessions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                session_token_hash TEXT NOT NULL UNIQUE,

                expires_at TEXT NOT NULL,

                created_at TEXT NOT NULL,

                last_used_at TEXT,

                revoked_at TEXT,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );


            CREATE INDEX IF NOT EXISTS idx_sessions_user_id
                ON sessions(user_id);


            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
                ON sessions(expires_at);


            CREATE INDEX IF NOT EXISTS idx_sessions_token_hash
                ON sessions(session_token_hash);


            CREATE INDEX IF NOT EXISTS idx_sessions_revoked_at
                ON sessions(revoked_at);
            """
        )

        connection.commit()

    finally:

        connection.close()


if __name__ == "__main__":

    init_database()

    print(
        f"PARAKH SQLite database ready: {DATABASE_PATH}"
    )
