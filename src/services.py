import json
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import Iterator, List

from psycopg import Cursor, OperationalError, sql
from psycopg.sql import Composed
from redis import Redis

from src.config import JOBS_DIR
from src.connections import get_analytic_db_cursor, get_main_db_cursor, get_redis_connection
from src.logs import logger


def load_jobs() -> list[Path]:
    """Загрузка списка путей к файлам в директории jobs."""
    return [file for file in JOBS_DIR.iterdir() if file.is_file() and file.suffix == ".json"]


def read_job(job_path: Path) -> dict[str, str | list]:
    """Получение задания из файла для выполнения."""
    with open(job_path, encoding="utf-8") as f:
        return json.load(f)


def extract_data(main_cursor: Cursor, query: str, hash_date: datetime | None,  batch_size: int = 50) -> Iterator[str]:
    """
    Получение данных из основной базы данных.
    :return: генератор, которые возвращает данные в "чанках"
    """
    date = datetime.min
    if hash_date:
        date = datetime.fromisoformat(hash_date.decode('utf-8'))
    try:
        main_cursor.execute(query, [date])
    except Exception as e:
        logger.exception(e, exc_info=True)
        raise OperationalError
    logger.info(f'Запрос "{query}" отправлен успешно')
    while result := main_cursor.fetchmany(batch_size):
        yield result


def create_delete_query(key_columns: List[str], values_in_main_db: List[tuple], name_table: str) -> Composed:
    """Создание запроса на удаление записей из таблицы."""

    query = sql.SQL("DELETE FROM {name_table}").format(
        name_table=sql.Identifier(name_table)
    )
    if values_in_main_db:
        if len(key_columns) > 1:
            values = [
                sql.SQL("({})").format(
                    sql.SQL(', ').join([sql.Literal(val) for val in row])
                )
                for row in values_in_main_db
            ]
            name_columns = [sql.Identifier(name) for name in key_columns]
            query = sql.SQL("DELETE FROM {name_table} WHERE ({name_columns}) NOT IN ({values})").format(
                name_table=sql.Identifier(name_table),
                name_columns=sql.SQL(', ').join(name_columns),
                values=sql.SQL(', ').join(values),
            )
        elif len(key_columns) == 1:
            rows_value = list(chain.from_iterable(values_in_main_db))
            values = [sql.Literal(val) for val in rows_value]
            name_column = key_columns[0]
            query = sql.SQL("DELETE FROM {name_table} WHERE {name_column} NOT IN ({values})").format(
                name_table=sql.Identifier(name_table),
                name_column=sql.Identifier(name_column),
                values=sql.SQL(', ').join(values),
            )
    return query


def get_redis_date(redis_key: str, redis: Redis) -> bytes | None:
    """Получение из Redis даты последнего обновления данных в таблице."""
    return redis.hget(redis_key, "timestamp")


def set_redis_date(redis_key: str, redis: Redis, date_start_job: str) -> None:
    """Запись в Redis даты последнего обновления данных в таблице."""
    date = date_start_job
    redis.hset(redis_key, "timestamp", date)


def process_job(job_path: Path) -> None:
    """Обработка задания."""
    logger.info(f"Начало обработки задания: {job_path.name}")
    date_start_job = datetime.now().isoformat()
    job = read_job(job_path)

    create_table_query: str = job["CREATE_TABLE_SQL"]
    select_source_query: str = job["SELECT_SOURCE_SQL"]
    upsert_target_query: str = job["UPSERT_TARGET_SQL"]
    select_keys_query: str = job["SELECT_KEYS_SQL"]
    target_table: str = job["TARGET_TABLE"]
    key_columns: List[str] = job["KEY_COLUMNS"]
    try:
        with (get_main_db_cursor() as main_cursor,
              get_analytic_db_cursor() as analytic_cursor,
              get_redis_connection() as redis):

            analytic_cursor.execute(create_table_query)
            redis_key = f"{target_table}:last_datetime_job"
            hash_date = get_redis_date(redis_key, redis)
            rows = extract_data(main_cursor, select_source_query, hash_date)
            data_list = []
            for rows_tuple in rows:
                for row in rows_tuple:
                    data_list.append(row)
            analytic_cursor.executemany(upsert_target_query, data_list)
            logger.info(f"Вставлено/обновлено {len(data_list)} записей в таблицу {target_table}")

            main_cursor.execute(select_keys_query)
            values_in_main_db = main_cursor.fetchall()
            delete_query = create_delete_query(key_columns, values_in_main_db, target_table)
            analytic_cursor.execute(delete_query)
            deleted_count = analytic_cursor.rowcount
            logger.info(f"Удалено {deleted_count} записей из таблицы {target_table}")

            analytic_cursor.connection.commit()
            set_redis_date(redis_key, redis, date_start_job)
            logger.info(f"Задание {job_path.name} выполнено успешно")
    except Exception as e:
        logger.error(f"Ошибка при выполнении задания {job_path.name}: {e}")
