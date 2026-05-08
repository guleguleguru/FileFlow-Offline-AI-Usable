from __future__ import annotations

from pathlib import Path
import tomllib


def test_installer_scripts_and_release_notes_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "packaging" / "inno" / "FileFlowOffline-Core.iss").exists()
    assert (root / "packaging" / "inno" / "FileFlowOffline-OCR-Addon.iss").exists()
    assert (root / "packaging" / "inno" / "FileFlowOffline-LibreOffice-Addon.iss").exists()
    assert (root / "packaging" / "offline-converter-core.spec").exists()
    assert (root / "docs" / "RELEASE_v0.2.0.md").exists()
    assert (root / "docs" / "RELEASE_CHECKLIST.md").exists()


def test_ocr_addon_installer_declares_python_runtime_payload() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "packaging" / "inno" / "FileFlowOffline-OCR-Addon.iss").read_text(encoding="utf-8")

    assert r"AddonDir" in script
    assert r"{#AddonDir}\python\*" in script
    assert r"{app}\plugins\ocr\python" in script


def test_ocr_dependency_versions_match_addon_requirements() -> None:
    root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    optional_ocr = set(pyproject["project"]["optional-dependencies"]["ocr"])
    addon_requirements = {
        line.strip()
        for line in (root / "requirements-ocr.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    assert "paddlepaddle==2.6.2" in optional_ocr
    assert optional_ocr <= addon_requirements


def test_release_notes_state_installation_limits_and_license_boundaries() -> None:
    root = Path(__file__).resolve().parents[1]
    release_notes = (root / "docs" / "RELEASE_v0.2.0.md").read_text(encoding="utf-8")

    assert "Core" in release_notes
    assert "OCR Addon" in release_notes
    assert "LibreOffice Addon" in release_notes
    assert "不承诺" in release_notes
    assert "第三方许可证" in release_notes
