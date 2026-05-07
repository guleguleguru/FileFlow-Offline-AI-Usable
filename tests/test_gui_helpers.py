from __future__ import annotations

import pytest

from offline_converter.converters import ConversionError
from offline_converter.gui import APP_STYLESHEET
from offline_converter.runner import parse_pages


def test_parse_pages_accepts_commas_spaces_and_ranges() -> None:
    assert parse_pages("1, 3-5 7") == [1, 3, 4, 5, 7]


def test_parse_pages_returns_none_for_empty_value() -> None:
    assert parse_pages("  ") is None


def test_parse_pages_rejects_reversed_range() -> None:
    with pytest.raises(ConversionError, match="Invalid page range"):
        parse_pages("5-3")


def test_stylesheet_pins_readable_text_colors() -> None:
    assert "QLabel {" in APP_STYLESHEET
    assert "QTableWidget#taskTable::item:selected" in APP_STYLESHEET
    assert "selection-color: #102033" in APP_STYLESHEET
    assert "color: #102033" in APP_STYLESHEET
    assert "QMessageBox QLabel" in APP_STYLESHEET
    assert "QMessageBox QPushButton" in APP_STYLESHEET
