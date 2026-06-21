"""
Structured logging configuration.
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        return json.dumps(log_data)

class HumanReadableFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"{color}[{timestamp}] {record.levelname:8s}{reset} {record.name}: {record.getMessage()}"

def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    json_output: bool = False,
    human_readable: bool = True,
):
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    if human_readable:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(HumanReadableFormatter())
        root_logger.addHandler(console_handler)
    
    if json_output:
        json_handler = logging.StreamHandler(sys.stdout)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "telegram-board.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    
    return root_logger
