from __future__ import annotations

from pathlib import Path

from offline_converter import dependencies


def test_find_soffice_detects_bundled_vendor_runtime(monkeypatch, tmp_path: Path) -> None:
    soffice = tmp_path / "vendor" / "LibreOffice" / "program" / "soffice.exe"
    soffice.parent.mkdir(parents=True)
    soffice.write_bytes(b"")

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)
    monkeypatch.setattr(dependencies.shutil, "which", lambda _: None)

    assert dependencies.find_soffice() == soffice


def test_find_bundled_ocr_models_detects_vendor_models(monkeypatch, tmp_path: Path) -> None:
    model_root = tmp_path / "vendor" / "paddleocr" / "whl"
    for relative in [
        "det/ch/ch_PP-OCRv4_det_infer",
        "rec/ch/ch_PP-OCRv4_rec_infer",
        "cls/ch_ppocr_mobile_v2.0_cls_infer",
    ]:
        model_dir = model_root / relative
        model_dir.mkdir(parents=True)
        (model_dir / "inference.pdmodel").write_bytes(b"model")

    monkeypatch.setattr(dependencies, "_runtime_root", lambda: tmp_path)

    assert dependencies.find_bundled_ocr_models() == {
        "det_model_dir": model_root / "det" / "ch" / "ch_PP-OCRv4_det_infer",
        "rec_model_dir": model_root / "rec" / "ch" / "ch_PP-OCRv4_rec_infer",
        "cls_model_dir": model_root / "cls" / "ch_ppocr_mobile_v2.0_cls_infer",
    }
