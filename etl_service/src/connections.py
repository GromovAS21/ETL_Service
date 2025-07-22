from contextlib import closing, contextmanager
from typing import Iterator

import psycopg
from redis import Redis

from src.config import settings


@contextmanager
def get_redis_connection() -> Iterator[Redis]:
    """Получает соединение с Redis."""
    try:
        redis = Redis.from_url(settings.redis.connection_url)
        yield redis
    finally:
        redis.close()


@contextmanager
def get_main_db_cursor() -> Iterator[psycopg.Cursor]:
    """Получает курсор для основной базы данных."""
    with closing(psycopg.connect(settings.main_database.connection_url)) as conn:
        with closing(conn.cursor()) as cursor:
            yield cursor


@contextmanager
def get_analytic_db_cursor() -> Iterator[psycopg.Cursor]:
    """Получает курсор для аналитической базы данных."""
    with closing(psycopg.connect(settings.analytic_database.connection_url)) as conn:
        with closing(conn.cursor()) as cursor:
            yield cursor
