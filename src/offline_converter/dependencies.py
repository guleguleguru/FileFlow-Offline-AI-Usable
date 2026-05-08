from __future__ import annotations

from dataclasses import dataclass
from importlib import invalidate_caches
from importlib.util import find_spec
import os
from pathlib import Path
import shutil
import site
import sys
from typing import Any


_DLL_DIRECTORY_HANDLES: list[Any] = []


@dataclass(frozen=True)
class RuntimeIssue:
    name: str
    message: str
    required_for: str


def check_runtime_dependencies(*, as_payload: bool = False) -> list[RuntimeIssue] | dict[str, Any]:
    issues: list[RuntimeIssue] = []
    soffice = find_soffice()
    ocr_runtime = find_ocr_runtime()
    if soffice is None:
        issues.append(
            RuntimeIssue(
                name="LibreOffice",
                message="未找到 LibreOffice；Word 转 PDF 暂不可用。",
                required_for="Word 转 PDF",
            )
        )
    if ocr_runtime is None:
        issues.append(
            RuntimeIssue(
                name="PaddleOCR",
                message="未安装 PaddleOCR；扫描件 PDF 转 Word 的中文 OCR 暂不可用。",
                required_for="扫描件 OCR",
            )
        )
    if as_payload:
        return {
            "ok": not issues,
            "components": {
                "core": {
                    "available": True,
                    "path": str(_runtime_root()),
                    "install_hint": "Core 已安装。",
                },
                "libreoffice": {
                    "available": soffice is not None,
                    "path": str(soffice) if soffice else "",
                    "install_hint": "请安装 LibreOffice Addon，或安装本机 LibreOffice。",
                },
                "ocr": {
                    "available": ocr_runtime is not None,
                    "path": str(ocr_runtime) if ocr_runtime else "",
                    "install_hint": "请安装 OCR Addon。",
                },
            },
            "issues": [
                {"name": issue.name, "message": issue.message, "required_for": issue.required_for}
                for issue in issues
            ],
        }
    return issues


def find_bundled_ocr_models() -> dict[str, Path]:
    runtime_root = _runtime_root()
    model_roots = [
        runtime_root / "plugins" / "ocr" / "paddleocr" / "whl",
        runtime_root / "_internal" / "plugins" / "ocr" / "paddleocr" / "whl",
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


def find_ocr_runtime() -> Path | None:
    if find_spec("paddleocr") is not None:
        return Path("python-site-packages:paddleocr")
    for candidate in _ocr_python_paths():
        if _contains_python_package(candidate, "paddleocr"):
            return candidate
    return None


def add_ocr_plugin_paths() -> list[Path]:
    paths = [
        path
        for path in _ocr_python_paths()
        if path.exists() and path.is_dir() and str(path) not in sys.path
    ]
    for path in reversed(paths):
        sys.path.insert(0, str(path))
    for path in paths:
        _configure_plugin_user_site(path)
        _add_windows_dll_search_paths(path)
        _prefer_plugin_package("pkg_resources", path)
        _prefer_plugin_package("setuptools", path)
    if paths:
        invalidate_caches()
    return paths


def find_soffice() -> Path | None:
    path_match = shutil.which("soffice") or shutil.which("soffice.exe")
    runtime_root = _runtime_root()
    candidates = [
        Path(path_match) if path_match else None,
        runtime_root / "plugins" / "libreoffice" / "program" / "soffice.exe",
        runtime_root / "_internal" / "plugins" / "libreoffice" / "program" / "soffice.exe",
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


def _ocr_python_paths() -> list[Path]:
    runtime_root = _runtime_root()
    return [
        runtime_root / "plugins" / "ocr" / "python",
        runtime_root / "plugins" / "ocr" / "python" / "site-packages",
        runtime_root / "_internal" / "plugins" / "ocr" / "python",
        runtime_root / "_internal" / "plugins" / "ocr" / "python" / "site-packages",
    ]


def _contains_python_package(root: Path, package_name: str) -> bool:
    return (root / package_name).exists() or (root / f"{package_name}.py").exists()


def _add_windows_dll_search_paths(root: Path) -> None:
    if sys.platform != "win32":
        return
    dll_dirs = {root}
    dll_dirs.update(path.parent for path in root.rglob("*.dll"))
    for directory in sorted(dll_dirs):
        directory_text = str(directory)
        path_parts = os.environ.get("PATH", "").split(os.pathsep)
        if directory_text not in path_parts:
            os.environ["PATH"] = directory_text + os.pathsep + os.environ.get("PATH", "")
        add_dll_directory = getattr(os, "add_dll_directory", None)
        if add_dll_directory is not None:
            try:
                _DLL_DIRECTORY_HANDLES.append(add_dll_directory(directory_text))
            except OSError:
                continue


def _configure_plugin_user_site(plugin_root: Path) -> None:
    if site.USER_SITE is None:
        site.USER_SITE = str(plugin_root)
    if getattr(site, "ENABLE_USER_SITE", None) is None:
        site.ENABLE_USER_SITE = True


def _prefer_plugin_package(package_name: str, plugin_root: Path) -> None:
    external_path = plugin_root / package_name
    if not external_path.exists():
        return
    external_text = str(external_path)
    module = sys.modules.get(package_name)
    module_file = str(getattr(module, "__file__", "")) if module else ""
    if module is not None and module_file and module_file.startswith(str(plugin_root)):
        return
    for loaded_name in [name for name in sys.modules if name == package_name or name.startswith(f"{package_name}.")]:
        del sys.modules[loaded_name]
