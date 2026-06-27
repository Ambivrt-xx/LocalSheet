"""
CellStylesDialog — quick-apply cell style presets.
Good, Bad, Neutral, Heading 1-4, Input, Output, Calculation, Total, Warning.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QLabel, QDialogButtonBox
)


STYLE_PRESETS = {
    "Good": {
        'bg_color': "#c6efce", 'text_color': "#006100",
        'bold': False, 'italic': False,
    },
    "Bad": {
        'bg_color': "#ffc7ce", 'text_color': "#9c0006",
        'bold': False, 'italic': False,
    },
    "Neutral": {
        'bg_color': "#ffeb9c", 'text_color': "#9c6500",
        'bold': False, 'italic': False,
    },
    "Heading 1": {
        'bg_color': "#4472c4", 'text_color': "#ffffff",
        'bold': True, 'font_size': 14, 'align': 'left',
    },
    "Heading 2": {
        'bg_color': "#5b9bd5", 'text_color': "#ffffff",
        'bold': True, 'font_size': 12, 'align': 'left',
    },
    "Heading 3": {
        'bg_color': "#9dc3e6", 'text_color': "#1f3864",
        'bold': True, 'font_size': 11, 'align': 'left',
    },
    "Heading 4": {
        'bg_color': "#bdd7ee", 'text_color': "#1f3864",
        'bold': True, 'font_size': 11, 'align': 'left',
    },
    "Input": {
        'bg_color': "#ffcc99", 'text_color': "#3c4043",
        'border': 'all', 'bold': False,
    },
    "Output": {
        'bg_color': "#f2f2f2", 'text_color': "#3c4043",
        'bold': True, 'border': 'all',
    },
    "Calculation": {
        'bg_color': "#e2efda", 'text_color': "#375623",
        'italic': True, 'border': 'all',
    },
    "Total": {
        'bg_color': "#d9e1f2", 'text_color': "#1f3864",
        'bold': True, 'border': 'all',
        'number_format': 'thousands',
    },
    "Warning": {
        'bg_color': "#ffeb9c", 'text_color': "#9c6500",
        'bold': True, 'italic': True,
    },
    "Explanatory": {
        'bg_color': "#f2f2f2", 'text_color': "#808080",
        'italic': True,
    },
}


class CellStylesDialog(QDialog):
    """Dialog showing clickable style preset buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cell Styles")
        self.setMinimumWidth(360)
        self._selected_style = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Click a style to apply to the selected cells:"))

        grid = QGridLayout()
        grid.setSpacing(4)
        cols = 3
        for i, (name, fmt) in enumerate(STYLE_PRESETS.items()):
            btn = QPushButton(name)
            bg = fmt.get('bg_color', '#ffffff')
            fg = fmt.get('text_color', '#000000')
            bold = 'bold' if fmt.get('bold') else 'normal'
            btn.setStyleSheet(
                f"QPushButton {{ background: {bg}; color: {fg}; "
                f"font-weight: {bold}; border: 1px solid #d0d0d0; "
                f"padding: 6px 12px; text-align: left; }}"
                f"QPushButton:hover {{ border: 2px solid #1a73e8; }}")
            btn.clicked.connect(lambda checked=False, n=name: self._select(n))
            grid.addWidget(btn, i // cols, i % cols)

        layout.addLayout(grid)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select(self, name):
        self._selected_style = name
        self.accept()

    def get_style(self):
        """Return the selected style name, or None."""
        return self._selected_style

    @staticmethod
    def get_format_dict(name):
        """Return the format dict for a style name."""
        return dict(STYLE_PRESETS.get(name, {}))