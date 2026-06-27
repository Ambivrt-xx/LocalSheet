"""
ChartDialog — dialog for selecting chart type and viewing the chart.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup,
    QLabel, QComboBox, QDialogButtonBox
)
from .chart_widget import ChartWidget


class ChartDialog(QDialog):
    """Dialog that displays a chart with type selector."""

    def __init__(self, labels, values, title="", parent=None):
        super().__init__(parent)
        self.labels = labels
        self.values = values
        self.chart_title = title
        self.setWindowTitle("Chart")
        self.setMinimumSize(640, 480)
        self.setStyleSheet(self._stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Toolbar row: chart type selector
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Chart type:"))

        self.type_combo = QComboBox()
        self.type_combo.addItem("Bar Chart", "bar")
        self.type_combo.addItem("Line Chart", "line")
        self.type_combo.addItem("Pie Chart", "pie")
        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        toolbar.addWidget(self.type_combo)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        # Chart widget
        self.chart = ChartWidget('bar', labels, values, title)
        layout.addWidget(self.chart, 1)

        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_type_change(self):
        chart_type = self.type_combo.currentData()
        self.chart.set_data(chart_type, self.labels, self.values, self.chart_title)

    def _stylesheet(self):
        return """
            QDialog { background: #f8f9fa; }
            QLabel { color: #3c4043; font-size: 13px; }
            QComboBox {
                padding: 4px 8px; border: 1px solid #dadce0;
                border-radius: 4px; background: white; font-size: 13px;
            }
            QPushButton {
                padding: 6px 16px; border: 1px solid #dadce0;
                border-radius: 4px; background: white; font-size: 13px;
            }
            QPushButton:hover { background: #f1f3f4; }
        """