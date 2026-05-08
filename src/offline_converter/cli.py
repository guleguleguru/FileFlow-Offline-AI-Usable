from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Sequence

from offline_converter import __version__
from offline_converter.converters import ConversionError
from offline_converter.dependencies import check_runtime_dependencies
from offline_converter.errors import FileFlowError, error_payload
from offline_converter.logging_utils import LOGGER_NAME, configure_logging, export_logs, log_path
from offline_converter.runner import output_paths_payload, parse_pages, run_task
from offline_converter.tasks import ConversionKind, ConversionTask, TaskStatus, accepted_extensions


KIND_ALIASES = {
    "image-to-pdf": ConversionKind.IMAGE_TO_PDF,
    "pdf-to-images": ConversionKind.PDF_TO_IMAGES,
    "word-to-pdf": ConversionKind.WORD_TO_PDF,
    "pdf-to-word": ConversionKind.PDF_TO_WORD,
}


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check-dependencies":
        return check_dependencies(json_output=args.json)
    if args.command == "convert":
        return convert(args)
    if args.command == "diagnose":
        return diagnose(json_output=args.json)
    if args.command == "export-logs":
        return export_logs_command(args)
    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="offline_converter",
        description="Offline PDF, Word, and image converter.",
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check-dependencies", help="Check bundled conversion engines.")
    check_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    diagnose_parser = subparsers.add_parser("diagnose", help="Print runtime diagnostics.")
    diagnose_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    export_parser = subparsers.add_parser("export-logs", help="Export diagnostic logs as a zip.")
    export_parser.add_argument("--output", required=True, type=Path, help="Output zip path.")
    export_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    convert_parser = subparsers.add_parser("convert", help="Run a conversion without opening the GUI.")
    convert_parser.add_argument("--kind", required=True, choices=sorted(KIND_ALIASES), help="Conversion type.")
    convert_parser.add_argument("--input", nargs="+", required=True, type=Path, help="Input file path(s).")
    convert_parser.add_argument("--output-dir", required=True, type=Path, help="Directory for converted files.")
    convert_parser.add_argument("--pages", default="", help="PDF page range for pdf-to-images, for example 1,3-5.")
    convert_parser.add_argument("--image-format", default="png", choices=["png", "jpg"], help="Image format for pdf-to-images.")
    convert_parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback for pdf-to-word.")
    convert_parser.add_argument(
        "--pdf-word-mode",
        default="visual",
        choices=["visual", "editable"],
        help="PDF to Word mode: visual preserves page appearance; editable prioritizes extracted text.",
    )
    convert_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def check_dependencies(*, json_output: bool = False) -> int:
    payload = check_runtime_dependencies(as_payload=True)
    issues = payload["issues"]
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif issues:
        for issue in issues:
            print(f"{issue['name']}: {issue['message']}", file=sys.stderr)
    else:
        print("dependencies-ok")
    return 0 if not issues else 1


def diagnose(*, json_output: bool = False) -> int:
    payload = {
        "ok": True,
        "version": __version__,
        "log_path": str(log_path()),
        "dependencies": check_runtime_dependencies(as_payload=True),
    }
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"version: {payload['version']}")
        print(f"log_path: {payload['log_path']}")
    return 0


def export_logs_command(args: argparse.Namespace) -> int:
    try:
        output = export_logs(args.output)
    except Exception as exc:
        return emit_result({"ok": False, "error": error_payload(exc), "tasks": []}, json_output=args.json)
    payload = {"ok": True, "output": str(output)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(output)
    return 0


def convert(args: argparse.Namespace) -> int:
    kind = KIND_ALIASES[args.kind]
    output_dir = args.output_dir.expanduser()
    options = {
        "pages": args.pages,
        "image_format": args.image_format,
        "ocr_enabled": not args.no_ocr,
        "pdf_word_mode": args.pdf_word_mode,
    }

    try:
        parse_pages(args.pages)
        tasks = build_tasks(kind, args.input, output_dir, options)
    except (ConversionError, ValueError) as exc:
        if isinstance(exc, ValueError):
            exc = FileFlowError(
                str(exc),
                code="invalid_pages",
                action="请使用类似 1,3-5 的页码格式。",
                detail=exc.__class__.__name__,
            )
        return emit_result({"ok": False, "tasks": [], "error": error_payload(exc)}, json_output=args.json)

    results: list[dict[str, object]] = []
    ok = True
    for task in tasks:
        task.status = TaskStatus.RUNNING
        logging.getLogger(LOGGER_NAME).info(
            "conversion started kind=%s inputs=%s output_dir=%s options=%s",
            task.kind.value,
            [str(path) for path in task.input_paths],
            task.output_dir,
            task.options,
        )
        try:
            result = run_task(task)
        except Exception as exc:
            logging.getLogger(LOGGER_NAME).exception(
                "conversion failed kind=%s inputs=%s output_dir=%s",
                task.kind.value,
                [str(path) for path in task.input_paths],
                task.output_dir,
            )
            ok = False
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            payload = task_payload(task)
            payload["error"] = error_payload(exc)
            results.append(payload)
        else:
            task.status = TaskStatus.COMPLETED
            task.outputs = result.outputs or (result.output_path,)
            logging.getLogger(LOGGER_NAME).info(
                "conversion completed kind=%s outputs=%s page_count=%s",
                task.kind.value,
                [str(path) for path in task.outputs],
                result.page_count,
            )
            payload = task_payload(task)
            payload["page_count"] = result.page_count
            results.append(payload)

    return emit_result({"ok": ok, "tasks": results}, json_output=args.json)


def build_tasks(
    kind: ConversionKind,
    input_paths: Sequence[Path],
    output_dir: Path,
    options: dict[str, object],
) -> list[ConversionTask]:
    paths = [path.expanduser() for path in input_paths]
    invalid = [
        path
        for path in paths
        if not path.is_file() or path.suffix.lower() not in accepted_extensions(kind)
    ]
    if invalid:
        raise ConversionError(
            f"Input file type does not match {kind.value}: {invalid[0]}",
            code="invalid_input",
            action="请选择存在的输入文件，并确认文件类型与转换方式匹配。",
        )
    if kind is ConversionKind.IMAGE_TO_PDF:
        return [ConversionTask(kind, tuple(paths), output_dir, options.copy())]
    return [ConversionTask(kind, (path,), output_dir, options.copy()) for path in paths]


def task_payload(task: ConversionTask) -> dict[str, object]:
    return {
        "id": task.id,
        "kind": task.kind.value,
        "status": task.status.value,
        "inputs": [str(path) for path in task.input_paths],
        "output_dir": str(task.output_dir),
        "outputs": output_paths_payload(task.outputs),
        "error": error_payload(ConversionError(task.error)) if task.error else "",
    }


def emit_result(payload: dict[str, object], *, json_output: bool) -> int:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload.get("ok"):
        for task in payload.get("tasks", []):
            if isinstance(task, dict):
                outputs = task.get("outputs") or []
                print(f"{task.get('status')}: {', '.join(str(path) for path in outputs)}")
    else:
        error = payload.get("error")
        if error:
            print(error, file=sys.stderr)
        for task in payload.get("tasks", []):
            if isinstance(task, dict) and task.get("error"):
                print(task["error"], file=sys.stderr)
    return 0 if payload.get("ok") else 1
