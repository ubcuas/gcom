import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "mission_planner") -> logging.Logger:
    """
    Configure and return a logger with both console and file output.

    Args:
        name: Logger name (defaults to "mission_planner")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Create logs directory
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"mission_planner_{timestamp}.log"

    # Format for log messages
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Print message to console about log file location
    print(f"Mission Planner logs are being written to: {log_file.absolute()}")

    return logger


# Create default logger for the mission planner
logger = setup_logger()
