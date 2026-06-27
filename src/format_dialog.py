"""
FormatCellsDialog — comprehensive formatting dialog with sections for
Font, Alignment, Number, Border, and Fill, applying all settings to the
selected range at once.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen, QPainter, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QComboBox, QCheckBox, QPushButton, QColorDialog, QDialogButtonBox,
    QGroupBox, QButtonGroup, QRadioButton, QLineEdit, QFrame
)

BORDER_STYLES = [
    (None, "No Borders"),
    ('all', "All Borders"),
    ('outline', "Outline"),
    ('grid', "Grid"),
    ('bottom', "Bottom"),
    ('top', "Top"),
    ('left', "Left"),
    ('right', "Right"),
]

NUMBER_FORMATS = [
    (None, "General"),
    ('int', "Integer (0)"),
    ('float2', "Two Decimals (0.00)"),
    ('thousands', "Thousands (1,234)"),
    ('currency', "Currency (\$0.00)"),
    ('percent', "Percent (0%)"),
    ('date', "Date (mm/dd/yyyy)"),
    ('time', "Time (hh:mm:ss)"),
    ('datetime', "Date & Time (mm/dd/yyyy hh:mm)"),
]

def _swatch(color_hex, size=22):
    btn = QPushButton()
    btn.setFixedSize(size, size)
    if color_hex:
        btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #999; border-radius: 3px;")
    else:
        btn.setStyleSheet("background: repeating-linear-gradient(45deg, #fff 0 4px, #ccc 4px 8px); border: 1px solid #999; border-radius: 3px;")
    return btn

class FormatCellsDialog(QDialog):
    def __init__(self, current_fmt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Format Cells")
        self.setMinimumWidth(420)
        self._fmt = current_fmt
        self._result = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        font_group = QGroupBox("Font")
        fg_layout = QGridLayout(font_group)
        fg_layout.addWidget(QLabel("Font family:"), 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["(default)", "Arial", "Calibri", "Roboto", "Times New Roman", "Courier New", "Georgia", "Verdana", "Tahoma"])
        if self._fmt.font_family:
            self.font_combo.setCurrentText(self._fmt.font_family)
        fg_layout.addWidget(self.font_combo, 0, 1)
        fg_layout.addWidget(QLabel("Size:"), 0, 2)
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        for s in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 28, 36]:
            self.size_combo.addItem(str(s), s)
        self.size_combo.setCurrentText(str(self._fmt.font_size))
        fg_layout.addWidget(self.size_combo, 0, 3)
        style_row = QHBoxLayout()
        self.bold_cb = QCheckBox("Bold")
        self.bold_cb.setChecked(self._fmt.bold)
        self.italic_cb = QCheckBox("Italic")
        self.italic_cb.setChecked(self._fmt.italic)
        self.underline_cb = QCheckBox("Underline")
        self.underline_cb.setChecked(self._fmt.underline)
        self.strike_cb = QCheckBox("Strikethrough")
        self.strike_cb.setChecked(self._fmt.strikethrough)
        style_row.addWidget(self.bold_cb)
        style_row.addWidget(self.italic_cb)
        style_row.addWidget(self.underline_cb)
        style_row.addWidget(self.strike_cb)
        style_row.addStretch()
        fg_layout.addLayout(style_row, 1, 0, 1, 4)
        fg_layout.addWidget(QLabel("Rotation:"), 3, 0)
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItem("None", 0)
        self.rotation_combo.addItem("45 deg", 45)
        self.rotation_combo.addItem("90 deg (vertical)", 90)
        self.rotation_combo.addItem("Stacked", 255)
        for i in range(self.rotation_combo.count()):
            if self.rotation_combo.itemData(i) == self._fmt.text_rotation:
                self.rotation_combo.setCurrentIndex(i)
                break
        fg_layout.addWidget(self.rotation_combo, 3, 1)
        fg_layout.addWidget(QLabel("Text color:"), 2, 0)
        self.text_color_btn = _swatch(self._fmt.text_color)
        self.text_color_btn.clicked.connect(self._pick_text_color)
        fg_layout.addWidget(self.text_color_btn, 2, 1)
        self._text_color = self._fmt.text_color
        layout.addWidget(font_group)
        align_group = QGroupBox("Alignment")
        ag_layout = QHBoxLayout(align_group)
        self.align_group = QButtonGroup(self)
        self.align_none = QRadioButton("Default")
        self.align_left = QRadioButton("Left")
        self.align_center = QRadioButton("Center")
        self.align_right = QRadioButton("Right")
        for rb in (self.align_none, self.align_left, self.align_center, self.align_right):
            self.align_group.addButton(rb)
            ag_layout.addWidget(rb)
        align_map = {None: self.align_none, 'left': self.align_left, 'center': self.align_center, 'right': self.align_right}
        align_map.get(self._fmt.align, self.align_none).setChecked(True)
        ag_layout.addStretch()
        self.wrap_cb = QCheckBox("Wrap text")
        self.wrap_cb.setChecked(self._fmt.wrap_text)
        ag_layout.addWidget(self.wrap_cb)
        indent_row = QHBoxLayout()
        indent_row.addWidget(QLabel("indent:"))
        self.indent_combo = QComboBox()
        for i in range(16):
            self.indent_combo.addItem(str(i), i)
        self.indent_combo.setCurrentIndex(min(self._fmt.indent, 15))
        indent_row.addWidget(self.indent_combo)
        ag_layout.addLayout(indent_row)
        layout.addWidget(align_group)
        num_group = QGroupBox("Number")
        ng_layout = QVBoxLayout(num_group)
        ng_row = QHBoxLayout()
        ng_row.addWidget(QLabel("Format:"))
        self.num_combo = QComboBox()
        for val, label in NUMBER_FORMATS:
            self.num_combo.addItem(label, val)
        idx = next((i for i, (v, _) in enumerate(NUMBER_FORMATS) if v == self._fmt.number_format), 0)
        self.num_combo.setCurrentIndex(idx)
        ng_row.addWidget(self.num_combo)
        ng_row.addStretch()
        ng_layout.addLayout(ng_row)
        cf_row = QHBoxLayout()
        cf_row.addWidget(QLabel("Custom:"))
        self.custom_fmt_input = QLineEdit(self._fmt.custom_format or "")
        self.custom_fmt_input.setPlaceholderText("#,##0.00;[Red]-#,##0.00")
        cf_row.addWidget(self.custom_fmt_input)
        ng_layout.addLayout(cf_row)
        layout.addWidget(num_group)
        border_group = QGroupBox("Border")
        bg_layout = QHBoxLayout(border_group)
        self.border_combo = QComboBox()
        for val, label in BORDER_STYLES:
            self.border_combo.addItem(label, val)
        idx = next((i for i, (v, _) in enumerate(BORDER_STYLES) if v == self._fmt.border), 0)
        self.border_combo.setCurrentIndex(idx)
        bg_layout.addWidget(self.border_combo)
        bg_layout.addStretch()
        layout.addWidget(border_group)
        fill_group = QGroupBox("Fill")
        fl_layout = QHBoxLayout(fill_group)
        fl_layout.addWidget(QLabel("Background color:"))
        self.bg_color_btn = _swatch(self._fmt.bg_color)
        self.bg_color_btn.clicked.connect(self._pick_bg_color)
        fl_layout.addWidget(self.bg_color_btn)
        self._bg_color = self._fmt.bg_color
        clear_bg = QPushButton("Clear")
        clear_bg.clicked.connect(self._clear_bg)
        fl_layout.addWidget(clear_bg)
        fl_layout.addStretch()
        layout.addWidget(fill_group)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pick_text_color(self):
        color = QColorDialog.getColor(QColor(self._text_color or "#000000"), self, "Text Color")
        if color.isValid():
            self._text_color = color.name()
            self.text_color_btn.setStyleSheet(f"background-color: {self._text_color}; border: 1px solid #999; border-radius: 3px;")

    def _pick_bg_color(self):
        color = QColorDialog.getColor(QColor(self._bg_color or "#ffffff"), self, "Fill Color")
        if color.isValid():
            self._bg_color = color.name()
            self.bg_color_btn.setStyleSheet(f"background-color: {self._bg_color}; border: 1px solid #999; border-radius: 3px;")

    def _clear_bg(self):
        self._bg_color = None
        self.bg_color_btn.setStyleSheet("background: repeating-linear-gradient(45deg, #fff 0 4px, #ccc 4px 8px); border: 1px solid #999; border-radius: 3px;")

    def _on_accept(self):
        fmt = {}
        ff = self.font_combo.currentText()
        fmt['font_family'] = ff if ff != "(default)" else None
        try:
            fmt['font_size'] = int(self.size_combo.currentText())
        except ValueError:
            pass
        fmt['bold'] = self.bold_cb.isChecked()
        fmt['italic'] = self.italic_cb.isChecked()
        fmt['underline'] = self.underline_cb.isChecked()
        fmt['strikethrough'] = self.strike_cb.isChecked()
        fmt['text_rotation'] = self.rotation_combo.currentData()
        fmt['text_color'] = self._text_color
        if self.align_left.isChecked():
            fmt['align'] = 'left'
        elif self.align_center.isChecked():
            fmt['align'] = 'center'
        elif self.align_right.isChecked():
            fmt['align'] = 'right'
        else:
            fmt['align'] = None
        fmt['wrap_text'] = self.wrap_cb.isChecked()
        fmt['indent'] = self.indent_combo.currentData()
        fmt['number_format'] = self.num_combo.currentData()
        custom = self.custom_fmt_input.text().strip()
        fmt['custom_format'] = custom if custom else None
        fmt['border'] = self.border_combo.currentData()
        fmt['bg_color'] = self._bg_color
        self._result = fmt
        self.accept()

    def get_format(self):
        return self._result
