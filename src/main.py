import time

from src.logs import logger
from src.services import load_jobs, process_job


def main(interval_seconds: int = 300) -> None:
    """Основная функция программы."""
    logger.info("Запуск цикла ETL")
    while True:
        try:
            jobs = load_jobs()
            if not jobs:
                logger.info("Нет заданий для выполнения.")
            else:
                for job in jobs:
                    process_job(job)
            logger.info("Цикл ETL завершен.")
        except Exception:
            logger.exception("Критическая ошибка в ETL-цикле")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
