from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4


class ConversionKind(str, Enum):
    IMAGE_TO_PDF = "image_to_pdf"
    PDF_TO_IMAGES = "pdf_to_images"
    WORD_TO_PDF = "word_to_pdf"
    PDF_TO_WORD = "pdf_to_word"

    @property
    def label(self) -> str:
        return {
            ConversionKind.IMAGE_TO_PDF: "图片转 PDF",
            ConversionKind.PDF_TO_IMAGES: "PDF 转图片",
            ConversionKind.WORD_TO_PDF: "Word 转 PDF",
            ConversionKind.PDF_TO_WORD: "PDF 转 Word",
        }[self]


class TaskStatus(str, Enum):
    PENDING = "待处理"
    RUNNING = "转换中"
    COMPLETED = "完成"
    FAILED = "失败"


@dataclass
class ConversionTask:
    kind: ConversionKind
    input_paths: tuple[Path, ...]
    output_dir: Path
    options: dict[str, object] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    outputs: tuple[Path, ...] = ()
    error: str = ""

    @property
    def display_input(self) -> str:
        if len(self.input_paths) == 1:
            return str(self.input_paths[0])
        return f"{len(self.input_paths)} 个图片文件"

    @property
    def display_output(self) -> str:
        if self.outputs:
            if len(self.outputs) == 1:
                return str(self.outputs[0])
            return f"{len(self.outputs)} 个输出文件"
        return str(self.output_dir)


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
PDF_EXTENSIONS = {".pdf"}
WORD_EXTENSIONS = {".doc", ".docx"}


def accepted_extensions(kind: ConversionKind) -> set[str]:
    if kind is ConversionKind.IMAGE_TO_PDF:
        return IMAGE_EXTENSIONS
    if kind in {ConversionKind.PDF_TO_IMAGES, ConversionKind.PDF_TO_WORD}:
        return PDF_EXTENSIONS
    if kind is ConversionKind.WORD_TO_PDF:
        return WORD_EXTENSIONS
    return set()
