from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from offline_converter.converters import ConversionError
from offline_converter.dependencies import check_runtime_dependencies
from offline_converter.runner import output_paths_payload, parse_pages, run_task
from offline_converter.tasks import ConversionKind, ConversionTask, TaskStatus, accepted_extensions


KIND_ALIASES = {
    "image-to-pdf": ConversionKind.IMAGE_TO_PDF,
    "pdf-to-images": ConversionKind.PDF_TO_IMAGES,
    "word-to-pdf": ConversionKind.WORD_TO_PDF,
    "pdf-to-word": ConversionKind.PDF_TO_WORD,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check-dependencies":
        return check_dependencies(json_output=args.json)
    if args.command == "convert":
        return convert(args)
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

    convert_parser = subparsers.add_parser("convert", help="Run a conversion without opening the GUI.")
    convert_parser.add_argument("--kind", required=True, choices=sorted(KIND_ALIASES), help="Conversion type.")
    convert_parser.add_argument("--input", nargs="+", required=True, type=Path, help="Input file path(s).")
    convert_parser.add_argument("--output-dir", required=True, type=Path, help="Directory for converted files.")
    convert_parser.add_argument("--pages", default="", help="PDF page range for pdf-to-images, for example 1,3-5.")
    convert_parser.add_argument("--image-format", default="png", choices=["png", "jpg"], help="Image format for pdf-to-images.")
    convert_parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback for pdf-to-word.")
    convert_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def check_dependencies(*, json_output: bool = False) -> int:
    issues = check_runtime_dependencies()
    payload = {
        "ok": not issues,
        "issues": [
            {"name": issue.name, "message": issue.message, "required_for": issue.required_for}
            for issue in issues
        ],
    }
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif issues:
        for issue in issues:
            print(f"{issue.name}: {issue.message}", file=sys.stderr)
    else:
        print("dependencies-ok")
    return 0 if not issues else 1


def convert(args: argparse.Namespace) -> int:
    kind = KIND_ALIASES[args.kind]
    output_dir = args.output_dir.expanduser()
    options = {
        "pages": args.pages,
        "image_format": args.image_format,
        "ocr_enabled": not args.no_ocr,
    }

    try:
        parse_pages(args.pages)
        tasks = build_tasks(kind, args.input, output_dir, options)
    except (ConversionError, ValueError) as exc:
        return emit_result({"ok": False, "tasks": [], "error": str(exc)}, json_output=args.json)

    results: list[dict[str, object]] = []
    ok = True
    for task in tasks:
        task.status = TaskStatus.RUNNING
        try:
            result = run_task(task)
        except Exception as exc:
            ok = False
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            results.append(task_payload(task))
        else:
            task.status = TaskStatus.COMPLETED
            task.outputs = result.outputs or (result.output_path,)
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
        raise ConversionError(f"Input file type does not match {kind.value}: {invalid[0]}")
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
        "error": task.error,
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
