import time

from src.services import load_jobs, process_job
from src.logs import logger


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
        except Exception as e:
            logger.critical(f"Критическая ошибка в ETL-цикле: {e}", exc_info=True)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
