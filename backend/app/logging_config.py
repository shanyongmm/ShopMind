import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    log_dir = backend_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    try:
        file_handler = RotatingFileHandler(
            log_dir / settings.log_file,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError as exc:
        root_logger.warning("file logging disabled: %s", exc)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def backend_dir() -> Path:
    return Path(__file__).resolve().parents[1]
