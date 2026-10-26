"""Structured logging setup using Loguru."""

import sys

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Configure Loguru to write nicely formatted logs to stdout."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
