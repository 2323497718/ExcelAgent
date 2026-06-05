"""
Logger module for creating consistent logging across the application.
"""

import os
import logging
from datetime import datetime
from pathlib import Path


def get_logger(
    save_dir: str = "./output/logs",
    task_name: str = "agent",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Create and configure a logger instance.

    Args:
        save_dir: Directory to save log files
        task_name: Name for the task (used in log filename)
        level: Logging level (default: INFO)

    Returns:
        logging.Logger: Configured logger instance
    """
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{task_name}_{timestamp}.log"
    log_filepath = os.path.join(save_dir, log_filename)

    logger = logging.getLogger(task_name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialized. Log file: {log_filepath}")

    return logger
