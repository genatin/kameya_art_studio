import logging
import sqlite3
from contextlib import closing

from src.config import get_config

logger = logging.getLogger(__name__)
DB_PATH = get_config().DB_PATH


def add_mclass(name: str, image: str, description: str = None):
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mclasses (name, image, description)
                VALUES (?, ?, ?)
            """,
                (name, image, description),
            )
            conn.commit()
            logger.info("File added successfully")
    except sqlite3.IntegrityError:
        logger.error("File path must be unique")


def get_all_mclasses():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM mclasses")
        return cursor.fetchall()


def remove_mclasses_by_name(name: str):
    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mclasses WHERE name = ?", (name,))
            conn.commit()
            logger.info(f"File '{name}' deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
