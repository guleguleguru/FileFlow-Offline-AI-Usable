from __future__ import annotations

import json
from pathlib import Path

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
    assert "Input file type does not match" in payload["error"]
