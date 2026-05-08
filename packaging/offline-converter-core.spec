# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

spec_path = Path(SPECPATH)
project_root = spec_path if (spec_path / "src").exists() else spec_path.parent
assets = project_root / "assets"
datas = []
if assets.exists():
    datas.append((str(assets), "assets"))

a = Analysis(
    [str(project_root / "src" / "offline_converter" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "fitz",
        "docx",
        "PIL",
        "PIL.ImageDraw",
        "PIL.ImageEnhance",
        "PIL.ImageFilter",
        "PIL.ImageFont",
        "PIL.ImageOps",
        "http.client",
        "http.cookies",
        "http.cookiejar",
        "logging.handlers",
        "sqlite3",
        "_sqlite3",
        "wave",
        "zoneinfo",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "cv2",
        "matplotlib",
        "numpy.distutils",
        "paddle",
        "paddleocr",
        "pandas",
        "pytest",
        "scipy",
        "skimage",
        "sklearn",
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
    name="FileFlowOffline-Core",
)
