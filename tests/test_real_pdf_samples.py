from __future__ import annotations

import os
from pathlib import Path

import fitz
import pytest

from offline_converter.converters import pdf_to_images, pdf_to_word
from offline_converter.dependencies import find_soffice


def _real_pdf_samples() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    candidates: list[Path] = []
    sample_dir = os.environ.get("FILEFLOW_REAL_SAMPLE_DIR")
    if sample_dir:
        candidates.extend(Path(sample_dir).glob("*.pdf"))
    local_attachment = root / "附件材料.pdf"
    if local_attachment.exists():
        candidates.append(local_attachment)
    return sorted({path.resolve() for path in candidates if path.is_file()})


def test_real_pdf_samples_render_first_page(tmp_path: Path) -> None:
    samples = _real_pdf_samples()
    if not samples:
        pytest.skip("Set FILEFLOW_REAL_SAMPLE_DIR or place a local PDF sample to run real PDF smoke tests.")

    for sample in samples:
        with fitz.open(sample) as document:
            assert document.page_count > 0
        result = pdf_to_images(sample, tmp_path / sample.stem / "pages", pages=[1], dpi=100)
        assert result.page_count == 1
        assert result.outputs[0].exists()
        assert result.outputs[0].stat().st_size > 0


def test_real_pdf_samples_visual_word_smoke_when_libreoffice_available(tmp_path: Path) -> None:
    samples = _real_pdf_samples()
    if not samples:
        pytest.skip("Set FILEFLOW_REAL_SAMPLE_DIR or place a local PDF sample to run real PDF smoke tests.")
    if find_soffice() is None:
        pytest.skip("LibreOffice is not available for visual PDF to Word real-sample smoke tests.")

    for sample in samples:
        with fitz.open(sample) as document:
            expected_pages = document.page_count
        result = pdf_to_word(sample, tmp_path / sample.stem / f"{sample.stem}.docx", mode="visual")
        assert result.page_count == expected_pages
        assert result.output_path.exists()
        assert result.output_path.stat().st_size > 0
