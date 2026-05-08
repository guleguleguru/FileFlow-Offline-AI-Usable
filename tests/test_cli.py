from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import fitz

from offline_converter.cli import main


def test_cli_converts_pdf_to_word_with_json_output(tmp_path: Path, capsys) -> None:
    source_pdf = tmp_path / "source.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Agent readable text")
    doc.save(source_pdf)
    doc.close()

    exit_code = main(
        [
            "convert",
            "--kind",
            "pdf-to-word",
            "--pdf-word-mode",
            "editable",
            "--input",
            str(source_pdf),
            "--output-dir",
            str(tmp_path / "out"),
            "--no-ocr",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["tasks"][0]["status"] == "完成"
    assert payload["tasks"][0]["page_count"] == 1
    assert Path(payload["tasks"][0]["outputs"][0]).exists()


def test_cli_visual_pdf_to_word_embeds_page_image_without_libreoffice(tmp_path: Path, capsys, monkeypatch) -> None:
    source_pdf = tmp_path / "source.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Visual mode text")
    doc.save(source_pdf)
    doc.close()
    monkeypatch.setattr("offline_converter.converters.find_soffice", lambda: None)

    exit_code = main(
        [
            "convert",
            "--kind",
            "pdf-to-word",
            "--pdf-word-mode",
            "visual",
            "--input",
            str(source_pdf),
            "--output-dir",
            str(tmp_path / "out"),
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    output = Path(payload["tasks"][0]["outputs"][0])
    with ZipFile(output) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    assert len(media) == 1


def test_cli_diagnose_and_export_logs_return_machine_readable_paths(tmp_path: Path, capsys) -> None:
    assert main(["diagnose", "--json"]) == 0
    diagnose = json.loads(capsys.readouterr().out)
    assert diagnose["ok"] is True
    assert "log_path" in diagnose
    assert "dependencies" in diagnose

    output = tmp_path / "logs.zip"
    assert main(["export-logs", "--output", str(output), "--json"]) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["ok"] is True
    assert Path(exported["output"]).exists()


def test_cli_reports_invalid_input_as_json(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "convert",
            "--kind",
            "pdf-to-word",
            "--input",
            str(tmp_path / "missing.pdf"),
            "--output-dir",
            str(tmp_path / "out"),
            "--json",
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_input"


def test_cli_visual_mode_reports_page_count(tmp_path: Path, capsys) -> None:
    source_pdf = tmp_path / "visual.pdf"
    doc = fitz.open()
    page = doc.new_page(width=240, height=120)
    page.insert_text((24, 48), "Form title")
    doc.save(source_pdf)
    doc.close()

    exit_code = main(
        [
            "convert",
            "--kind",
            "pdf-to-word",
            "--pdf-word-mode",
            "visual",
            "--input",
            str(source_pdf),
            "--output-dir",
            str(tmp_path / "out"),
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    output = Path(payload["tasks"][0]["outputs"][0])
    assert output.exists()
    assert payload["tasks"][0]["page_count"] == 1
