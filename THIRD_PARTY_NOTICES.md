# Third-Party Notices

This project source code is licensed under the MIT License.

Runtime bundles and release packages may include third-party components that
remain under their own licenses, including but not limited to:

- LibreOffice: office conversion runtime used by the optional LibreOffice Addon.
- PaddleOCR: OCR pipeline used by the optional OCR Addon.
- PaddlePaddle: PaddleOCR inference runtime used by the optional OCR Addon.
- PySide6: Windows desktop GUI runtime.
- PyMuPDF: PDF rendering and text extraction.
- python-docx: DOCX generation.
- Pillow: image loading and PDF/image conversion helpers.

When distributing binary release packages, review and comply with the license
terms of each bundled dependency. Large third-party runtimes and OCR models are
not part of the source repository and should be distributed only as GitHub
Release assets or other binary packages.
