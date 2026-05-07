from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
import shutil
import sys


@dataclass(frozen=True)
class RuntimeIssue:
    name: str
    message: str
    required_for: str


def check_runtime_dependencies() -> list[RuntimeIssue]:
    issues: list[RuntimeIssue] = []
    if find_soffice() is None:
        issues.append(
            RuntimeIssue(
                name="LibreOffice",
                message="未找到 LibreOffice；Word 转 PDF 暂不可用。",
                required_for="Word 转 PDF",
            )
        )
    if find_spec("paddleocr") is None:
        issues.append(
            RuntimeIssue(
                name="PaddleOCR",
                message="未安装 PaddleOCR；扫描件 PDF 转 Word 的中文 OCR 暂不可用。",
                required_for="扫描件 OCR",
            )
        )
    return issues


def find_bundled_ocr_models() -> dict[str, Path]:
    runtime_root = _runtime_root()
    model_roots = [
        runtime_root / "vendor" / "paddleocr" / "whl",
        runtime_root / "_internal" / "vendor" / "paddleocr" / "whl",
    ]
    for model_root in model_roots:
        models = {
            "det_model_dir": model_root / "det" / "ch" / "ch_PP-OCRv4_det_infer",
            "rec_model_dir": model_root / "rec" / "ch" / "ch_PP-OCRv4_rec_infer",
            "cls_model_dir": model_root / "cls" / "ch_ppocr_mobile_v2.0_cls_infer",
        }
        if all((path / "inference.pdmodel").exists() for path in models.values()):
            return models
    return {}


def find_soffice() -> Path | None:
    path_match = shutil.which("soffice") or shutil.which("soffice.exe")
    runtime_root = _runtime_root()
    candidates = [
        Path(path_match) if path_match else None,
        runtime_root / "vendor" / "LibreOffice" / "program" / "soffice.exe",
        runtime_root / "_internal" / "vendor" / "LibreOffice" / "program" / "soffice.exe",
        Path("C:/Program Files/LibreOffice/program/soffice.exe"),
        Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
    ]
    for candidate in candidates:
        if candidate and candidate.exists() and candidate.is_file():
            return candidate
    return None


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]
