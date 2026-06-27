"""
Toolbar factory — builds the main QToolBar with all formatting and file actions.
Google Sheets style: flat, compact, text-based icons with subtle hover.
Returns a dict of actions/widgets for the main window to reference.
"""
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QFont, QColor, QIcon, QPixmap, QPainter, QPen
from PyQt6.QtWidgets import (
    QToolBar, QStyle, QComboBox, QPushButton, QLabel, QMenu, QWidget, QHBoxLayout
)
from . import qt_constants as C


def _make_icon(draw_fn, size=20):
    """Create an icon using a draw callback on a transparent pixmap."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_fn(painter, size)
    painter.end()
    return QIcon(pixmap)


def _text_icon(text, bold=False, italic=False, underline=False, color="#3c4043", size=11):
    """Create a simple text icon."""
    def draw(painter, sz):
        font = QFont("Arial", size)
        font.setBold(bold)
        font.setItalic(italic)
        font.setUnderline(underline)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.drawText(painter.device().rect(), Qt.AlignmentFlag.AlignCenter, text)
    return _make_icon(draw, 20)


def _draw_align_left(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.5)
    painter.setPen(pen)
    y = sz // 2
    painter.drawLine(3, y - 4, sz - 3, y - 4)
    painter.drawLine(3, y, int(sz * 0.65), y)
    painter.drawLine(3, y + 4, sz - 3, y + 4)

def _draw_align_center(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.5)
    painter.setPen(pen)
    y = sz // 2
    painter.drawLine(3, y - 4, sz - 3, y - 4)
    painter.drawLine(int(sz * 0.18), y, int(sz * 0.82), y)
    painter.drawLine(3, y + 4, sz - 3, y + 4)

def _draw_align_right(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.5)
    painter.setPen(pen)
    y = sz // 2
    painter.drawLine(3, y - 4, sz - 3, y - 4)
    painter.drawLine(int(sz * 0.35), y, sz - 3, y)
    painter.drawLine(3, y + 4, sz - 3, y + 4)

def _draw_fill_bucket(painter, sz):
    pen = QPen(QColor("#e8420d"), 1.5)
    painter.setPen(pen)
    painter.setBrush(QColor("#fbbc04"))
    painter.drawRect(4, 4, sz - 8, sz - 10)
    painter.setBrush(QColor("#e8420d"))
    painter.drawRect(4, 4, sz - 8, 3)

def _draw_border_icon(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.5)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(3, 3, sz - 6, sz - 6)

def _draw_merge(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.5)
    painter.setPen(pen)
    painter.drawRect(3, 6, sz - 6, sz - 12)
    painter.drawLine(3, sz // 2, sz - 3, sz // 2)

def _draw_undo(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.8)
    painter.setPen(pen)
    cx, cy = sz // 2, sz // 2 + 2
    painter.drawArc(cx - 5, cy - 5, 10, 10, 0, -180 * 16)
    painter.drawLine(cx - 5, cy, cx - 5, cy - 5)
    painter.drawLine(cx - 5, cy - 5, cx - 8, cy - 2)

def _draw_redo(painter, sz):
    pen = QPen(QColor("#3c4043"), 1.8)
    painter.setPen(pen)
    cx, cy = sz // 2, sz // 2 + 2
    painter.drawArc(cx - 5, cy - 5, 10, 10, 0, 180 * 16)
    painter.drawLine(cx + 5, cy, cx + 5, cy - 5)
    painter.drawLine(cx + 5, cy - 5, cx + 8, cy - 2)

def _draw_text_color(painter, sz):
    font = QFont("Arial", 11)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#3c4043"))
    painter.drawText(painter.device().rect(), Qt.AlignmentFlag.AlignCenter, "A")
    pen = QPen(QColor("#e8420d"), 2)
    painter.setPen(pen)
    painter.drawLine(4, sz - 4, sz - 4, sz - 4)

def _draw_percent(painter, sz):
    font = QFont("Arial", 10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#3c4043"))
    painter.drawText(painter.device().rect(), Qt.AlignmentFlag.AlignCenter, "%")

def _draw_decimal(painter, sz):
    font = QFont("Arial", 9)
    painter.setFont(font)
    painter.setPen(QColor("#3c4043"))
    painter.drawText(painter.device().rect(), Qt.AlignmentFlag.AlignCenter, ".00")


def create_toolbar(main_window):
    tb = main_window.addToolBar("Main")
    tb.setMovable(False)
    tb.setIconSize(QSize(18, 18))
    tb.layout().setSpacing(0)

    actions = {}

    # ── Undo / Redo ──
    a = QAction(_make_icon(_draw_undo), "Undo", main_window)
    a.setShortcut(QKeySequence("Ctrl+Z"))
    a.triggered.connect(main_window.on_undo)
    tb.addAction(a)
    actions['undo'] = a

    a = QAction(_make_icon(_draw_redo), "Redo", main_window)
    a.setShortcut(QKeySequence("Ctrl+Y"))
    a.triggered.connect(main_window.on_redo)
    tb.addAction(a)
    actions['redo'] = a

    tb.addSeparator()

    # ── Font family (display only, Google Sheets has this) ──
    font_combo = QComboBox()
    font_combo.addItem("Arial")
    font_combo.addItem("Roboto")
    font_combo.addItem("Times New Roman")
    font_combo.addItem("Courier New")
    font_combo.addItem("Georgia")
    font_combo.addItem("Calibri")
    font_combo.setFixedWidth(110)
    font_combo.setToolTip("Font")
    font_combo.currentTextChanged.connect(
        lambda text: main_window.apply_format({'font_family': text}))
    tb.addWidget(font_combo)
    actions['font_family'] = font_combo

    # ── Font size ──
    size_combo = QComboBox()
    size_combo.setEditable(True)
    for s in [6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 28, 36]:
        size_combo.addItem(str(s), s)
    size_combo.setCurrentText("11")
    size_combo.setFixedWidth(48)
    size_combo.setToolTip("Font size")

    def _on_font_size(text):
        try:
            main_window.apply_format({'font_size': int(text)})
        except ValueError:
            pass
    size_combo.currentTextChanged.connect(_on_font_size)
    tb.addWidget(size_combo)
    actions['font_size'] = size_combo

    tb.addSeparator()

    # ── Bold / Italic / Underline ──
    a = QAction(_text_icon("B", bold=True), "Bold", main_window)
    a.setShortcut(QKeySequence("Ctrl+B"))
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'bold': checked}))
    tb.addAction(a)
    actions['bold'] = a

    a = QAction(_text_icon("I", italic=True), "Italic", main_window)
    a.setShortcut(QKeySequence("Ctrl+I"))
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'italic': checked}))
    tb.addAction(a)
    actions['italic'] = a

    a = QAction(_text_icon("U", underline=True), "Underline", main_window)
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'underline': checked}))
    tb.addAction(a)
    actions['underline'] = a

    # Strikethrough
    a = QAction(_text_icon("S", color="#5f6368"), "Strikethrough", main_window)
    a.setCheckable(True)
    a.triggered.connect(main_window.toggle_strikethrough)
    tb.addAction(a)
    actions['strikethrough'] = a

    tb.addSeparator()

    # ── Indent ──
    a = QAction(_text_icon("\u2192", size=10), "Increase Indent", main_window)
    a.triggered.connect(main_window.increase_indent)
    tb.addAction(a)
    actions['indent_increase'] = a

    a = QAction(_text_icon("\u2190", size=10), "Decrease Indent", main_window)
    a.triggered.connect(main_window.decrease_indent)
    tb.addAction(a)
    actions['indent_decrease'] = a

    tb.addSeparator()

    # ── Text color / Fill color ──
    a = QAction(_make_icon(_draw_text_color), "Text Color", main_window)
    a.triggered.connect(main_window.on_text_color)
    tb.addAction(a)
    actions['text_color'] = a

    a = QAction(_make_icon(_draw_fill_bucket), "Fill Color", main_window)
    a.triggered.connect(main_window.on_bg_color)
    tb.addAction(a)
    actions['bg_color'] = a

    tb.addSeparator()

    # ── Borders ──
    a = QAction(_make_icon(_draw_border_icon), "Borders", main_window)
    a.setCheckable(False)
    border_menu = QMenu(main_window)
    a.setMenu(border_menu)
    tb.addAction(a)
    actions['borders'] = a

    border_options = [
        ("All Borders", 'all'),
        ("Outline", 'outline'),
        ("Bottom Border", 'bottom'),
        ("Top Border", 'top'),
        ("Left Border", 'left'),
        ("Right Border", 'right'),
        ("No Borders", None),
    ]
    for label, btype in border_options:
        act = QAction(label, main_window)
        act.triggered.connect(lambda checked=False, bt=btype: main_window.apply_format({'border': bt}))
        border_menu.addAction(act)

    tb.addSeparator()

    # ── Alignment ──
    a = QAction(_make_icon(_draw_align_left), "Align Left", main_window)
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'align': 'left'}))
    tb.addAction(a)
    actions['align_left'] = a

    a = QAction(_make_icon(_draw_align_center), "Align Center", main_window)
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'align': 'center'}))
    tb.addAction(a)
    actions['align_center'] = a

    a = QAction(_make_icon(_draw_align_right), "Align Right", main_window)
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'align': 'right'}))
    tb.addAction(a)
    actions['align_right'] = a

    tb.addSeparator()

    # ── Number format: currency / percent / decimals ──
    a = QAction(_text_icon("$", bold=True), "Format as Currency", main_window)
    a.triggered.connect(lambda: main_window.apply_format({'number_format': 'currency'}))
    tb.addAction(a)
    actions['currency'] = a

    a = QAction(_make_icon(_draw_percent), "Format as Percent", main_window)
    a.triggered.connect(lambda: main_window.apply_format({'number_format': 'percent'}))
    tb.addAction(a)
    actions['percent'] = a

    a = QAction(_make_icon(_draw_decimal), "Two Decimals", main_window)
    a.triggered.connect(lambda: main_window.apply_format({'number_format': 'float2'}))
    tb.addAction(a)
    actions['decimal'] = a

    # ── Wrap text ──
    a = QAction(_text_icon("\u21b5", size=11), "Wrap Text", main_window)
    a.setCheckable(True)
    a.triggered.connect(lambda checked: main_window.apply_format({'wrap_text': checked}))
    tb.addAction(a)
    actions['wrap_text'] = a

    tb.addSeparator()

    # ── Freeze ──
    a = QAction("Freeze", main_window)
    a.setToolTip("Freeze rows/columns")
    a.setCheckable(True)
    a.triggered.connect(main_window.toggle_freeze_row)
    tb.addAction(a)
    actions['freeze_row'] = a

    tb.addSeparator()

    # ── Conditional formatting ──
    a = QAction(_text_icon("CF", bold=True, size=8), "Conditional Format", main_window)
    a.triggered.connect(main_window.show_conditional_format_dialog)
    tb.addAction(a)
    actions['cond_format'] = a

    # ── Merge cells ──
    a = QAction(_make_icon(_draw_merge), "Merge Cells", main_window)
    a.setToolTip("Merge selected cells")
    a.triggered.connect(main_window.toggle_merge)
    tb.addAction(a)
    actions['merge'] = a

    # ── Format painter ──
    a = QAction(_text_icon("\u1f3a8", size=10), "Format Painter", main_window)
    a.setToolTip("Copy formatting from current cell")
    a.triggered.connect(main_window.toggle_format_painter)
    tb.addAction(a)
    actions['format_painter'] = a

    # ── AutoSum ──
    a = QAction(_text_icon("\u03a3", bold=True), "AutoSum", main_window)
    a.setToolTip("Insert =SUM() for adjacent data")
    a.triggered.connect(main_window.autosum)
    tb.addAction(a)
    actions['autosum'] = a

    # ── Insert Function ──
    a = QAction(_text_icon("fx", italic=True, size=9), "Insert Function", main_window)
    a.setToolTip("Browse and insert a function")
    a.triggered.connect(main_window.show_insert_function_dialog)
    tb.addAction(a)
    actions['insert_function'] = a

    tb.addSeparator()

    # ── Gridlines toggle ──
    a = QAction(_text_icon("#", size=11), "Toggle Gridlines", main_window)
    a.setCheckable(True)
    a.setChecked(True)
    a.triggered.connect(main_window.toggle_gridlines)
    tb.addAction(a)
    actions['gridlines'] = a

    # ── Dark mode ──
    a = QAction(_text_icon("\u25d0", size=12), "Dark Mode", main_window)
    a.setCheckable(True)
    a.triggered.connect(main_window.toggle_theme)
    tb.addAction(a)
    actions['dark_mode'] = a

    return actions