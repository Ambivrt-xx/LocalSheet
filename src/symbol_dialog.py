"""
InsertSymbolDialog — special character picker for inserting symbols into cells.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton, QDialogButtonBox,
    QLabel, QLineEdit
)


SYMBOL_SETS = {
    "Common": [
        "(c)", "(r)", "(tm)", "deg", "+/-", "x", "/", "!=", "~", "<=", ">=",
    ],
    "Currency": [
        "$", "EUR", "GBP", "JPY", "INR", "RUB", "KRW", "ILS", "PHP", "NGN",
    ],
    "Math": [
        "+/-", "x", "/", "!=", "~=", "<=", ">=", "sqrt", "sum", "int",
        "pi", "delta", "nabla", "in", "not in", "subset", "superset",
    ],
    "Arrows": [
        "->", "<-", "^", "v", "<->", "=>", "<=", "^", "v",
    ],
    "Greek": [
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
        "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi",
        "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    ],
}


class InsertSymbolDialog(QDialog):
    """Dialog for inserting special characters/symbols."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Symbol")
        self.setMinimumWidth(420)
        self._symbol = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        cat_row = QVBoxLayout()
        for cat_name, symbols in SYMBOL_SETS.items():
            cat_row.addWidget(QLabel(f"<b>{cat_name}</b>"))
            grid = QGridLayout()
            grid.setSpacing(2)
            cols = 12
            for i, sym in enumerate(symbols):
                btn = QPushButton(sym)
                btn.setFixedSize(30, 30)
                btn.setFont(QFont("Arial", 12))
                btn.clicked.connect(lambda checked=False, s=sym: self._pick(s))
                grid.addWidget(btn, i // cols, i % cols)
            cat_row.addLayout(grid)
            cat_row.addSpacing(8)
        layout.addLayout(cat_row)

        self.preview = QLineEdit()
        self.preview.setPlaceholderText("Selected symbol appears here")
        self.preview.setFont(QFont("Arial", 14))
        layout.addWidget(self.preview)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick(self, symbol):
        self._symbol = symbol
        self.preview.setText(symbol)

    def _on_accept(self):
        if self._symbol:
            self.accept()
        else:
            self.reject()

    def get_symbol(self):
        """Return the selected symbol, or None."""
        return self._symbol