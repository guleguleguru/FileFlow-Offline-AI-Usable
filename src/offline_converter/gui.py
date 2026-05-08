from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QDropEvent, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from offline_converter.dependencies import check_runtime_dependencies
from offline_converter.errors import error_payload
from offline_converter.logging_utils import export_logs
from offline_converter.runner import run_task
from offline_converter.tasks import ConversionKind, ConversionTask, TaskStatus, accepted_extensions

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ICON_PATH = PROJECT_ROOT / "assets" / "converter-icon.ico"

APP_STYLESHEET = """
QWidget#appRoot {
    background: #f4f7fa;
    color: #17212f;
    font-family: "Microsoft YaHei", "Microsoft YaHei UI", "Segoe UI";
    font-size: 14px;
}
QLabel#appTitle {
    color: #102033;
    font-size: 26px;
    font-weight: 800;
}
QLabel {
    color: #102033;
}
QLabel#stepText, QLabel#summaryText {
    color: #4f6178;
}
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    font-weight: 700;
}
QPushButton#kindButton {
    background: #ffffff;
    border: 1px solid #d4dee8;
    color: #233247;
    min-height: 44px;
}
QPushButton#kindButton:checked {
    background: #176b87;
    border: 1px solid #176b87;
    color: #ffffff;
}
QPushButton#dropButton {
    background: #ffffff;
    border: 2px dashed #9fb4c5;
    color: #34465c;
    font-size: 18px;
    min-height: 104px;
}
QPushButton#primaryButton {
    background: #176b87;
    color: white;
    min-height: 42px;
}
QPushButton#startButton {
    background: #21824f;
    color: white;
    min-height: 46px;
    font-size: 16px;
}
QPushButton#secondaryButton {
    background: #e5ecf2;
    color: #253447;
    min-height: 38px;
}
QPushButton:hover {
    background: #2283a4;
}
QPushButton#secondaryButton:hover {
    background: #d7e1e9;
}
QPushButton:disabled {
    background: #cbd5de;
    color: #7f8b96;
}
QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #cbd6e2;
    border-radius: 7px;
    color: #102033;
    padding: 8px 10px;
    min-height: 28px;
}
QLineEdit:disabled, QComboBox:disabled {
    color: #6b7b8f;
    background: #eef3f7;
}
QLineEdit::placeholder {
    color: #6b7b8f;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #176b87;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #102033;
    selection-background-color: #d6edf7;
    selection-color: #102033;
}
QCheckBox {
    color: #102033;
}
QTableWidget#taskTable {
    background: #ffffff;
    alternate-background-color: #f8fbfd;
    border: 1px solid #dbe4ec;
    border-radius: 9px;
    selection-background-color: #d6edf7;
    selection-color: #17212f;
}
QTableWidget#taskTable::item {
    color: #102033;
    padding: 4px;
}
QTableWidget#taskTable::item:selected {
    background: #d6edf7;
    color: #102033;
}
QHeaderView::section {
    background: #eaf1f5;
    border: none;
    border-bottom: 1px solid #d2dee8;
    color: #34465c;
    font-weight: 800;
    padding: 9px;
}
QMessageBox {
    background: #ffffff;
    color: #102033;
}
QMessageBox QLabel {
    color: #102033;
}
QMessageBox QPushButton {
    background: #176b87;
    color: #ffffff;
    min-width: 78px;
    padding: 8px 18px;
}
QMessageBox QPushButton:hover {
    background: #2283a4;
}
"""


class DropButton(QPushButton):
    filesDropped = Signal(list)

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("dropButton")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        files = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if files:
            self.filesDropped.emit(files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class TaskTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, 4)
        self.setObjectName("taskTable")
        self.setHorizontalHeaderLabels(["文件", "转换", "状态", "结果"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)


class ConversionWorker(QObject):
    taskStarted = Signal(int)
    taskFinished = Signal(int, object)
    taskFailed = Signal(int, str)
    allFinished = Signal()

    def __init__(self, tasks: list[tuple[int, ConversionTask]]) -> None:
        super().__init__()
        self._tasks = tasks

    def run(self) -> None:
        for row, task in self._tasks:
            self.taskStarted.emit(row)
            try:
                result = run_task(task)
            except Exception as exc:
                self.taskFailed.emit(row, str(exc))
            else:
                self.taskFinished.emit(row, result.outputs or (result.output_path,))
        self.allFinished.emit()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_kind = ConversionKind.PDF_TO_WORD
        self.tasks: list[ConversionTask] = []
        self.worker_thread: QThread | None = None
        self.worker: ConversionWorker | None = None

        self.setWindowTitle("离线文件转换器")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(980, 640)
        self._build_ui()
        self._show_dependency_warnings()

    def _build_ui(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)

        root = QWidget()
        root.setObjectName("appRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        self.setCentralWidget(root)

        title_row = QHBoxLayout()
        title = QLabel("离线文件转换器")
        title.setObjectName("appTitle")
        self.summary_label = QLabel("0 个文件")
        self.summary_label.setObjectName("summaryText")
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.summary_label)
        layout.addLayout(title_row)

        step_text = QLabel("1 选择转换方式    2 添加文件    3 点击开始转换")
        step_text.setObjectName("stepText")
        layout.addWidget(step_text)

        self.kind_group = QButtonGroup(self)
        kind_row = QHBoxLayout()
        kind_row.setSpacing(10)
        for kind in [
            ConversionKind.PDF_TO_WORD,
            ConversionKind.IMAGE_TO_PDF,
            ConversionKind.PDF_TO_IMAGES,
            ConversionKind.WORD_TO_PDF,
        ]:
            button = QPushButton(kind.label)
            button.setObjectName("kindButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, selected=kind: self._set_kind(selected))
            self.kind_group.addButton(button)
            kind_row.addWidget(button)
            if kind is self.current_kind:
                button.setChecked(True)
        layout.addLayout(kind_row)

        self.drop_button = DropButton("点击添加文件，或把文件拖到这里")
        self.drop_button.clicked.connect(self.choose_files)
        self.drop_button.filesDropped.connect(self.add_paths)
        layout.addWidget(self.drop_button)

        output_row = QHBoxLayout()
        output_label = QLabel("保存到")
        self.output_edit = QLineEdit(str(Path.home() / "Documents" / "Converted"))
        choose_output = QPushButton("更改")
        choose_output.setObjectName("secondaryButton")
        choose_output.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        choose_output.clicked.connect(self.choose_output_dir)
        output_row.addWidget(output_label)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(choose_output)
        layout.addLayout(output_row)

        self.option_row = QHBoxLayout()
        self.option_label = QLabel("")
        self.pages_edit = QLineEdit()
        self.pages_edit.setPlaceholderText("页码，例如 1,3-5；留空为全部")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpg"])
        self.ocr_check = QCheckBox("扫描件使用中文 OCR")
        self.ocr_check.setChecked(True)
        self.pdf_word_mode_combo = QComboBox()
        self.pdf_word_mode_combo.addItem("原版式优先", "visual")
        self.pdf_word_mode_combo.addItem("文字可编辑优先", "editable")
        self.option_row.addWidget(self.option_label)
        self.option_row.addWidget(self.pages_edit)
        self.option_row.addWidget(self.format_combo)
        self.option_row.addWidget(self.pdf_word_mode_combo)
        self.option_row.addWidget(self.ocr_check)
        self.option_row.addStretch()
        layout.addLayout(self.option_row)

        self.table = TaskTable()
        layout.addWidget(self.table, 1)

        action_row = QHBoxLayout()
        self.add_button = QPushButton("添加文件")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.add_button.clicked.connect(self.choose_files)
        self.start_button = QPushButton("开始转换")
        self.start_button.setObjectName("startButton")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.clicked.connect(self.start_conversion)
        self.remove_button = QPushButton("移除选中")
        self.remove_button.setObjectName("secondaryButton")
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button = QPushButton("清空")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(self.clear_tasks)
        self.export_logs_button = QPushButton("导出日志")
        self.export_logs_button.setObjectName("secondaryButton")
        self.export_logs_button.clicked.connect(self.export_logs)
        action_row.addWidget(self.add_button)
        action_row.addWidget(self.start_button)
        action_row.addStretch()
        action_row.addWidget(self.export_logs_button)
        action_row.addWidget(self.remove_button)
        action_row.addWidget(self.clear_button)
        layout.addLayout(action_row)

        self._sync_options()
        self._update_summary()

    def _show_dependency_warnings(self) -> None:
        issues = check_runtime_dependencies()
        if not issues:
            return
        message = "\n".join(f"- {issue.message}\n  处理方式：安装对应 Addon，或使用不依赖该组件的转换方式。" for issue in issues)
        QMessageBox.warning(
            self,
            "部分转换能力需要补充组件",
            f"{message}\n\n图片转 PDF、PDF 转图片、文字型 PDF 转 Word 仍可继续使用。",
        )

    def _set_kind(self, kind: ConversionKind) -> None:
        self.current_kind = kind
        self._sync_options()

    def _sync_options(self) -> None:
        kind = self.current_kind
        self.pages_edit.setVisible(kind is ConversionKind.PDF_TO_IMAGES)
        self.format_combo.setVisible(kind is ConversionKind.PDF_TO_IMAGES)
        self.ocr_check.setVisible(kind is ConversionKind.PDF_TO_WORD)
        self.pdf_word_mode_combo.setVisible(kind is ConversionKind.PDF_TO_WORD)
        self.option_label.setVisible(kind in {ConversionKind.PDF_TO_IMAGES, ConversionKind.PDF_TO_WORD})
        if kind is ConversionKind.PDF_TO_IMAGES:
            self.option_label.setText("可选")
        elif kind is ConversionKind.PDF_TO_WORD:
            self.option_label.setText("选项")

        hints = {
            ConversionKind.PDF_TO_WORD: "添加 PDF，转换成可编辑 Word",
            ConversionKind.IMAGE_TO_PDF: "添加图片，合成一个 PDF",
            ConversionKind.PDF_TO_IMAGES: "添加 PDF，导出为图片",
            ConversionKind.WORD_TO_PDF: "添加 Word，转换成 PDF",
        }
        self.drop_button.setText(hints[kind] + "\n\n点击添加文件，或拖到这里")

    def choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text())
        if directory:
            self.output_edit.setText(directory)

    def choose_files(self) -> None:
        filters = {
            ConversionKind.IMAGE_TO_PDF: "图片文件 (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff)",
            ConversionKind.PDF_TO_IMAGES: "PDF 文件 (*.pdf)",
            ConversionKind.PDF_TO_WORD: "PDF 文件 (*.pdf)",
            ConversionKind.WORD_TO_PDF: "Word 文件 (*.doc *.docx)",
        }
        files, _ = QFileDialog.getOpenFileNames(self, "添加文件", str(Path.home()), filters[self.current_kind])
        self.add_paths([Path(file) for file in files])

    def add_paths(self, paths: Iterable[Path]) -> None:
        output_dir = Path(self.output_edit.text()).expanduser()
        valid = [path for path in paths if path.is_file() and path.suffix.lower() in accepted_extensions(self.current_kind)]
        if not valid:
            QMessageBox.information(self, "文件类型不匹配", "请先选择正确的转换方式，再添加对应文件。")
            return

        options = self._current_options()
        if self.current_kind is ConversionKind.IMAGE_TO_PDF:
            self._append_task(ConversionTask(self.current_kind, tuple(sorted(valid)), output_dir, options))
            return

        for path in valid:
            self._append_task(ConversionTask(self.current_kind, (path,), output_dir, options.copy()))

    def _current_options(self) -> dict[str, object]:
        return {
            "image_format": self.format_combo.currentText(),
            "pages": self.pages_edit.text(),
            "ocr_enabled": self.ocr_check.isChecked(),
            "pdf_word_mode": self.pdf_word_mode_combo.currentData(),
        }

    def _append_task(self, task: ConversionTask) -> None:
        row = self.table.rowCount()
        self.tasks.append(task)
        self.table.insertRow(row)
        self._paint_row(row)

    def _paint_row(self, row: int) -> None:
        task = self.tasks[row]
        result = task.error or task.display_output
        values = [task.display_input, task.kind.label, task.status.value, result]
        status_color = {
            TaskStatus.PENDING: QColor("#516173"),
            TaskStatus.RUNNING: QColor("#0f6d9a"),
            TaskStatus.COMPLETED: QColor("#1c7a46"),
            TaskStatus.FAILED: QColor("#b42318"),
        }[task.status]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setForeground(QBrush(QColor("#102033")))
            if column == 2:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QBrush(status_color))
            if column == 3 and task.status is TaskStatus.FAILED:
                item.setForeground(QBrush(status_color))
            self.table.setItem(row, column, item)
        self._update_summary()

    def remove_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
            del self.tasks[row]
        self._update_summary()

    def clear_tasks(self) -> None:
        self.tasks.clear()
        self.table.setRowCount(0)
        self._update_summary()

    def export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出日志", str(Path.home() / "Desktop" / "fileflow-logs.zip"), "Zip (*.zip)")
        if not path:
            return
        try:
            output = export_logs(Path(path))
        except Exception as exc:
            payload = error_payload(exc)
            QMessageBox.warning(self, "日志导出失败", f"{payload['message']}\n\n建议：{payload['action']}")
        else:
            QMessageBox.information(self, "日志已导出", f"日志已保存到：\n{output}")

    def start_conversion(self) -> None:
        pending = [
            (row, task)
            for row, task in enumerate(self.tasks)
            if task.status in {TaskStatus.PENDING, TaskStatus.FAILED}
        ]
        if not pending:
            QMessageBox.information(self, "没有文件", "请先添加要转换的文件。")
            return
        for _, task in pending:
            task.output_dir.mkdir(parents=True, exist_ok=True)
        self._set_controls_enabled(False)
        self.worker_thread = QThread()
        self.worker = ConversionWorker(pending)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.taskStarted.connect(self._task_started)
        self.worker.taskFinished.connect(self._task_finished)
        self.worker.taskFailed.connect(self._task_failed)
        self.worker.allFinished.connect(self._conversion_finished)
        self.worker.allFinished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _task_started(self, row: int) -> None:
        self.tasks[row].status = TaskStatus.RUNNING
        self.tasks[row].error = ""
        self._paint_row(row)

    def _task_finished(self, row: int, outputs: object) -> None:
        task = self.tasks[row]
        task.status = TaskStatus.COMPLETED
        task.outputs = tuple(Path(path) for path in outputs)
        task.error = ""
        self._paint_row(row)

    def _task_failed(self, row: int, message: str) -> None:
        task = self.tasks[row]
        task.status = TaskStatus.FAILED
        task.error = message
        self._paint_row(row)

    def _conversion_finished(self) -> None:
        self._set_controls_enabled(True)
        self._update_summary()
        QMessageBox.information(self, "转换完成", "处理完成，结果已显示在列表中。")

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.add_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.export_logs_button.setEnabled(enabled)
        for button in self.kind_group.buttons():
            button.setEnabled(enabled)

    def _update_summary(self) -> None:
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.status is TaskStatus.COMPLETED)
        failed = sum(1 for task in self.tasks if task.status is TaskStatus.FAILED)
        if total == 0:
            self.summary_label.setText("0 个文件")
            return
        text = f"{total} 个文件"
        if completed:
            text += f" · {completed} 完成"
        if failed:
            text += f" · {failed} 失败"
        self.summary_label.setText(text)


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#102033"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#102033"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#102033"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#d6edf7"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#102033"))
    app.setPalette(palette)
    app.setStyleSheet(APP_STYLESHEET)
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    window = MainWindow()
    window.show()
    return app.exec()
