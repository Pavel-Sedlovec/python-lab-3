import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QDateTimeEdit, QSpinBox,
    QLineEdit, QLabel, QMessageBox, QSplitter, QStatusBar
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from api_client import ApiClient
from exceptions import InvalidSleepPeriodError, NoRecordSelectedError

logging.basicConfig(filename=Path(__file__).resolve().parent / "sleep_tracker.log",
                    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class SleepTrackerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = ApiClient()
        self.setWindowTitle("Sleep Tracker — учёт сна")
        self.resize(1050, 720)
        self._build_menu()
        self._build_ui()
        self.load_records()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addAction("Обновить", self.load_records)
        file_menu.addAction("Выход", self.close)
        help_menu = self.menuBar().addMenu("Справка")
        help_menu.addAction("О программе", lambda: QMessageBox.about(
            self, "О программе", "Sleep Tracker\nПриложение для учёта и анализа сна."
        ))

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.addWidget(QLabel("История сна"))
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Заснул", "Проснулся", "Длительность (ч)", "Качество (1–5)", "Заметка"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._fill_form_from_selection)
        self.records_by_id = {}
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.table)

        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        self.figure = Figure(figsize=(7, 2.5))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        splitter.addWidget(chart_widget)
        splitter.setSizes([350, 230])
        root.addWidget(splitter)

        form = QFormLayout()
        now = QDateTime.currentDateTime()
        self.start_edit = QDateTimeEdit(now.addSecs(-3600 * 8))
        self.end_edit = QDateTimeEdit(now)
        for widget in (self.start_edit, self.end_edit):
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.quality_edit = QSpinBox()
        self.quality_edit.setRange(1, 5)
        self.quality_edit.setValue(3)
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Например: хорошо выспался")
        form.addRow("Время засыпания:", self.start_edit)
        form.addRow("Время пробуждения:", self.end_edit)
        form.addRow("Качество сна:", self.quality_edit)
        form.addRow("Заметки:", self.notes_edit)
        root.addLayout(form)

        buttons = QHBoxLayout()
        for title, callback in [
            ("Добавить", self.add_record),
            ("Изменить выбранную", self.edit_record),
            ("Удалить выбранную", self.delete_record),
            ("Обновить", self.load_records),
        ]:
            button = QPushButton(title)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        root.addLayout(buttons)
        self.stats_label = QLabel("Статистика: —")
        root.addWidget(self.stats_label)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Готово")

    def _fill_form_from_selection(self):
        row = self.table.currentRow()
        if row < 0:
            return
        id_item = self.table.item(row, 0)
        if id_item is None:
            return
        record = self.records_by_id.get(int(id_item.text()))
        if record is None:
            return
        start = datetime.fromisoformat(record["sleep_start"])
        end = datetime.fromisoformat(record["sleep_end"])
        self.start_edit.setDateTime(QDateTime(start.year, start.month, start.day,
                                              start.hour, start.minute, start.second))
        self.end_edit.setDateTime(QDateTime(end.year, end.month, end.day,
                                            end.hour, end.minute, end.second))
        self.quality_edit.setValue(record["quality"])
        self.notes_edit.setText(record.get("notes") or "")

    def _payload(self):
        start = self.start_edit.dateTime().toPython()
        end = self.end_edit.dateTime().toPython()
        if end <= start:
            raise InvalidSleepPeriodError("Время пробуждения должно быть позже времени засыпания.")
        return {"sleep_start": start.isoformat(), "sleep_end": end.isoformat(),
                "quality": self.quality_edit.value(), "notes": self.notes_edit.text().strip() or None}

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            raise NoRecordSelectedError("Сначала выбери запись в таблице.")
        return int(self.table.item(row, 0).text())

    def _show_error(self, exc):
        logging.exception("Ошибка приложения")
        QMessageBox.critical(self, "Ошибка", str(exc))
        self.statusBar().showMessage("Операция не выполнена")

    def add_record(self):
        try:
            self.api.create_record(self._payload())
            logging.info("Добавлена запись сна")
            self.load_records()
            self.statusBar().showMessage("Запись добавлена")
        except Exception as exc:
            self._show_error(exc)

    def edit_record(self):
        try:
            record_id = self._selected_id()
            self.api.update_record(record_id, self._payload())
            logging.info("Изменена запись id=%s", record_id)
            self.load_records()
            self.statusBar().showMessage("Запись изменена")
        except Exception as exc:
            self._show_error(exc)

    def delete_record(self):
        try:
            record_id = self._selected_id()
            answer = QMessageBox.question(self, "Подтверждение", "Удалить выбранную запись?")
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.api.delete_record(record_id)
            logging.info("Удалена запись id=%s", record_id)
            self.load_records()
            self.statusBar().showMessage("Запись удалена")
        except Exception as exc:
            self._show_error(exc)

    def load_records(self):
        try:
            records = self.api.list_records()
            self.records_by_id = {record["id"]: record for record in records}
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                start = datetime.fromisoformat(record["sleep_start"])
                end = datetime.fromisoformat(record["sleep_end"])
                duration = (end - start).total_seconds() / 3600
                values = [str(record["id"]), start.strftime("%Y-%m-%d %H:%M"),
                          end.strftime("%Y-%m-%d %H:%M"), f"{duration:.2f}", str(record["quality"]), record.get("notes") or ""]
                for col, value in enumerate(values):
                    self.table.setItem(row, col, QTableWidgetItem(value))
            stats = self.api.stats()
            average = stats["average_duration_hours"]
            avg_text = f"{average:.2f} ч" if average is not None else "нет данных"
            self.stats_label.setText(f"Всего записей: {stats['records_count']} · Средняя длительность: {avg_text}")
            self._draw_chart(records)
            self.statusBar().showMessage(f"Загружено записей: {len(records)}")
        except Exception as exc:
            self._show_error(exc)

    def _draw_chart(self, records):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ordered = sorted(records, key=lambda r: r["sleep_start"])
        labels, durations = [], []
        for record in ordered:
            start = datetime.fromisoformat(record["sleep_start"])
            end = datetime.fromisoformat(record["sleep_end"])
            labels.append(start.strftime("%d.%m"))
            durations.append((end - start).total_seconds() / 3600)
        if durations:
            ax.bar(labels, durations)
            ax.axhline(8, linestyle="--", label="Цель: 8 ч")
            ax.legend()
            ax.set_ylabel("Часы сна")
            ax.set_title("Продолжительность сна")
        else:
            ax.text(0.5, 0.5, "Добавьте запись, чтобы увидеть график",
                    ha="center", va="center", transform=ax.transAxes)
        self.figure.tight_layout()
        self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    window = SleepTrackerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
