# Test Samples

Do not commit private or sensitive documents here.

Use this directory for small sanitized PDFs only. Required sample categories for v0.2.0 validation:

- text PDF
- scanned Chinese PDF
- table/form PDF
- mixed text and scanned PDF
- multi-page PDF
- image-to-PDF input images
- Word-to-PDF input document

Automated tests may generate lightweight synthetic samples when binary fixtures are not present.

For private release validation, set `FILEFLOW_REAL_SAMPLE_DIR` to a local folder containing sanitized PDFs. The optional real-sample tests render the first page of every PDF and, when LibreOffice is available, run visual PDF-to-Word smoke checks without committing those documents.
