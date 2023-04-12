from .base import Database
from .sqlite import SQLiteDatabase


def create_database(db_url: str) -> Database:
    databases = {
        db_class.url_prefix: db_class
        for db_class in [SQLiteDatabase, ]
    }
    return databases[db_url.split('://')[0]](db_url=db_url)


__all__ = [
    'create_database',
    'Database',
    'SQLiteDatabase',
]
