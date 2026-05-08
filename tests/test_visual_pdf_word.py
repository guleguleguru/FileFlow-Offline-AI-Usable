from __future__ import annotations

from pathlib import Path
import subprocess
from zipfile import ZipFile

import fitz
import pytest
from docx import Document
from PIL import Image, ImageOps

from offline_converter import converters
from offline_converter.converters import pdf_to_word


def test_visual_pdf_to_word_embeds_page_image_without_libreoffice(tmp_path: Path, monkeypatch) -> None:
    source_pdf = tmp_path / "form.pdf"
    doc = fitz.open()
    page = doc.new_page(width=240, height=120)
    page.insert_text((24, 48), "Form field")
    doc.save(source_pdf)
    doc.close()
    monkeypatch.setattr("offline_converter.converters.find_soffice", lambda: None)

    result = pdf_to_word(source_pdf, tmp_path / "out.docx", mode="visual")

    assert result.page_count == 1
    assert result.output_path.exists()
    parsed = Document(result.output_path)
    assert parsed.paragraphs
    with ZipFile(result.output_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    assert len(media) == 1


def test_visual_pdf_to_word_embeds_one_image_per_page(tmp_path: Path, monkeypatch) -> None:
    source_pdf = tmp_path / "form.pdf"
    doc = fitz.open()
    page1 = doc.new_page(width=240, height=120)
    page1.insert_text((24, 48), "Form field")
    page2 = doc.new_page(width=240, height=120)
    page2.insert_text((24, 48), "Second page")
    doc.save(source_pdf)
    doc.close()
    monkeypatch.setattr("offline_converter.converters.find_soffice", lambda: None)

    result = pdf_to_word(source_pdf, tmp_path / "out.docx", mode="visual")

    assert result.page_count == 2
    with ZipFile(result.output_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    assert len(media) == 2


def test_visual_pdf_to_word_roundtrips_to_nonblank_pdf_when_libreoffice_available(tmp_path: Path) -> None:
    soffice = converters.find_soffice()
    if soffice is None:
        pytest.skip("LibreOffice is not installed")

    source_pdf = tmp_path / "form.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.draw_rect(fitz.Rect(72, 96, 540, 260), color=(0, 0, 0), width=2)
    page.insert_text((96, 150), "Visual page must not be blank", fontsize=24)
    doc.save(source_pdf)
    doc.close()

    result = pdf_to_word(source_pdf, tmp_path / "out.docx", mode="visual")
    output_dir = tmp_path / "roundtrip"
    output_dir.mkdir()
    profile_dir = tmp_path / "lo-profile"
    profile_dir.mkdir()

    completed = subprocess.run(
        [
            str(soffice),
            f"-env:UserInstallation={profile_dir.as_uri()}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(result.output_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    roundtrip_pdf = output_dir / "out.pdf"
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert roundtrip_pdf.exists()

    with fitz.open(roundtrip_pdf) as roundtrip:
        pixmap = roundtrip[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
        page_png = tmp_path / "roundtrip.png"
        pixmap.save(page_png)
    with Image.open(page_png) as image:
        darkest, _ = ImageOps.grayscale(image).getextrema()
    assert darkest < 250
