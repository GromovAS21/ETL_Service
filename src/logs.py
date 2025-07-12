import logging

from src.config import settings

if not settings.log.file.exists():
    settings.log.file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=settings.log.level,
    format=settings.log.log_format,
    handlers=[
        logging.FileHandler(settings.log.file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
