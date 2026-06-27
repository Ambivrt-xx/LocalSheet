"""
SpreadsheetFeaturesMixin — additional everyday spreadsheet features:
  • Fill Down (Ctrl+D) / Fill Right (Ctrl+R)
  • Paste Special (values only, transpose)
  • Remove Duplicates
  • Go To (Ctrl+G)
  • Show/Hide Formulas (Ctrl+`)
"""
import re
import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox,
    QButtonGroup, QLabel, QInputDialog
)
from . import undo_commands as UC


class PasteSpecialDialog(QDialog):
    """Dialog for choosing paste special mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paste Special")
        self.setMinimumWidth(260)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Paste:"))

        self.group = QButtonGroup(self)
        self.rb_all = QRadioButton("All")
        self.rb_values = QRadioButton("Values only")
        self.rb_transpose = QRadioButton("Transpose")
        self.rb_all.setChecked(True)

        for rb in (self.rb_all, self.rb_values, self.rb_transpose):
            self.group.addButton(rb)
            layout.addWidget(rb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_mode(self):
        if self.rb_values.isChecked():
            return 'values'
        if self.rb_transpose.isChecked():
            return 'transpose'
        return 'all'


class SpreadsheetFeaturesMixin:
    """Mixin providing additional spreadsheet features for MainWindow."""

    # ── Fill Down / Fill Right ──

    def fill_down(self):
        """Copy the top row's value down through the selection."""
        selection = self.view.selectionModel().selection()
        if not selection:
            idx = self.view.currentIndex()
            if idx.isValid():
                self._fill_direction(idx.row(), idx.column(), idx.row(), idx.column(),
                                     vertical=True)
            return
        for rng in selection:
            self._fill_direction(rng.top(), rng.left(), rng.bottom(), rng.right(),
                                vertical=True)

    def fill_right(self):
        """Copy the left column's value right through the selection."""
        selection = self.view.selectionModel().selection()
        if not selection:
            idx = self.view.currentIndex()
            if idx.isValid():
                self._fill_direction(idx.row(), idx.column(), idx.row(), idx.column(),
                                     vertical=False)
            return
        for rng in selection:
            self._fill_direction(rng.top(), rng.left(), rng.bottom(), rng.right(),
                                vertical=False)

    def _fill_direction(self, top, left, bottom, right, vertical):
        ws = self.model.worksheet
        changes = []
        if vertical:
            for c in range(left, right + 1):
                src = ws.get_cell_or_none(top, c)
                src_raw = src.raw if src else ""
                for r in range(top + 1, bottom + 1):
                    old = ws.get_cell(r, c).raw
                    if old != src_raw:
                        changes.append((r, c, old, src_raw))
        else:
            for r in range(top, bottom + 1):
                src = ws.get_cell_or_none(r, left)
                src_raw = src.raw if src else ""
                for c in range(left + 1, right + 1):
                    old = ws.get_cell(r, c).raw
                    if old != src_raw:
                        changes.append((r, c, old, src_raw))
        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)

    # ── Paste Special ──

    def paste_special(self):
        from PyQt6.QtWidgets import QApplication
        text = QApplication.clipboard().text()
        if not text:
            self.status.showMessage("Clipboard is empty", 3000)
            return
        dlg = PasteSpecialDialog(self)
        if not dlg.exec():
            return
        mode = dlg.get_mode()
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        start_row, start_col = idx.row(), idx.column()

        rows = [line.split('\t') for line in text.split('\n')]
        while rows and rows[-1] == ['']:
            rows.pop()

        if mode == 'transpose':
            max_cols = max(len(r) for r in rows) if rows else 0
            transposed = []
            for c in range(max_cols):
                new_row = []
                for r in range(len(rows)):
                    new_row.append(rows[r][c] if c < len(rows[r]) else "")
                transposed.append(new_row)
            rows = transposed

        changes = []
        for r, row_vals in enumerate(rows):
            for c, val in enumerate(row_vals):
                rr, cc = start_row + r, start_col + c
                old = self.model.worksheet.get_cell(rr, cc).raw
                if old != val:
                    changes.append((rr, cc, old, val))
        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)
            self.status.showMessage(f"Pasted {len(changes)} cells ({mode})", 3000)

    # ── Remove Duplicates ──

    def remove_duplicates(self):
        selection = self.view.selectionModel().selection()
        if not selection:
            self.status.showMessage("Select a range first", 3000)
            return
        ws = self.model.worksheet
        seen = set()
        rows_to_delete = []
        for rng in selection:
            for r in range(rng.top(), rng.bottom() + 1):
                key = tuple(
                    (ws.get_cell_or_none(r, c).raw
                     if ws.get_cell_or_none(r, c) else "")
                    for c in range(rng.left(), rng.right() + 1)
                )
                if key in seen:
                    rows_to_delete.append(r)
                else:
                    seen.add(key)
        if not rows_to_delete:
            self.status.showMessage("No duplicates found", 3000)
            return
        self.undo_stack.beginMacro(f"Remove {len(rows_to_delete)} duplicates")
        for r in sorted(rows_to_delete, reverse=True):
            self.undo_stack.push(UC.DeleteRowCommand(self.model, r))
        self.undo_stack.endMacro()

    # ── Go To ──

    def go_to(self):
        text, ok = QInputDialog.getText(self, "Go To", "Cell reference (e.g. A1, Z100):")
        if not ok or not text.strip():
            return
        m = re.match(r'^([A-Za-z]+)(\d+)$', text.strip())
        if not m:
            self.status.showMessage("Invalid reference", 3000)
            return
        letters, num = m.groups()
        col = 0
        for ch in letters.upper():
            col = col * 26 + (ord(ch) - ord('A') + 1)
        col -= 1
        row = int(num) - 1
        idx = self.model.index(row, col)
        self.view.setCurrentIndex(idx)
        self.view.scrollTo(idx)
        self.status.showMessage(
            f"Jumped to {letters.upper()}{num}", 2000)

    # ── Show / Hide Formulas ──

    def toggle_show_formulas(self):
        self.model.show_formulas = not self.model.show_formulas
        self.model.notify_all()
        self.status.showMessage(
            "Formulas " + ("visible" if self.model.show_formulas else "hidden"), 2000)