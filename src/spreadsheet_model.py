"""
QAbstractTableModel for the virtual spreadsheet grid.
Returns cell data, formatting roles, and handles editing through the undo stack.
"""
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt6.QtGui import QFont, QBrush, QColor
from . import qt_constants as C
from .formula_engine import format_value


SEARCH_HIGHLIGHT = QColor(255, 235, 59, 100)   # translucent yellow


def _interpolate_color(hex1, hex2, t):
    """Interpolate between two hex colors. t=0 returns hex1, t=1 returns hex2."""
    h1 = hex1.lstrip('#')
    h2 = hex2.lstrip('#')
    r1, g1, b1 = int(h1[0:2], 16), int(h1[2:4], 16), int(h1[4:6], 16)
    r2, g2, b2 = int(h2[0:2], 16), int(h2[2:4], 16), int(h2[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return QColor(r, g, b)


class SpreadsheetModel(QAbstractTableModel):
    def __init__(self, worksheet, undo_stack, parent=None):
        super().__init__(parent)
        self.worksheet = worksheet
        self.undo_stack = undo_stack
        self._rows = 10000
        self._cols = 1000
        self.search_matches = set()       # {(row, col)}
        self.search_active = False
        self.show_formulas = False         # toggle: show formula text instead of values
        self._cond_cache = {}              # {rule_index: {min, max, median}}

    # ── required overrides ──

    def rowCount(self, parent=QModelIndex()):
        return self._rows

    def columnCount(self, parent=QModelIndex()):
        return self._cols

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return C.ItemIsEnabled | C.ItemIsSelectable | C.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            from .formula_engine import col_index_to_letters
            label = col_index_to_letters(section)
            # Show filter arrow when a filter is active on this column
            if hasattr(self.worksheet, 'filters') and section in self.worksheet.filters:
                label += " \u25bc"
            return label
        else:
            return str(section + 1)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        cell = self.worksheet.get_cell_or_none(row, col)

        if cell is None:
            if role == C.BackgroundRole and self.search_active and (row, col) in self.search_matches:
                return QBrush(SEARCH_HIGHLIGHT)
            return None

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.ToolTipRole:
            if self.show_formulas and cell.is_formula():
                return cell.raw
            return cell.display_value()

        if role == C.EditRole:
            return cell.raw

        if role == C.FontRole:
            return self._font_for(cell)

        if role == C.BackgroundRole:
            if self.search_active and (row, col) in self.search_matches:
                return QBrush(SEARCH_HIGHLIGHT)
            cond_bg = self._conditional_bg_for(row, col)
            if cond_bg:
                return QBrush(cond_bg)
            if cell.fmt.bg_color:
                return QBrush(QColor(cell.fmt.bg_color))
            return None

        if role == C.ForegroundRole:
            if cell.fmt.text_color:
                return QBrush(QColor(cell.fmt.text_color))
            return None

        if role == C.TextAlignmentRole:
            return self._alignment_for(cell)

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole:
            return False
        from .undo_commands import EditCellCommand
        row, col = index.row(), index.column()
        old = self.worksheet.get_cell(row, col).raw
        if old == value:
            return False
        cmd = EditCellCommand(self, row, col, old, value)
        self.undo_stack.push(cmd)
        return True

    # ── public helpers ──

    def set_worksheet(self, worksheet):
        self.beginResetModel()
        self.worksheet = worksheet
        self.search_matches.clear()
        self.search_active = False
        self.endResetModel()
        self.rebuild_conditional_cache()

    def set_search_matches(self, matches):
        old = set(self.search_matches)
        self.search_matches = set(matches)
        self.search_active = len(matches) > 0
        all_cells = old | self.search_matches
        for (r, c) in all_cells:
            idx = self.index(r, c)
            self.dataChanged.emit(idx, idx, [C.BackgroundRole])

    def clear_search(self):
        if self.search_matches:
            old = set(self.search_matches)
            self.search_matches.clear()
            self.search_active = False
            for (r, c) in old:
                idx = self.index(r, c)
                self.dataChanged.emit(idx, idx, [C.BackgroundRole])

    def notify_cell(self, row, col):
        idx = self.index(row, col)
        self.dataChanged.emit(idx, idx)

    def notify_range(self, top, left, bottom, right):
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))

    def notify_all(self):
        self.dataChanged.emit(self.index(0, 0),
                              self.index(self._rows - 1, self._cols - 1))

    def recalc_and_notify(self):
        changed = self.worksheet.recalc()
        self.rebuild_conditional_cache()
        for (r, c) in changed:
            self.dataChanged.emit(self.index(r, c), self.index(r, c))

    def rebuild_conditional_cache(self):
        """Recompute min/max/median for each conditional rule's range."""
        self._cond_cache = {}
        sheet = self.worksheet
        rules = getattr(sheet, 'conditional_rules', [])
        for i, rule in enumerate(rules):
            values = []
            for r in range(rule.top, rule.bottom + 1):
                for c in range(rule.left, rule.right + 1):
                    cell = sheet.get_cell_or_none(r, c)
                    if cell and isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                        values.append(cell.value)
            if values:
                sorted_vals = sorted(values)
                self._cond_cache[i] = {
                    'min': sorted_vals[0],
                    'max': sorted_vals[-1],
                    'median': sorted_vals[len(sorted_vals) // 2],
                }

    def _conditional_bg_for(self, row, col):
        """Compute conditional background color for a cell (color scale only)."""
        sheet = self.worksheet
        rules = getattr(sheet, 'conditional_rules', [])
        for i, rule in enumerate(rules):
            if not rule.contains(row, col):
                continue
            if rule.rule_type != 'color_scale':
                continue
            cache = self._cond_cache.get(i)
            if not cache:
                continue
            cell = sheet.get_cell_or_none(row, col)
            if not cell or not isinstance(cell.value, (int, float)) or isinstance(cell.value, bool):
                continue
            val = cell.value
            mn, mx, med = cache['min'], cache['max'], cache['median']
            if mx == mn:
                return QColor(rule.mid_color)
            if val <= mn:
                return QColor(rule.min_color)
            if val >= mx:
                return QColor(rule.max_color)
            if val <= med:
                t = (val - mn) / (med - mn) if med > mn else 0
                return _interpolate_color(rule.min_color, rule.mid_color, t)
            t = (val - med) / (mx - med) if mx > med else 1
            return _interpolate_color(rule.mid_color, rule.max_color, t)
        return None

    def data_bar_fraction(self, row, col):
        """Return (fraction, color_hex) for a data bar rule, or None."""
        sheet = self.worksheet
        rules = getattr(sheet, 'conditional_rules', [])
        for i, rule in enumerate(rules):
            if not rule.contains(row, col):
                continue
            if rule.rule_type != 'data_bar':
                continue
            cache = self._cond_cache.get(i)
            if not cache:
                continue
            cell = sheet.get_cell_or_none(row, col)
            if not cell or not isinstance(cell.value, (int, float)) or isinstance(cell.value, bool):
                continue
            val = cell.value
            mn, mx = cache['min'], cache['max']
            frac = 0.0 if mx == mn else (val - mn) / (mx - mn)
            return max(0.0, min(1.0, frac)), rule.bar_color
        return None

    def apply_format_to_range(self, top, left, bottom, right, fmt_dict):
        """Apply formatting dict to every cell in the rectangular range."""
        from .undo_commands import FormatCommand
        cells = []
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                cells.append((r, c))
        cmd = FormatCommand(self, cells, fmt_dict)
        self.undo_stack.push(cmd)

    # ── internals ──

    def _font_for(self, cell):
        family = cell.fmt.font_family or ("Segoe UI" if _is_windows() else "SF Pro Text")
        f = QFont(family, cell.fmt.font_size or 11)
        f.setBold(cell.fmt.bold)
        f.setItalic(cell.fmt.italic)
        f.setUnderline(cell.fmt.underline)
        f.setStrikeOut(cell.fmt.strikethrough)
        return f

    def _alignment_for(self, cell):
        a = C.AlignVCenter
        if cell.fmt.wrap_text:
            a |= Qt.TextFlag.TextWordWrap
        if cell.fmt.align == 'center':
            a |= C.AlignCenter
        elif cell.fmt.align == 'right':
            a |= C.AlignRight
        elif cell.fmt.align == 'left':
            a |= C.AlignLeft
        else:
            # default: numbers right, text left
            v = cell.value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                a |= C.AlignRight
            else:
                a |= C.AlignLeft
        # Indent is handled in the delegate paint, not via alignment flag
        return int(a)


def _is_windows():
    import sys
    return sys.platform.startswith('win')