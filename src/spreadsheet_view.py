"""
SpreadsheetView — QTableView subclass with:
  • Enter/Tab spreadsheet-style navigation
  • Character-key to start editing
  • Right-click context menus (cells + headers)
  • Freeze panes (overlay QTableView)
  • Custom delegate for blue current-cell outline
"""
from PyQt6.QtCore import Qt, QModelIndex, QPoint, QEvent, QRect, QPointF, QItemSelection, QItemSelectionModel
from PyQt6.QtGui import QPen, QColor, QPainter, QKeyEvent, QKeySequence, QAction, QPolygonF, QFont
from PyQt6.QtWidgets import (
    QTableView, QMenu, QHeaderView, QFrame, QAbstractItemView,
    QStyledItemDelegate, QApplication, QComboBox, QPlainTextEdit
)
from . import qt_constants as C


class CellEditor(QPlainTextEdit):
    """Single-line editor that supports Alt+Enter / Shift+Enter for line breaks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabChangesFocus(True)


class CellDelegate(QStyledItemDelegate):
    """Draws a blue outline around the current cell (Google Sheets style)."""

    def __init__(self, view, parent=None):
        super().__init__(parent)
        self._view = view

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        # Data bar (conditional formatting)
        model = index.model()
        if hasattr(model, 'data_bar_fraction'):
            bar = model.data_bar_fraction(index.row(), index.column())
            if bar:
                frac, color_hex = bar
                c = QColor(color_hex)
                c.setAlpha(120)
                bar_w = max(int(option.rect.width() * frac), 1)
                painter.fillRect(QRect(option.rect.x(), option.rect.y(),
                                       bar_w, option.rect.height()), c)

        # Blue outline on the current cell
        current = self._view.currentIndex()
        if current.isValid() and current == index:
            painter.save()
            pen = QPen(QColor("#1a73e8"), 2)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRect(option.rect.x(), option.rect.y(),
                                   option.rect.width() - 1, option.rect.height() - 1))
            painter.restore()
            # Fill handle (small blue square at bottom-right corner)
            painter.save()
            handle_size = 6
            hx = option.rect.right() - handle_size + 1
            hy = option.rect.bottom() - handle_size + 1
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1a73e8"))
            painter.drawRect(hx, hy, handle_size, handle_size)
            painter.restore()

        # Note indicator (small red triangle in top-right corner)
        model = index.model()
        if hasattr(model, '_worksheet'):
            cell = model._worksheet.get_cell_or_none(index.row(), index.column())
            if cell and cell.note:
                painter.save()
                tri_size = 6
                x = option.rect.right() - tri_size
                y = option.rect.top()
                triangle = QPolygonF()
                triangle.append(QPointF(x, y))
                triangle.append(QPointF(x + tri_size, y))
                triangle.append(QPointF(x + tri_size, y + tri_size))
                painter.setBrush(QColor("#e8420d"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(triangle)
                painter.restore()

        # Dropdown arrow for data validation list cells
        if hasattr(model, '_worksheet'):
            ws = model._worksheet
            dv = ws.data_validations.get((index.row(), index.column()))
            if dv and dv.dv_type == 'list':
                painter.save()
                ar_x = option.rect.right() - 14
                ar_y = option.rect.center().y()
                painter.setBrush(QColor("#5f6368"))
                painter.setPen(Qt.PenStyle.NoPen)
                tri = QPolygonF()
                tri.append(QPointF(ar_x, ar_y - 3))
                tri.append(QPointF(ar_x + 8, ar_y - 3))
                tri.append(QPointF(ar_x + 4, ar_y + 3))
                painter.drawPolygon(tri)
                painter.restore()

        # Text overflow — spill text into adjacent empty cells
        if hasattr(model, '_worksheet'):
            ws = model._worksheet
            cell = ws.get_cell_or_none(index.row(), index.column())
            if cell and cell.raw and not cell.fmt.wrap_text:
                is_left = (cell.fmt.align == 'left' or
                           (cell.fmt.align is None and
                            not isinstance(cell.value, (int, float)) and
                            not isinstance(cell.value, bool)))
                if is_left:
                    text = cell.display_value()
                    if text:
                        font = index.data(Qt.ItemDataRole.FontRole)
                        if font:
                            painter.setFont(font)
                        fm = painter.fontMetrics()
                        text_w = fm.horizontalAdvance(text)
                        cell_w = option.rect.width()
                        if text_w > cell_w - 8:
                            overflow_w = cell_w
                            for c in range(index.column() + 1,
                                           min(index.column() + 30, model.columnCount())):
                                adj = ws.get_cell_or_none(index.row(), c)
                                if (adj and adj.raw) or ws.is_merged_covered(index.row(), c):
                                    break
                                overflow_w += self._view.columnWidth(c)
                                if overflow_w >= text_w + 8:
                                    break
                            if overflow_w > cell_w:
                                painter.save()
                                painter.setClipRect(option.rect.x(), option.rect.y(),
                                                    overflow_w, option.rect.height())
                                color = QColor(cell.fmt.text_color) if cell.fmt.text_color \
                                    else QColor("#3c4043")
                                painter.setPen(color)
                                rect = QRect(option.rect.x(), option.rect.y(),
                                              overflow_w, option.rect.height())
                                painter.drawText(
                                    rect.adjusted(4, 0, -2, 0),
                                    int(Qt.AlignmentFlag.AlignVCenter |
                                        Qt.AlignmentFlag.AlignLeft), text)
                                painter.restore()

        # Text rotation (vertical / angled text)
        if hasattr(model, '_worksheet'):
            ws = model._worksheet
            cell = ws.get_cell_or_none(index.row(), index.column())
            if cell and cell.raw and cell.fmt.text_rotation:
                rotation = cell.fmt.text_rotation
                text = cell.display_value()
                if text:
                    painter.save()
                    painter.translate(option.rect.center())
                    if rotation == 255:
                        # Stacked text — draw each character on its own line
                        painter.restore()
                    elif rotation == 90:
                        painter.rotate(-90)
                        color = QColor(cell.fmt.text_color) if cell.fmt.text_color else QColor("#3c4043")
                        painter.setPen(color)
                        painter.drawText(
                            QRect(-option.rect.height() // 2, -option.rect.width() // 2,
                                  option.rect.height(), option.rect.width()),
                            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter), text)
                    else:
                        painter.rotate(-rotation)
                        color = QColor(cell.fmt.text_color) if cell.fmt.text_color else QColor("#3c4043")
                        painter.setPen(color)
                        painter.drawText(
                            QRect(-option.rect.width(), -option.rect.height() // 2,
                                  option.rect.width() * 2, option.rect.height()),
                            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter), text)
                    painter.restore()

    # ── Data validation dropdown editor ──

    def createEditor(self, parent, option, index):
        """Return a QComboBox for list-validated cells, CellEditor otherwise."""
        model = index.model()
        if hasattr(model, '_worksheet'):
            ws = model._worksheet
            dv = ws.data_validations.get((index.row(), index.column()))
            if dv and dv.dv_type == 'list':
                combo = QComboBox(parent)
                values = [v.strip() for v in dv.formula1.split(',')]
                if dv.allow_blank:
                    combo.addItem("")
                combo.addItems(values)
                return combo
        return CellEditor(parent)

    def setEditorData(self, editor, index):
        """Populate the editor with the current cell value."""
        if isinstance(editor, QComboBox):
            text = index.data(Qt.ItemDataRole.EditRole) or ""
            i = editor.findText(text)
            if i >= 0:
                editor.setCurrentIndex(i)
        elif isinstance(editor, QPlainTextEdit):
            editor.setPlainText(index.data(Qt.ItemDataRole.EditRole) or "")
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """Commit the editor value back to the model."""
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
        elif isinstance(editor, QPlainTextEdit):
            model.setData(index, editor.toPlainText(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def eventFilter(self, editor, event):
        """Intercept Alt+Enter / Shift+Enter to insert a line break in the editor."""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and \
               (mods & Qt.KeyboardModifier.AltModifier):
                if hasattr(editor, 'insertPlainText'):
                    editor.insertPlainText("\n")
                    event.accept()
                    return True
        return super().eventFilter(editor, event)


class SpreadsheetView(QTableView):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setModel(model)
        self._main_window = parent

        # Selection
        self.setSelectionBehavior(C.SelectItems)
        self.setSelectionMode(C.ExtendedSelection)

        # Edit triggers
        self.setEditTriggers(C.DoubleClicked | C.SelectedClicked | C.EditKeyPressed)

        # Horizontal header (column letters)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(C.Interactive)
        hh.setHighlightSections(True)
        hh.setMinimumSectionSize(40)
        hh.setDefaultSectionSize(100)
        hh.setSectionsMovable(True)

        # Vertical header (row numbers)
        vh = self.verticalHeader()
        vh.setSectionResizeMode(C.Interactive)
        vh.setHighlightSections(True)
        vh.setDefaultSectionSize(28)
        vh.setMinimumSectionSize(20)

        # Custom delegate
        self.setItemDelegate(CellDelegate(self, self))

        # Word wrap
        self.setWordWrap(True)

        # Zoom
        self._zoom = 1.0

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

        # Header context menus
        hh.customContextMenuRequested.connect(self._on_header_context_menu)
        hh.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        vh.customContextMenuRequested.connect(self._on_row_header_context_menu)
        vh.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Freeze pane overlay
        self._frozen_row_count = 0
        self._frozen_col_count = 0
        self._frozen_view = QTableView(self)
        self._frozen_view.setModel(model)
        self._frozen_view.setSelectionModel(self.selectionModel())
        self._frozen_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._frozen_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._frozen_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._frozen_view.horizontalHeader().hide()
        self._frozen_view.verticalHeader().hide()
        self._frozen_view.setFrameStyle(QFrame.Shape.NoFrame)
        self._frozen_view.setItemDelegate(CellDelegate(self._frozen_view, self))
        self._frozen_view.setWordWrap(True)
        self._frozen_view.hide()

        # Sync column widths and scrolling
        hh.sectionResized.connect(self._on_h_section_resized)
        vh.sectionResized.connect(self._on_v_section_resized)
        self.horizontalScrollBar().valueChanged.connect(
            self._frozen_view.horizontalScrollBar().setValue)
        self._frozen_view.horizontalScrollBar().valueChanged.connect(
            self.horizontalScrollBar().setValue)

        # Double-click header to auto-fit
        hh.sectionDoubleClicked.connect(self._on_header_double_clicked)
        vh.sectionDoubleClicked.connect(self._on_vheader_double_clicked)

        self._update_frozen_geometry()

        # Auto-fill drag state
        self._filling = False
        self._fill_start_idx = QModelIndex()
        self._fill_end_idx = QModelIndex()
        self._fill_rect = None
        self.setViewportMargins(0, 0, 0, 0)

        # Enable drag-and-drop for file opening
        self.setAcceptDrops(True)

    # ── Freeze panes ──

    def set_frozen_rows(self, n):
        self._frozen_row_count = n
        model = self.model()
        if model:
            for r in range(model.rowCount()):
                self._frozen_view.setRowHidden(r, r >= n)
        self._update_frozen_geometry()

    def set_frozen_cols(self, n):
        self._frozen_col_count = n
        model = self.model()
        if model:
            for c in range(model.columnCount()):
                self._frozen_view.setColumnHidden(c, c >= n)
        self._update_frozen_geometry()

    def _frozen_height(self):
        return sum(self.rowHeight(r) for r in range(self._frozen_row_count))

    def _frozen_width(self):
        return sum(self.columnWidth(c) for c in range(self._frozen_col_count))

    def _update_frozen_geometry(self):
        total_h = self._frozen_height()
        total_w = self._frozen_width()
        if total_h == 0 and total_w == 0:
            self._frozen_view.hide()
            self.setViewportMargins(0, 0, 0, 0)
            return
        self._frozen_view.show()
        frame = self.frameWidth()
        vh_w = self.verticalHeader().width() if self.verticalHeader().isVisible() else 0
        hh_h = self.horizontalHeader().height() if self.horizontalHeader().isVisible() else 0
        x = frame + vh_w
        y = frame + hh_h

        if total_w > 0 and total_h > 0:
            w = total_w
            h = total_h
        elif total_h > 0:
            w = self.viewport().width()
            h = total_h
        else:
            w = total_w
            h = self.viewport().height()

        self._frozen_view.setGeometry(x, y, w, h)
        self.setViewportMargins(total_w, total_h, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_frozen_geometry()

    def _on_h_section_resized(self, col, old, new):
        self._frozen_view.setColumnWidth(col, new)
        self._update_frozen_geometry()

    def _on_v_section_resized(self, row, old, new):
        self._frozen_view.setRowHeight(row, new)
        self._update_frozen_geometry()

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        self._update_frozen_geometry()

    # ── Merged cell spans ──

    def refresh_spans(self):
        """Apply QTableView spans for all merged cell ranges in the worksheet."""
        model = self.model()
        if not model or not hasattr(model, '_worksheet'):
            return
        # Clear existing spans by resetting the grid size
        self.clearSpans()
        ws = model._worksheet
        for (r1, c1, r2, c2) in ws.merged_cells:
            self.setSpan(r1, c1, r2 - r1 + 1, c2 - c1 + 1)

    # ── Auto-fill drag ──

    def _fill_handle_rect(self, index):
        """Return the fill-handle rect for a visible cell index, or None."""
        if not index.isValid():
            return None
        vr = self.visualRect(index)
        if not vr.isValid() or self.isIndexHidden(index):
            return None
        handle_size = 6
        return QRect(vr.right() - handle_size + 1, vr.bottom() - handle_size + 1,
                     handle_size, handle_size)

    def mousePressEvent(self, event):
        # Format painter: click to apply formatting
        if (event.button() == Qt.MouseButton.LeftButton and
                self._main_window and
                getattr(self._main_window, '_format_painter_active', False)):
            idx = self.indexAt(event.pos())
            if idx.isValid():
                self._main_window._apply_format_painter(idx.row(), idx.column())
                event.accept()
                return
        # Ctrl+Click to open hyperlink
        if (event.button() == Qt.MouseButton.LeftButton and
                event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            idx = self.indexAt(event.pos())
            if idx.isValid() and self._main_window:
                self._main_window.open_hyperlink(idx.row(), idx.column())
                event.accept()
                return
        # Check if press is on the fill handle of the current cell
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.currentIndex()
            handle = self._fill_handle_rect(idx)
            if handle and handle.contains(event.pos()):
                self._filling = True
                self._fill_start_idx = idx
                self._fill_end_idx = idx
                self._fill_rect = self.visualRect(idx)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._filling:
            # Determine target cell under cursor — expand in one axis only
            target = self.indexAt(event.pos())
            if not target.isValid():
                return super().mouseMoveEvent(event)
            sr, sc = self._fill_start_idx.row(), self._fill_start_idx.column()
            tr, tc = target.row(), target.column()
            # Choose axis with the larger delta
            dr = abs(tr - sr)
            dc = abs(tc - sc)
            if dr >= dc:
                tc = sc
            else:
                tr = sr
            target = self.model().index(tr, tc)
            self._fill_end_idx = target
            top = min(sr, tr)
            bottom = max(sr, tr)
            left = min(sc, tc)
            right = max(sc, tc)
            self._fill_rect = QRect(
                self.visualRect(self.model().index(top, left)).topLeft(),
                self.visualRect(self.model().index(bottom, right)).bottomRight()
            )
            self.viewport().update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._filling:
            self._filling = False
            start = self._fill_start_idx
            end = self._fill_end_idx
            self._fill_rect = None
            self.viewport().update()
            if start.isValid() and end.isValid() and start != end:
                if self._main_window:
                    self._main_window.autofill(start.row(), start.column(),
                                               end.row(), end.column())
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._filling and self._fill_rect and self._fill_rect.isValid():
            painter = QPainter(self.viewport())
            pen = QPen(QColor("#1a73e8"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self._fill_rect.adjusted(0, 0, -1, -1))
            painter.end()

    def mouseDoubleClickEvent(self, event):
        """Double-click fill handle — auto-fill down to end of adjacent data."""
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.currentIndex()
            handle = self._fill_handle_rect(idx)
            if handle and handle.contains(event.pos()):
                if self._main_window:
                    self._main_window.autofill_down(idx.row(), idx.column())
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    # ── Navigation helpers ──

    def _find_edge(self, row, col, key):
        """Return (row, col) of the data edge in the given direction."""
        model = self.model()
        ws = model._worksheet if hasattr(model, '_worksheet') else None

        def is_empty(r, c):
            if r < 0 or r >= model.rowCount() or c < 0 or c >= model.columnCount():
                return True
            cell = ws.get_cell_or_none(r, c) if ws else None
            return not cell or not cell.raw

        cur_empty = is_empty(row, col)

        if key == Qt.Key.Key_Down:
            if cur_empty:
                r = row + 1
                while r < model.rowCount() and is_empty(r, col):
                    r += 1
                return min(r, model.rowCount() - 1), col
            r = row + 1
            while r < model.rowCount() and not is_empty(r, col):
                r += 1
            return r - 1, col

        if key == Qt.Key.Key_Up:
            if cur_empty:
                r = row - 1
                while r >= 0 and is_empty(r, col):
                    r -= 1
                return max(r, 0), col
            r = row - 1
            while r >= 0 and not is_empty(r, col):
                r -= 1
            return r + 1, col

        if key == Qt.Key.Key_Right:
            if cur_empty:
                c = col + 1
                while c < model.columnCount() and is_empty(row, c):
                    c += 1
                return row, min(c, model.columnCount() - 1)
            c = col + 1
            while c < model.columnCount() and not is_empty(row, c):
                c += 1
            return row, c - 1

        if key == Qt.Key.Key_Left:
            if cur_empty:
                c = col - 1
                while c >= 0 and is_empty(row, c):
                    c -= 1
                return row, max(c, 0)
            c = col - 1
            while c >= 0 and not is_empty(row, c):
                c -= 1
            return row, c + 1

        return row, col

    def _jump_to_edge(self, key):
        current = self.currentIndex()
        if not current.isValid():
            return
        r, c = self._find_edge(current.row(), current.column(), key)
        self.setCurrentIndex(self.model().index(r, c))

    def _select_to_edge(self, key):
        current = self.currentIndex()
        if not current.isValid():
            return
        r, c = self._find_edge(current.row(), current.column(), key)
        top = min(current.row(), r)
        bottom = max(current.row(), r)
        left = min(current.column(), c)
        right = max(current.column(), c)
        sel = QItemSelection(self.model().index(top, left),
                             self.model().index(bottom, right))
        self.selectionModel().select(sel, QItemSelectionModel.SelectionFlag.Select)
        self.selectionModel().setCurrentIndex(
            self.model().index(r, c),
            QItemSelectionModel.SelectionFlag.NoUpdate)

    def _last_used_cell(self):
        model = self.model()
        ws = model._worksheet if hasattr(model, '_worksheet') else None
        if not ws or not ws.cells:
            return (0, 0)
        return (max(r for r, _ in ws.cells), max(c for _, c in ws.cells))

    def _insert_value(self, value):
        if self.state() == C.EditingState:
            editor = QApplication.focusWidget()
            if editor and hasattr(editor, 'insertPlainText'):
                editor.insertPlainText(value)
            elif editor and hasattr(editor, 'insert'):
                editor.insert(value)
        else:
            idx = self.currentIndex()
            if idx.isValid():
                self.model().setData(idx, value, Qt.ItemDataRole.EditRole)

    # ── Key handling ──

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        # Enter — commit edit then move down; or start editing
        if key in (C.Key_Return, C.Key_Enter):
            if self.state() == C.EditingState:
                super().keyPressEvent(event)
                self._move_cursor(C.MoveDown, mods)
            else:
                self.edit(self.currentIndex())
            return

        # Tab — commit then move right; Shift+Tab moves left
        if key == C.Key_Tab:
            if self.state() == C.EditingState:
                super().keyPressEvent(event)
                self._move_cursor(C.MoveRight, mods)
            else:
                self._move_cursor(C.MoveRight, mods)
            return
        if key == C.Key_Backtab:
            if self.state() == C.EditingState:
                super().keyPressEvent(event)
            self._move_cursor(C.MoveLeft, mods)
            return

        # Escape — cancel edit
        if key == C.Key_Escape:
            if self.state() == C.EditingState:
                self.closeEditor(self._current_editor(), C.NoHint)
                return

        # Delete — clear selected cells
        if key == C.Key_Delete:
            if self.state() != C.EditingState:
                self._clear_selection()
                return

        # F2 — start editing
        if key == C.Key_F2:
            if self.state() != C.EditingState:
                self.edit(self.currentIndex())
            return

        # ── Alt+= for AutoSum ──
        if (mods & Qt.KeyboardModifier.AltModifier) and key == Qt.Key.Key_Equal:
            if self._main_window:
                self._main_window.autosum()
            event.accept()
            return

        # ── Ctrl shortcuts (not during editing) ──
        if not (mods & Qt.KeyboardModifier.AltModifier) and \
           (mods & Qt.KeyboardModifier.ControlModifier) and \
           self.state() != C.EditingState:
            # Ctrl+D — fill down
            if key == Qt.Key.Key_D and not (mods & Qt.KeyboardModifier.ShiftModifier):
                if self._main_window:
                    self._main_window.fill_down()
                event.accept()
                return
            # Ctrl+R — fill right
            if key == Qt.Key.Key_R and not (mods & Qt.KeyboardModifier.ShiftModifier):
                if self._main_window:
                    self._main_window.fill_right()
                event.accept()
                return
            # Ctrl+G — go to
            if key == Qt.Key.Key_G and not (mods & Qt.KeyboardModifier.ShiftModifier):
                if self._main_window:
                    self._main_window.go_to()
                event.accept()
                return
            # Ctrl+` — toggle show formulas
            if key == Qt.Key.Key_QuoteLeft:
                if self._main_window:
                    self._main_window.toggle_show_formulas()
                event.accept()
                return
            # Ctrl+; — insert date, Ctrl+Shift+; — insert time
            if key == Qt.Key.Key_Semicolon:
                import datetime
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    self._insert_value(datetime.datetime.now().strftime("%H:%M"))
                else:
                    self._insert_value(datetime.date.today().strftime("%Y-%m-%d"))
                event.accept()
                return
            # Ctrl+Arrow — jump to data edge (Shift extends selection)
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down,
                       Qt.Key.Key_Left, Qt.Key.Key_Right):
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    self._select_to_edge(key)
                else:
                    self._jump_to_edge(key)
                event.accept()
                return
            # Ctrl+Home — jump to A1
            if key == Qt.Key.Key_Home:
                self.setCurrentIndex(self.model().index(0, 0))
                event.accept()
                return
            # Ctrl+End — jump to last used cell
            if key == Qt.Key.Key_End:
                r, c = self._last_used_cell()
                self.setCurrentIndex(self.model().index(r, c))
                event.accept()
                return
            # Ctrl+1 — Format Cells dialog
            if key == Qt.Key.Key_1:
                if self._main_window:
                    self._main_window.show_format_dialog()
                event.accept()
                return
            # Ctrl+Shift+5 — Percent format (check before Ctrl+5)
            if key == Qt.Key.Key_5 and (mods & Qt.KeyboardModifier.ShiftModifier):
                self._main_window.apply_format({'number_format': 'percent'})
                event.accept()
                return
            # Ctrl+5 — Strikethrough toggle (no Shift)
            if key == Qt.Key.Key_5 and not (mods & Qt.KeyboardModifier.ShiftModifier):
                if self._main_window:
                    self._main_window.toggle_strikethrough()
                event.accept()
                return
            # Ctrl+Shift+L — Toggle filter
            if key == Qt.Key.Key_L and (mods & Qt.KeyboardModifier.ShiftModifier):
                if self._main_window:
                    self._main_window.toggle_filter()
                event.accept()
                return
            # Ctrl+Shift+V — Paste Special
            if key == Qt.Key.Key_V and (mods & Qt.KeyboardModifier.ShiftModifier):
                if self._main_window:
                    self._main_window.paste_special()
                event.accept()
                return

        # Character key — start editing with replacement
        if self.state() != C.EditingState:
            if event.text() and len(event.text()) == 1 and event.text().isprintable():
                if not (mods & Qt.KeyboardModifier.ControlModifier) and \
                   not (mods & Qt.KeyboardModifier.AltModifier):
                    idx = self.currentIndex()
                    if idx.isValid() and (self.flags(idx) & C.ItemIsEditable):
                        self.edit(idx)
                        editor = QApplication.focusWidget()
                        if editor and hasattr(editor, 'setText'):
                            editor.setText(event.text())
                            if hasattr(editor, 'end'):
                                editor.end(False)
                            elif hasattr(editor, 'setCursorPosition'):
                                editor.setCursorPosition(len(event.text()))
                        return

        super().keyPressEvent(event)

    def _current_editor(self):
        return QApplication.focusWidget()

    def _move_cursor(self, action, mods):
        new_idx = self.moveCursor(action, mods)
        if new_idx.isValid():
            self.setCurrentIndex(new_idx)

    def _clear_selection(self):
        if self._main_window:
            self._main_window.clear_selected_cells()

    # ── Context menus ──

    def _menu_act(self, menu, text, handler):
        act = QAction(text, self)
        act.triggered.connect(handler)
        menu.addAction(act)
        return act

    def _on_context_menu(self, pos):
        idx = self.indexAt(pos)
        if not idx.isValid():
            return
        mw = self._main_window
        menu = QMenu(self)
        if mw:
            self._menu_act(menu, "Copy", mw.on_copy)
            self._menu_act(menu, "Cut", mw.on_cut)
            self._menu_act(menu, "Paste", mw.on_paste)
        menu.addSeparator()
        self._menu_act(menu, "Insert Row Above", lambda: self._insert_row(idx.row()))
        self._menu_act(menu, "Insert Row Below", lambda: self._insert_row(idx.row() + 1))
        self._menu_act(menu, "Delete Row", lambda: self._delete_row(idx.row()))
        menu.addSeparator()
        self._menu_act(menu, "Insert Column Left", lambda: self._insert_col(idx.column()))
        self._menu_act(menu, "Insert Column Right", lambda: self._insert_col(idx.column() + 1))
        self._menu_act(menu, "Delete Column", lambda: self._delete_col(idx.column()))
        menu.addSeparator()
        self._menu_act(menu, "Clear Contents", lambda: self._clear_cells())
        if mw:
            self._menu_act(menu, "Add/Edit Note…", mw.edit_cell_note)
            self._menu_act(menu, "Format Cells…", mw.show_format_dialog)
        menu.exec(self.viewport().mapToGlobal(pos))

    def _on_row_header_context_menu(self, pos):
        vh = self.verticalHeader()
        row = vh.logicalIndexAt(pos)
        if row < 0:
            return
        menu = QMenu(self)
        self._menu_act(menu, "Insert Row Above", lambda: self._insert_row(row))
        self._menu_act(menu, "Insert Row Below", lambda: self._insert_row(row + 1))
        self._menu_act(menu, "Delete Row", lambda: self._delete_row(row))
        menu.addSeparator()
        self._menu_act(menu, "Hide Row", lambda: self.setRowHidden(row, True))
        self._menu_act(menu, "Unhide All Rows", self._unhide_all_rows)
        menu.addSeparator()
        self._menu_act(menu, "Auto-fit Row Height", lambda: self._autofit_row(row))
        menu.exec(vh.mapToGlobal(pos))

    def _on_header_context_menu(self, pos):
        hh = self.horizontalHeader()
        col = hh.logicalIndexAt(pos)
        if col < 0:
            return
        menu = QMenu(self)
        self._menu_act(menu, "Insert Column Left", lambda: self._insert_col(col))
        self._menu_act(menu, "Insert Column Right", lambda: self._insert_col(col + 1))
        self._menu_act(menu, "Delete Column", lambda: self._delete_col(col))
        menu.addSeparator()
        self._menu_act(menu, "Hide Column", lambda: self.setColumnHidden(col, True))
        self._menu_act(menu, "Unhide All Columns", self._unhide_all_cols)
        menu.addSeparator()
        self._menu_act(menu, "Auto-fit Column Width", lambda: self._autofit_col(col))
        self._menu_act(menu, "Auto-fit All Columns", self._autofit_all_cols)
        menu.addSeparator()
        self._menu_act(menu, "Filter by Values…", lambda: self._filter_column(col))
        self._menu_act(menu, "Clear Filter", self._clear_filter)
        menu.addSeparator()
        self._menu_act(menu, "Sort A \u2192 Z", lambda: self._sort_column(col, True))
        self._menu_act(menu, "Sort Z \u2192 A", lambda: self._sort_column(col, False))
        menu.exec(hh.mapToGlobal(pos))

    # ── Auto-fit ──

    def _autofit_col(self, col):
        if self._main_window:
            self._main_window.autofit_column(col)

    def _autofit_all_cols(self):
        if self._main_window:
            self._main_window.autofit_all_columns()

    def _autofit_row(self, row):
        if self._main_window:
            self._main_window.autofit_row(row)

    def _on_header_double_clicked(self, col):
        """Double-click column header border to auto-fit width."""
        self._autofit_col(col)

    def _on_vheader_double_clicked(self, row):
        """Double-click row header border to auto-fit height."""
        self._autofit_row(row)

    # ── Zoom ──

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._adjust_zoom(0.1)
            elif delta < 0:
                self._adjust_zoom(-0.1)
            event.accept()
            return
        super().wheelEvent(event)

    def _adjust_zoom(self, delta):
        new_zoom = max(0.5, min(3.0, self._zoom + delta))
        if new_zoom == self._zoom:
            return
        self._zoom = new_zoom
        base_row = 28
        base_col = 100
        new_row = max(16, int(base_row * new_zoom))
        new_col = max(30, int(base_col * new_zoom))
        self.verticalHeader().setDefaultSectionSize(new_row)
        self.horizontalHeader().setDefaultSectionSize(new_col)
        self._frozen_view.verticalHeader().setDefaultSectionSize(new_row)
        self._frozen_view.horizontalHeader().setDefaultSectionSize(new_col)

    def zoom_in(self):
        self._adjust_zoom(0.1)

    def zoom_out(self):
        self._adjust_zoom(-0.1)

    def zoom_reset(self):
        self._zoom = 1.0
        self.verticalHeader().setDefaultSectionSize(28)
        self.horizontalHeader().setDefaultSectionSize(100)
        self._frozen_view.verticalHeader().setDefaultSectionSize(28)
        self._frozen_view.horizontalHeader().setDefaultSectionSize(100)

    # ── Row/Col operation helpers ──

    def _insert_row(self, at):
        if self._main_window:
            self._main_window.insert_row(at)

    def _delete_row(self, row):
        if self._main_window:
            self._main_window.delete_row(row)

    def _insert_col(self, at):
        if self._main_window:
            self._main_window.insert_col(at)

    def _delete_col(self, col):
        if self._main_window:
            self._main_window.delete_col(col)

    def _clear_cells(self):
        if self._main_window:
            self._main_window.clear_selected_cells()

    def _format_dialog(self):
        if self._main_window:
            self._main_window.show_format_dialog()

    def _unhide_all_rows(self):
        model = self.model()
        for r in range(model.rowCount()):
            self.setRowHidden(r, False)

    def _unhide_all_cols(self):
        model = self.model()
        for c in range(model.columnCount()):
            self.setColumnHidden(c, False)

    def _filter_column(self, col):
        if self._main_window:
            self._main_window.filter_column(col)

    def _clear_filter(self):
        if self._main_window:
            self._main_window.clear_filter()

    def _sort_column(self, col, ascending):
        if self._main_window:
            self._main_window.sort_column(col, ascending)

    # ── Note hover tooltip ──

    def helpEvent(self, event):
        """Show cell note as a tooltip on hover."""
        if event.type() == QEvent.Type.ToolTip:
            idx = self.indexAt(event.pos())
            if idx.isValid():
                model = idx.model()
                if hasattr(model, '_worksheet'):
                    ws = model._worksheet
                    cell = ws.get_cell_or_none(idx.row(), idx.column())
                    if cell and cell.note:
                        from PyQt6.QtWidgets import QToolTip
                        QToolTip.showText(event.globalPos(), cell.note, self)
                        event.accept()
                        return
                    # Show hyperlink URL as tooltip
                    if cell and cell.hyperlink:
                        from PyQt6.QtWidgets import QToolTip
                        QToolTip.showText(event.globalPos(), cell.hyperlink, self)
                        event.accept()
                        return
                from PyQt6.QtWidgets import QToolTip
                QToolTip.hideText()
            event.ignore()
            return
        super().helpEvent(event)

    # ── Drag-and-drop file open ──

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.xlsx', '.csv')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.xlsx', '.csv')):
                    if self._main_window:
                        self._main_window.open_dropped_file(path)
                    event.acceptProposedAction()
                    return
        event.ignore()