"""
Dialog for adding conditional formatting rules to the selected cell range.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QPushButton, QButtonGroup, QColorDialog, QFrame
)
from .formula_engine import col_index_to_letters


class ColorButton(QPushButton):
    """A button that shows a color and opens a color picker when clicked."""

    def __init__(self, color, label, parent=None):
        super().__init__(parent)
        self._color = color
        self._label = label
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        self.setText(self._label)
        self.setStyleSheet(
            f"QPushButton {{ background: {self._color}; color: #ffffff; "
            f"border: 1px solid #555; border-radius: 4px; padding: 6px 12px; }} "
            f"QPushButton:hover {{ border: 2px solid #1a73e8; }}"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, self._label)
        if c.isValid():
            self._color = c.name()
            self._update_style()

    @property
    def color(self):
        return self._color


class ConditionalFormatDialog(QDialog):
    """Dialog to add conditional formatting to the selected range."""

    def __init__(self, top, left, bottom, right, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conditional Formatting")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # Range display
        range_str = f"{col_index_to_letters(left)}{top + 1}:{col_index_to_letters(right)}{bottom + 1}"
        layout.addWidget(QLabel(f"Apply to range: <b>{range_str}</b>"))

        # Rule type selection
        layout.addWidget(QLabel("Format type:"))
        self.type_group = QButtonGroup(self)
        self.rb_color_scale = QRadioButton("Color Scale (red to yellow to green)")
        self.rb_data_bar = QRadioButton("Data Bar (proportional blue bars)")
        self.rb_color_scale.setChecked(True)
        self.type_group.addButton(self.rb_color_scale)
        self.type_group.addButton(self.rb_data_bar)
        layout.addWidget(self.rb_color_scale)
        layout.addWidget(self.rb_data_bar)

        self.rb_color_scale.toggled.connect(self._update_visibility)

        # Color scale colors
        self.cs_frame = QFrame()
        cs_layout = QVBoxLayout(self.cs_frame)
        cs_layout.addWidget(QLabel("Color Scale Colors:"))
        colors_row = QHBoxLayout()
        self.btn_min_color = ColorButton("#f8696b", "Min (Red)")
        self.btn_mid_color = ColorButton("#ffeb84", "Mid (Yellow)")
        self.btn_max_color = ColorButton("#63be7b", "Max (Green)")
        colors_row.addWidget(self.btn_min_color)
        colors_row.addWidget(self.btn_mid_color)
        colors_row.addWidget(self.btn_max_color)
        cs_layout.addLayout(colors_row)
        layout.addWidget(self.cs_frame)

        # Data bar color
        self.db_frame = QFrame()
        db_layout = QVBoxLayout(self.db_frame)
        db_layout.addWidget(QLabel("Data Bar Color:"))
        db_row = QHBoxLayout()
        self.btn_bar_color = ColorButton("#638ec6", "Bar Color")
        db_row.addWidget(self.btn_bar_color)
        db_layout.addLayout(db_row)
        layout.addWidget(self.db_frame)

        self._update_visibility()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_apply)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _update_visibility(self):
        is_cs = self.rb_color_scale.isChecked()
        self.cs_frame.setVisible(is_cs)
        self.db_frame.setVisible(not is_cs)

    def get_rule_params(self):
        """Returns a dict with rule_type and colors."""
        if self.rb_color_scale.isChecked():
            return {
                'rule_type': 'color_scale',
                'min_color': self.btn_min_color.color,
                'mid_color': self.btn_mid_color.color,
                'max_color': self.btn_max_color.color,
            }
        else:
            return {
                'rule_type': 'data_bar',
                'bar_color': self.btn_bar_color.color,
            }