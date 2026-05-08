from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path
import zipfile


LOGGER_NAME = "fileflow"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "FileFlowOffline"
    return Path.home() / "AppData" / "Local" / "FileFlowOffline"


def log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_path() -> Path:
    return log_dir() / "fileflow.log"


def configure_logging() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        handler = logging.FileHandler(log_path(), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def export_logs(output_path: Path) -> Path:
    configure_logging()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() != ".zip":
        output = output.with_suffix(".zip")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        current_log = log_path()
        if current_log.exists():
            archive.write(current_log, "fileflow.log")
        archive.writestr("diagnostic.txt", f"exported_at={datetime.now().isoformat(timespec='seconds')}\n")
    return output
