from src.connections import get_main_db_cursor, get_analytic_db_cursor, get_redis_connection
from src.logs import logger


def main() -> None:
    logger.info("Начало ETL процесса.")
    with get_main_db_cursor() as cursor, get_analytic_db_cursor() as analytic_cursor, get_redis_connection() as redis:
        cursor.execute("SELECT 1")
        print(cursor.fetchone())


if __name__ == "__main__":
    main()