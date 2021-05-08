import os
import sqlite3

from spotipy.cache_handler import CacheHandler


def dict_factory(cursor, row):
    dict = {}
    for i, col in enumerate(cursor.description):
        dict[col[0]] = row[i]
    return dict


table_query = """
    CREATE TABLE IF NOT EXISTS user (
        discord_id INTEGER PRIMARY KEY,
        access_token TEXT,
        token_type TEXT,
        expires_in INTEGER,
        refresh_token TEXT,
        scope TEXT,
        expires_at INTEGER
    );
"""

connection = sqlite3.connect(os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "cache.db"
))
connection.execute(table_query)
connection.row_factory = dict_factory

cursor = connection.cursor()


class DatabaseCacheHandler(CacheHandler):

    def __init__(self):
        self.current_user = ""

    def get_cached_token(self):
        return cursor.execute(
            """
                SELECT access_token, token_type, expires_in, refresh_token, scope, expires_at
                FROM user
                WHERE discord_id = ?
            """,
            (self.current_user,)
        ).fetchone()

    def save_token_to_cache(self, token_info):
        cursor.execute(
            "INSERT OR REPLACE INTO user VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.current_user, *token_info.values())
        )
        connection.commit()
