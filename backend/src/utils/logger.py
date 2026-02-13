"""
Centralized logging configuration with console and file output.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Create a configured logger with console and optional file handlers.

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path for file logging
        level: Override log level (defaults to LOG_LEVEL env)

    Returns:
        Configured logger instance
    """
    # Import here to avoid circular import with config
    from .config import settings

    logger = logging.getLogger(name)
    log_level = getattr(logging, level or settings.log_level)
    logger.setLevel(log_level)

    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
