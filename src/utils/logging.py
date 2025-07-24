# src/utils/logging.py
import logging
import sys


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configures and returns a logger for the application.

    This function sets up a logger that can be controlled by a log level string
    (e.g., "INFO", "DEBUG"). It ensures that all parts of the application
    use a consistent logging format and destination.

    Args:
        log_level (str): The desired logging level. Defaults to "INFO".

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Get the root logger for the application.
    # Naming it ensures we can get the same instance from anywhere in the app.
    logger = logging.getLogger("GeoPhotoToolkitLogger")
    logger.setLevel(log_level.upper())

    # Avoid adding duplicate handlers if the function is called multiple times.
    if not logger.handlers:
        # Create a handler to stream logs to the console (standard output).
        handler = logging.StreamHandler(sys.stdout)

        # Define the format for the log messages.
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add the configured handler to the logger.
        logger.addHandler(handler)

    return logger
