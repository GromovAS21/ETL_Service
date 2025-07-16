import json
from collections.abc import Generator
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import List

from psycopg import Cursor, OperationalError, sql
from psycopg.sql import Composed
from pydantic import BaseModel, Field, ValidationError
from redis import Redis

from src.config import JOBS_DIR
from src.connections import get_analytic_db_cursor, get_main_db_cursor, get_redis_connection
from src.logs import logger


class JobSchema(BaseModel):
    create_table_query: str  = Field(validation_alias="CREATE_TABLE_SQL")
    select_source_query: str = Field(validation_alias="SELECT_SOURCE_SQL")
    upsert_target_query: str = Field(validation_alias="UPSERT_TARGET_SQL")
    select_keys_query: str = Field(validation_alias="SELECT_KEYS_SQL")
    target_table: str = Field(validation_alias="TARGET_TABLE")
    key_columns: list[str] = Field(validation_alias="KEY_COLUMNS")


def load_jobs() -> list[Path]:
    """Загрузка списка путей к файлам в директории jobs."""
    return [file for file in JOBS_DIR.iterdir() if file.is_file() and file.suffix == ".json"]


def read_job(job_path: Path) -> JobSchema:
    """Получение задания из файла для выполнения."""
    try:
        with open(job_path, encoding="utf-8") as f:
            return JobSchema(**json.load(f))
    except ValidationError:
        logger.error("Ошибка валидации в задании %s", job_path.name)
        raise


def extract_data(main_cursor: Cursor, query: str, hash_date: bytes | None,  batch_size: int = 50) -> Generator[list, None, None]:
    """
    Получение данных из основной базы данных.
    :return: генератор, которые возвращает данные в "чанках"
    """
    date = datetime.min
    if hash_date is not None:
        date = datetime.fromisoformat(hash_date.decode('utf-8'))
    try:
        main_cursor.execute(query, [date])
    except Exception as e:
        logger.exception(e, exc_info=True)
        raise OperationalError from e
    logger.info("Запрос '%s' отправлен успешно", query)
    while result := main_cursor.fetchmany(batch_size):
        yield result


def create_delete_query(key_columns: List[str], values_in_main_db: List[tuple], name_table: str) -> Composed:
    """Создание запроса на удаление записей из таблицы."""

    query = sql.SQL("DELETE FROM {name_table}").format(name_table=sql.Identifier(name_table))
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
    logger.info("Начало обработки задания: %s", job_path.name)
    date_start_job = datetime.now().isoformat()
    job = read_job(job_path)

    try:
        with (get_main_db_cursor() as main_cursor,
              get_analytic_db_cursor() as analytic_cursor,
              get_redis_connection() as redis):

            analytic_cursor.execute(job.create_table_query)
            redis_key = f"{job.target_table}:last_datetime_job"
            hash_date = get_redis_date(redis_key, redis)
            rows = extract_data(main_cursor, job.select_source_query, hash_date)
            data_list = []
            for rows_tuple in rows:
                for row in rows_tuple:
                    data_list.append(row)
            analytic_cursor.executemany(job.upsert_target_query, data_list)
            logger.info("Вставлено/обновлено %d записей в таблицу %s", len(data_list), job.target_table)

            main_cursor.execute(job.select_keys_query)
            values_in_main_db = main_cursor.fetchall()
            delete_query = create_delete_query(job.key_columns, values_in_main_db, job.target_table)
            analytic_cursor.execute(delete_query)
            deleted_count = analytic_cursor.rowcount
            logger.info("Удалено %d записей из таблицы %s", deleted_count, job.target_table)

            analytic_cursor.connection.commit()
            set_redis_date(redis_key, redis, date_start_job)
            logger.info("Задание %s выполнено успешно", job_path.name)
    except Exception:
        logger.exception("Ошибка при выполнении задания %s", job_path.name)
