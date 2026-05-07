from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Protocol, Sequence

import fitz
from docx import Document
from PIL import Image, ImageOps

from offline_converter.dependencies import find_bundled_ocr_models, find_soffice


class ConversionError(RuntimeError):
    """Raised when a conversion fails."""


class MissingDependencyError(ConversionError):
    """Raised when an optional conversion engine is unavailable."""


class OcrEngine(Protocol):
    def recognize(self, image_path: Path) -> list[str]:
        ...


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    page_count: int = 0
    outputs: tuple[Path, ...] = ()


def image_to_pdf(
    image_paths: Sequence[Path | str],
    output_path: Path | str,
    *,
    quality: int = 90,
    auto_rotate: bool = True,
) -> ConversionResult:
    paths = [_require_file(path) for path in image_paths]
    if not paths:
        raise ConversionError("At least one image is required.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    images: list[Image.Image] = []
    try:
        for path in paths:
            image = Image.open(path)
            if auto_rotate:
                image = ImageOps.exif_transpose(image)
            images.append(_to_pdf_image(image))

        first, rest = images[0], images[1:]
        first.save(
            output,
            "PDF",
            save_all=True,
            append_images=rest,
            quality=max(1, min(100, quality)),
            resolution=100.0,
        )
    finally:
        for image in images:
            image.close()

    return ConversionResult(output_path=output, page_count=len(paths), outputs=(output,))


def pdf_to_images(
    pdf_path: Path | str,
    output_dir: Path | str,
    *,
    image_format: str = "png",
    dpi: int = 150,
    pages: Sequence[int] | None = None,
) -> ConversionResult:
    pdf = _require_file(pdf_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    suffix = image_format.lower().lstrip(".")
    if suffix not in {"png", "jpg", "jpeg"}:
        raise ConversionError("Image format must be png, jpg, or jpeg.")

    exported: list[Path] = []
    with fitz.open(pdf) as document:
        page_numbers = _normalize_pages(pages, document.page_count)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        for page_number in page_numbers:
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            extension = "jpg" if suffix == "jpeg" else suffix
            output = destination / f"{pdf.stem}-page-{page_number:03d}.{extension}"
            pixmap.save(output)
            exported.append(output)

    return ConversionResult(output_path=destination, page_count=len(exported), outputs=tuple(exported))


def pdf_to_word(
    pdf_path: Path | str,
    output_path: Path | str,
    *,
    ocr_enabled: bool = True,
    ocr_engine: OcrEngine | None = None,
) -> ConversionResult:
    pdf = _require_file(pdf_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    word = Document()
    pages_written = 0
    with fitz.open(pdf) as document:
        text_pages = [_extract_page_text(page) for page in document]
        if not any(page_text.strip() for page_text in text_pages) and not ocr_enabled:
            raise ConversionError("PDF does not contain editable text. Enable OCR for scanned documents.")

        engine: OcrEngine | None = None
        temp_dir: tempfile.TemporaryDirectory[str] | None = None
        try:
            for index, page in enumerate(document, start=1):
                page_text = text_pages[index - 1]
                if index > 1:
                    word.add_page_break()
                if page_text.strip():
                    _add_text_to_document(word, page_text)
                elif ocr_enabled:
                    if engine is None:
                        engine = ocr_engine or PaddleOcrEngine()
                    if temp_dir is None:
                        temp_dir = tempfile.TemporaryDirectory(prefix="offline-converter-ocr-")
                    image_path = Path(temp_dir.name) / f"page-{index:03d}.png"
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    pixmap.save(image_path)
                    lines = engine.recognize(image_path)
                    for line in lines:
                        if line.strip():
                            word.add_paragraph(line.strip())
                pages_written += 1
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

    word.save(output)
    return ConversionResult(output_path=output, page_count=pages_written, outputs=(output,))


def word_to_pdf(
    document_path: Path | str,
    output_dir: Path | str,
    *,
    soffice_path: Path | str | None = None,
) -> ConversionResult:
    source = _require_file(document_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    soffice = _resolve_soffice(soffice_path)

    completed = subprocess.run(
        [
            str(soffice),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(destination),
            str(source),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = destination / f"{source.stem}.pdf"
    if completed.returncode != 0 or not output.exists():
        details = (completed.stderr or completed.stdout or "unknown LibreOffice error").strip()
        raise ConversionError(f"LibreOffice failed to convert '{source.name}': {details}")

    return ConversionResult(output_path=output, page_count=1, outputs=(output,))


class PaddleOcrEngine:
    def __init__(self) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise MissingDependencyError(
                "PaddleOCR is required for scanned PDF OCR. Install the OCR bundle or run "
                "`python -m pip install paddleocr paddlepaddle`."
            ) from exc

        model_dirs = find_bundled_ocr_models()
        self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False, **model_dirs)

    def recognize(self, image_path: Path) -> list[str]:
        result = self._ocr.ocr(str(image_path), cls=True)
        lines: list[str] = []
        for page_result in result or []:
            for item in page_result or []:
                if len(item) >= 2 and isinstance(item[1], (list, tuple)) and item[1]:
                    text = str(item[1][0]).strip()
                    if text:
                        lines.append(text)
        return lines


def _require_file(path: Path | str) -> Path:
    resolved = Path(path)
    if not resolved.exists() or not resolved.is_file():
        raise ConversionError(f"Input file does not exist: {resolved}")
    return resolved


def _to_pdf_image(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image.copy()
    if image.mode in {"RGBA", "LA"}:
        background = Image.new("RGB", image.size, "white")
        alpha = image.getchannel("A") if "A" in image.getbands() else None
        background.paste(image, mask=alpha)
        return background
    return image.convert("RGB")


def _normalize_pages(pages: Sequence[int] | None, page_count: int) -> list[int]:
    if pages is None:
        return list(range(1, page_count + 1))
    normalized = list(dict.fromkeys(int(page) for page in pages))
    invalid = [page for page in normalized if page < 1 or page > page_count]
    if invalid:
        raise ConversionError(f"Page numbers out of range: {invalid}")
    return normalized


def _extract_page_text(page: fitz.Page) -> str:
    blocks = page.get_text("blocks")
    text_blocks = []
    for block in blocks:
        if len(block) >= 5 and str(block[4]).strip():
            text_blocks.append((float(block[1]), float(block[0]), str(block[4]).strip()))
    text_blocks.sort(key=lambda item: (item[0], item[1]))
    return "\n".join(block[2] for block in text_blocks)


def _add_text_to_document(word: Document, page_text: str) -> None:
    for line in page_text.splitlines():
        cleaned = line.strip()
        if cleaned:
            word.add_paragraph(cleaned)


def _resolve_soffice(soffice_path: Path | str | None) -> Path:
    if soffice_path is not None:
        candidate = Path(soffice_path)
        if candidate.exists() and candidate.is_file():
            return candidate
        raise MissingDependencyError(f"LibreOffice executable was not found: {candidate}")

    bundled = Path(__file__).resolve().parents[2] / "vendor" / "LibreOffice" / "program" / "soffice.exe"
    candidates = [
        bundled,
        Path("C:/Program Files/LibreOffice/program/soffice.exe"),
        Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
    ]
    discovered = find_soffice()
    if discovered:
        candidates.insert(0, discovered)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    raise MissingDependencyError(
        "LibreOffice is required for Word to PDF conversion. Bundle LibreOffice under "
        "`vendor/LibreOffice` or install LibreOffice locally."
    )
