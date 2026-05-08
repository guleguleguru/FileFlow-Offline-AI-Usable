from __future__ import annotations

from pathlib import Path
import re

from offline_converter.converters import ConversionError, image_to_pdf, pdf_to_images, pdf_to_word, word_to_pdf
from offline_converter.tasks import ConversionKind, ConversionTask


def run_task(task: ConversionTask):
    if task.kind is ConversionKind.IMAGE_TO_PDF:
        first = task.input_paths[0]
        name = f"{first.stem}.pdf" if len(task.input_paths) == 1 else f"{first.stem}-combined.pdf"
        return image_to_pdf(task.input_paths, task.output_dir / name, quality=90, auto_rotate=True)
    if task.kind is ConversionKind.PDF_TO_IMAGES:
        source = task.input_paths[0]
        return pdf_to_images(
            source,
            task.output_dir / source.stem,
            image_format=str(task.options.get("image_format", "png")),
            dpi=150,
            pages=parse_pages(str(task.options.get("pages", ""))),
        )
    if task.kind is ConversionKind.PDF_TO_WORD:
        source = task.input_paths[0]
        return pdf_to_word(
            source,
            task.output_dir / f"{source.stem}.docx",
            ocr_enabled=bool(task.options.get("ocr_enabled", True)),
            mode=str(task.options.get("pdf_word_mode", "visual")),
        )
    if task.kind is ConversionKind.WORD_TO_PDF:
        return word_to_pdf(task.input_paths[0], task.output_dir)
    raise ConversionError(f"Unsupported conversion kind: {task.kind}")


def parse_pages(value: str) -> list[int] | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    pages: list[int] = []
    for token in re.split(r"[,，\s]+", cleaned):
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ConversionError(f"Invalid page range: {token}")
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(token))
    return pages


def output_paths_payload(paths: tuple[Path, ...]) -> list[str]:
    return [str(path) for path in paths]
