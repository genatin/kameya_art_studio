import sqlite3

from src.config import get_config


def init_db():
    try:
        conn = sqlite3.connect(get_config().DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mclasses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                image TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        print("Database initialized successfully")

    except Exception as e:
        print(f"Error initializing database: {str(e)}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    init_db()
