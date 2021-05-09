import os
import sqlite3

from spotipy.cache_handler import CacheHandler


def dict_factory(cursor, row):
    """
    SQLite row factory to convert rows into dicts.

    :param cursor: SQLite cursor
    :param row: Table row
    :return: Converted dict
    """

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


def has_user(discord_id):
    """
    Check if a user exists in cache.

    :param discord_id: Discord user id
    :return: True, if user exists
    """

    result = cursor.execute(
        "SELECT COUNT(*) FROM user WHERE discord_id = ?", (discord_id,)
    ).fetchone()
    return result["COUNT(*)"] != 0


class DatabaseCacheHandler(CacheHandler):

    def __init__(self):
        self.current_user = ""

    def get_cached_token(self):
        """
        Return the cached token information of current_user.

        :return: Token information
        """

        return cursor.execute(
            """
                SELECT access_token, token_type, expires_in, refresh_token, scope, expires_at
                FROM user
                WHERE discord_id = ?
            """,
            (self.current_user,)
        ).fetchone()

    def save_token_to_cache(self, token_info):
        """
        Save the provided token information to current_user.

        :param token_info: Token information
        """

        cursor.execute(
            """
                INSERT OR REPLACE INTO user VALUES (
                    :discord_id, :access_token, :token_type, :expires_in,
                    :refresh_token, :scope, :expires_at
                )
            """,
            {"discord_id": self.current_user} | token_info
        )
        connection.commit()
