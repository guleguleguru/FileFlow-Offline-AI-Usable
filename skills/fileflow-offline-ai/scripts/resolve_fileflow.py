from __future__ import annotations

import json
from pathlib import Path


def candidates() -> list[Path]:
    cwd = Path.cwd()
    project = Path("C:/工作/offline-file-converter")
    roots = list(dict.fromkeys([cwd, project]))
    paths: list[Path] = []
    for root in roots:
        paths.extend(
            [
                root / "release-components-agent" / "离线文件转换器",
                root / "dist-agent" / "离线文件转换器",
                root / "release-components-reviewed" / "离线文件转换器",
                root / "dist-reviewed" / "离线文件转换器",
            ]
        )
    return paths


def main() -> int:
    entries = []
    for folder in candidates():
        entries.append(
            {
                "folder": str(folder),
                "agent": str(folder / "offline-converter-agent.exe"),
                "agent_exists": (folder / "offline-converter-agent.exe").exists(),
                "gui": str(folder / "离线文件转换器.exe"),
                "gui_exists": (folder / "离线文件转换器.exe").exists(),
            }
        )
    print(json.dumps({"candidates": entries}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
