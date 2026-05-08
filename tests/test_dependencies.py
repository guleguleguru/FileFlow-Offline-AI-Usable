from __future__ import annotations

from pathlib import Path
import types

from offline_converter import dependencies


def test_find_soffice_detects_bundled_vendor_runtime(monkeypatch, tmp_path: Path) -> None:
    soffice = tmp_path / "vendor" / "LibreOffice" / "program" / "soffice.exe"
    soffice.parent.mkdir(parents=True)
    soffice.write_bytes(b"")

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies.shutil, "which", lambda _: None)

    assert dependencies.find_soffice() == soffice


def test_find_bundled_ocr_models_detects_vendor_models(monkeypatch, tmp_path: Path) -> None:
    model_root = tmp_path / "vendor" / "paddleocr" / "whl"
    for relative in [
        "det/ch/ch_PP-OCRv4_det_infer",
        "rec/ch/ch_PP-OCRv4_rec_infer",
        "cls/ch_ppocr_mobile_v2.0_cls_infer",
    ]:
        model_dir = model_root / relative
        model_dir.mkdir(parents=True)
        (model_dir / "inference.pdmodel").write_bytes(b"model")

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)

    assert dependencies.find_bundled_ocr_models() == {
        "det_model_dir": model_root / "det" / "ch" / "ch_PP-OCRv4_det_infer",
        "rec_model_dir": model_root / "rec" / "ch" / "ch_PP-OCRv4_rec_infer",
        "cls_model_dir": model_root / "cls" / "ch_ppocr_mobile_v2.0_cls_infer",
    }


def test_find_soffice_prefers_plugin_runtime(monkeypatch, tmp_path: Path) -> None:
    plugin_soffice = tmp_path / "plugins" / "libreoffice" / "program" / "soffice.exe"
    plugin_soffice.parent.mkdir(parents=True)
    plugin_soffice.write_bytes(b"")
    vendor_soffice = tmp_path / "vendor" / "LibreOffice" / "program" / "soffice.exe"
    vendor_soffice.parent.mkdir(parents=True)
    vendor_soffice.write_bytes(b"")

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies.shutil, "which", lambda _: None)

    assert dependencies.find_soffice() == plugin_soffice


def test_check_runtime_dependencies_payload_has_component_states(monkeypatch) -> None:
    monkeypatch.setattr(dependencies, "find_soffice", lambda: None)
    monkeypatch.setattr(dependencies, "find_ocr_runtime", lambda: None)

    payload = dependencies.check_runtime_dependencies(as_payload=True)

    assert payload["ok"] is False
    assert payload["components"]["core"]["available"] is True
    assert payload["components"]["libreoffice"]["available"] is False
    assert "LibreOffice Addon" in payload["components"]["libreoffice"]["install_hint"]
    assert payload["components"]["ocr"]["available"] is False


def test_find_ocr_runtime_does_not_treat_models_only_as_runtime(monkeypatch, tmp_path: Path) -> None:
    model_root = tmp_path / "plugins" / "ocr" / "paddleocr" / "whl"
    model_root.mkdir(parents=True)

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies, "find_spec", lambda _: None)

    assert dependencies.find_ocr_runtime() is None


def test_find_ocr_runtime_detects_plugin_python_package(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "plugins" / "ocr" / "python"
    (package_root / "paddleocr").mkdir(parents=True)

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies, "find_spec", lambda _: None)

    assert dependencies.find_ocr_runtime() == package_root


def test_add_ocr_plugin_paths_prepends_importable_plugin_paths(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "plugins" / "ocr" / "python"
    (package_root / "paddleocr").mkdir(parents=True)
    original_path = ["existing"]

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies.sys, "path", original_path.copy())

    added = dependencies.add_ocr_plugin_paths()

    assert added == [package_root]
    assert dependencies.sys.path[:2] == [str(package_root), "existing"]


def test_add_ocr_plugin_paths_unloads_core_setuptools_for_plugin_runtime(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "plugins" / "ocr" / "python"
    (package_root / "paddleocr").mkdir(parents=True)
    (package_root / "setuptools").mkdir(parents=True)
    (package_root / "pkg_resources").mkdir(parents=True)
    fake_setuptools = types.ModuleType("setuptools")
    fake_setuptools.__file__ = "core/_internal/setuptools/__init__.py"
    fake_submodule = types.ModuleType("setuptools.command")
    fake_pkg_resources = types.ModuleType("pkg_resources")
    fake_pkg_resources.__file__ = "core/_internal/pkg_resources/__init__.py"

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies.sys, "path", [])
    monkeypatch.setitem(dependencies.sys.modules, "setuptools", fake_setuptools)
    monkeypatch.setitem(dependencies.sys.modules, "setuptools.command", fake_submodule)
    monkeypatch.setitem(dependencies.sys.modules, "pkg_resources", fake_pkg_resources)

    dependencies.add_ocr_plugin_paths()

    assert "setuptools" not in dependencies.sys.modules
    assert "setuptools.command" not in dependencies.sys.modules
    assert "pkg_resources" not in dependencies.sys.modules


def test_add_ocr_plugin_paths_configures_user_site_for_frozen_paddle(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "plugins" / "ocr" / "python"
    (package_root / "paddleocr").mkdir(parents=True)

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies.sys, "path", [])
    monkeypatch.setattr(dependencies.site, "USER_SITE", None)
    monkeypatch.setattr(dependencies.site, "ENABLE_USER_SITE", None)

    dependencies.add_ocr_plugin_paths()

    assert dependencies.site.USER_SITE == str(package_root)
    assert dependencies.site.ENABLE_USER_SITE is True
