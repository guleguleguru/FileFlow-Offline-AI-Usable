# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

spec_path = Path(SPECPATH)
project_root = spec_path if (spec_path / "src").exists() else spec_path.parent
vendor = project_root / "vendor"
assets = project_root / "assets"
datas = []
if vendor.exists():
    datas.append((str(vendor), "vendor"))
if assets.exists():
    datas.append((str(assets), "assets"))
datas += collect_data_files("paddleocr", include_py_files=False)
datas += collect_data_files("paddle", include_py_files=False)
binaries = collect_dynamic_libs("paddle")
hiddenimports = ["fitz", "docx", "PIL", "cv2"] + collect_submodules("paddleocr") + collect_submodules("paddle")

a = Analysis(
    [str(project_root / "src" / "offline_converter" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "babel",
        "docutils",
        "jinja2",
        "matplotlib",
        "openpyxl",
        "pandas",
        "pyarrow",
        "pytest",
        "pytz",
        "sphinx",
        "sqlalchemy",
        "tzdata",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

gui_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="离线文件转换器",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "assets" / "converter-icon.ico"),
)
agent_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="offline-converter-agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(project_root / "assets" / "converter-icon.ico"),
)
coll = COLLECT(
    gui_exe,
    agent_exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="离线文件转换器",
)
