"""
AdvancedFeaturesMixin — additional spreadsheet features for MainWindow:
  • AutoSum (Σ) — inserts =SUM(...) for adjacent numeric data
  • Drag-to-move cells — drag selection border to relocate
  • Right-drag fill options — copy vs fill series
  • Gridlines toggle
  • Group & outline rows/columns
  • Recent files list
  • Tab color for sheets
  • Hide/unhide sheets
  • Cell locking & sheet protection
  • Insert Function dialog
  • Insert Symbol
  • Insert Hyperlink
  • Insert Image
"""
import os
import webbrowser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QColorDialog, QMessageBox, QInputDialog
)
from . import qt_constants as C
from . import undo_commands as UC
from .formula_engine import col_index_to_letters, col_letters_to_index


class AdvancedFeaturesMixin:
    """Mixin providing advanced spreadsheet features for MainWindow."""

    # ── AutoSum ──

    def autosum(self):
        """Insert =SUM() formula for the contiguous numeric range above/left of the current cell."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        row, col = idx.row(), idx.column()
        ws = self.model.worksheet

        # Try to sum the column above
        top_row = row - 1
        while top_row >= 0:
            cell = ws.get_cell_or_none(top_row, col)
            if not cell or not cell.raw:
                break
            try:
                float(cell.value if cell.value is not None else cell.raw)
                top_row -= 1
            except (ValueError, TypeError):
                break
        top_row += 1

        if top_row < row:
            # Sum the column above
            start = col_index_to_letters(col) + str(top_row + 1)
            end = col_index_to_letters(col) + str(row)
            formula = f"=SUM({start}:{end})"
            self.model.setData(idx, formula, Qt.ItemDataRole.EditRole)
            self.status.showMessage(f"Inserted {formula}", 3000)
            return

        # Try to sum the row to the left
        left_col = col - 1
        while left_col >= 0:
            cell = ws.get_cell_or_none(row, left_col)
            if not cell or not cell.raw:
                break
            try:
                float(cell.value if cell.value is not None else cell.raw)
                left_col -= 1
            except (ValueError, TypeError):
                break
        left_col += 1

        if left_col < col:
            start = col_index_to_letters(left_col) + str(row + 1)
            end = col_index_to_letters(col) + str(row + 1)
            formula = f"=SUM({start}:{end})"
            self.model.setData(idx, formula, Qt.ItemDataRole.EditRole)
            self.status.showMessage(f"Inserted {formula}", 3000)
        else:
            self.status.showMessage("No numeric data found to sum", 3000)

    # ── Insert Function dialog ──

    def show_insert_function_dialog(self):
        from .function_dialog import InsertFunctionDialog
        dlg = InsertFunctionDialog(self)
        if dlg.exec():
            func = dlg.get_function()
            if func:
                idx = self.view.currentIndex()
                if idx.isValid():
                    self.model.setData(idx, f"={func}(", Qt.ItemDataRole.EditRole)
                    self.view.edit(idx)

    # ── Insert Symbol ──

    def show_insert_symbol_dialog(self):
        from .symbol_dialog import InsertSymbolDialog
        dlg = InsertSymbolDialog(self)
        if dlg.exec():
            sym = dlg.get_symbol()
            if sym:
                idx = self.view.currentIndex()
                if idx.isValid():
                    self.model.setData(idx, sym, Qt.ItemDataRole.EditRole)

    # ── Insert Hyperlink ──

    def show_hyperlink_dialog(self):
        from .hyperlink_dialog import InsertHyperlinkDialog
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(idx.row(), idx.column())
        current_url = cell.hyperlink if cell else None
        current_text = cell.raw if cell else ""
        dlg = InsertHyperlinkDialog(current_url, current_text, self)
        if dlg.exec():
            url = dlg.get_url()
            display = dlg.get_display_text()
            target_cell = ws.get_cell(idx.row(), idx.column())
            target_cell.hyperlink = url
            if display:
                target_cell.raw = display
                target_cell.value = display
            elif url:
                target_cell.raw = url
                target_cell.value = url
            # Apply blue underline style for hyperlinks
            target_cell.fmt.text_color = "#1a73e8"
            target_cell.fmt.underline = True
            self.model.notify_cell(idx.row(), idx.column())
            self.status.showMessage("Hyperlink added" if url else "Hyperlink removed", 2000)

    def open_hyperlink(self, row, col):
        """Open the hyperlink in the default browser."""
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(row, col)
        if cell and cell.hyperlink:
            webbrowser.open(cell.hyperlink)

    def remove_hyperlink(self):
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(idx.row(), idx.column())
        if cell:
            cell.hyperlink = None
            cell.fmt.text_color = None
            cell.fmt.underline = False
            self.model.notify_cell(idx.row(), idx.column())

    # ── Insert Image ──

    def insert_image(self):
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Insert Image", "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.svg)")
        if not path:
            return
        ws = self.model.worksheet
        ws.images[(idx.row(), idx.column())] = (path, 0, 0)
        self.view.viewport().update()
        self.status.showMessage(f"Inserted image from {os.path.basename(path)}", 3000)

    # ── Gridlines toggle ──

    def toggle_gridlines(self):
        ws = self.model.worksheet
        ws.show_gridlines = not ws.show_gridlines
        self.view.setShowGrid(ws.show_gridlines)
        self.status.showMessage(
            "Gridlines " + ("visible" if ws.show_gridlines else "hidden"), 2000)

    # ── Strikethrough ──

    def toggle_strikethrough(self):
        idx = self.view.currentIndex()
        if idx.isValid():
            cell = self.model.worksheet.get_cell_or_none(idx.row(), idx.column())
            current = cell.fmt.strikethrough if cell else False
            self.apply_format({'strikethrough': not current})

    # ── Text indent ──

    def increase_indent(self):
        selection = self.view.selectionModel().selection()
        cells = []
        if selection:
            for rng in selection:
                for r in range(rng.top(), rng.bottom() + 1):
                    for c in range(rng.left(), rng.right() + 1):
                        cells.append((r, c))
        else:
            idx = self.view.currentIndex()
            if idx.isValid():
                cells.append((idx.row(), idx.column()))
        for r, c in cells:
            cell = self.model.worksheet.get_cell(r, c)
            cell.fmt.indent = min(cell.fmt.indent + 1, 15)
        self.model.notify_all()

    def decrease_indent(self):
        selection = self.view.selectionModel().selection()
        cells = []
        if selection:
            for rng in selection:
                for r in range(rng.top(), rng.bottom() + 1):
                    for c in range(rng.left(), rng.right() + 1):
                        cells.append((r, c))
        else:
            idx = self.view.currentIndex()
            if idx.isValid():
                cells.append((idx.row(), idx.column()))
        for r, c in cells:
            cell = self.model.worksheet.get_cell(r, c)
            cell.fmt.indent = max(cell.fmt.indent - 1, 0)
        self.model.notify_all()

    # ── Tab color ──

    def set_tab_color(self):
        """Set the color of the active sheet tab."""
        sheet = self.workbook.active_sheet
        color = QColorDialog.getColor(
            QColor(sheet.tab_color) if sheet.tab_color else QColor("#1a73e8"),
            self, "Tab Color")
        if color.isValid():
            sheet.tab_color = color.name()
            self.sheet_tabs.refresh()
            self.status.showMessage(f"Tab color set to {color.name()}", 2000)

    def clear_tab_color(self):
        sheet = self.workbook.active_sheet
        sheet.tab_color = None
        self.sheet_tabs.refresh()

    # ── Hide / Unhide sheets ──

    def hide_sheet(self):
        """Hide the active sheet (must keep at least one visible)."""
        visible_count = sum(1 for s in self.workbook.sheets if not s.sheet_hidden)
        if visible_count <= 1:
            self.status.showMessage("Cannot hide the last visible sheet", 3000)
            return
        self.workbook.active_sheet.sheet_hidden = True
        # Switch to the first visible sheet
        for i, s in enumerate(self.workbook.sheets):
            if not s.sheet_hidden:
                self.workbook.active_index = i
                break
        self.sheet_tabs.refresh()
        self.model.set_worksheet(self.workbook.active_sheet)
        self.status.showMessage("Sheet hidden", 2000)

    def unhide_sheet(self):
        """Show a dialog to unhide a hidden sheet."""
        hidden = [(i, s.name) for i, s in enumerate(self.workbook.sheets) if s.sheet_hidden]
        if not hidden:
            self.status.showMessage("No hidden sheets", 3000)
            return
        names = [name for _, name in hidden]
        name, ok = QInputDialog.getItem(
            self, "Unhide Sheet", "Select sheet to unhide:", names, 0, False)
        if ok and name:
            for idx, _ in hidden:
                if self.workbook.sheets[idx].name == name:
                    self.workbook.sheets[idx].sheet_hidden = False
                    self.workbook.active_index = idx
                    break
            self.sheet_tabs.refresh()
            self.model.set_worksheet(self.workbook.active_sheet)
            self.status.showMessage(f"Unhid '{name}'", 2000)

    # ── Sheet protection ──

    def protect_sheet(self):
        from .protection_dialog import ProtectSheetDialog
        sheet = self.workbook.active_sheet
        dlg = ProtectSheetDialog(sheet.sheet_protected, self)
        if dlg.exec():
            sheet.sheet_protected = dlg.should_protect()
            self.status.showMessage(
                "Sheet protected" if sheet.sheet_protected else "Sheet unprotected", 2000)

    # ── Group & Outline ──

    def group_rows(self):
        selection = self.view.selectionModel().selection()
        if not selection:
            self.status.showMessage("Select rows to group", 3000)
            return
        sheet = self.model.worksheet
        for rng in selection:
            start, end = rng.top(), rng.bottom()
            sheet.row_groups.append((start, end, False))
            self._apply_row_group(start, end, False)
        self.status.showMessage("Rows grouped", 2000)

    def group_cols(self):
        selection = self.view.selectionModel().selection()
        if not selection:
            self.status.showMessage("Select columns to group", 3000)
            return
        sheet = self.model.worksheet
        for rng in selection:
            start, end = rng.left(), rng.right()
            sheet.col_groups.append((start, end, False))
            self._apply_col_group(start, end, False)
        self.status.showMessage("Columns grouped", 2000)

    def ungroup_all_rows(self):
        sheet = self.model.worksheet
        if sheet.row_groups:
            for start, end, _ in sheet.row_groups:
                for r in range(start, end + 1):
                    self.view.setRowHidden(r, False)
            sheet.row_groups = []
            self.status.showMessage("All row groups removed", 2000)

    def ungroup_all_cols(self):
        sheet = self.model.worksheet
        if sheet.col_groups:
            for start, end, _ in sheet.col_groups:
                for c in range(start, end + 1):
                    self.view.setColumnHidden(c, False)
            sheet.col_groups = []
            self.status.showMessage("All column groups removed", 2000)

    def _apply_row_group(self, start, end, collapsed):
        for r in range(start, end + 1):
            self.view.setRowHidden(r, collapsed)

    def _apply_col_group(self, start, end, collapsed):
        for c in range(start, end + 1):
            self.view.setColumnHidden(c, collapsed)

    def toggle_row_group(self, group_idx):
        sheet = self.model.worksheet
        if 0 <= group_idx < len(sheet.row_groups):
            start, end, collapsed = sheet.row_groups[group_idx]
            collapsed = not collapsed
            sheet.row_groups[group_idx] = (start, end, collapsed)
            self._apply_row_group(start, end, collapsed)

    def toggle_col_group(self, group_idx):
        sheet = self.model.worksheet
        if 0 <= group_idx < len(sheet.col_groups):
            start, end, collapsed = sheet.col_groups[group_idx]
            collapsed = not collapsed
            sheet.col_groups[group_idx] = (start, end, collapsed)
            self._apply_col_group(start, end, collapsed)

    # ── Recent files ──

    def _recent_files_path(self):
        import os
        home = os.path.expanduser("~")
        return os.path.join(home, ".localsheet", "recent.json")

    def _load_recent_files(self):
        import os, json
        path = self._recent_files_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (ValueError, IOError):
            return []

    def _add_recent_file(self, path):
        import os, json
        recent = self._load_recent_files()
        recent = [p for p in recent if p != path]
        recent.insert(0, path)
        recent = recent[:10]  # keep last 10
        try:
            os.makedirs(os.path.dirname(self._recent_files_path()), exist_ok=True)
            with open(self._recent_files_path(), 'w') as f:
                json.dump(recent, f)
        except IOError:
            pass

    def _rebuild_recent_menu(self, menu):
        """Populate the recent files submenu."""
        menu.clear()
        recent = self._load_recent_files()
        if not recent:
            act = menu.addAction("(No recent files)")
            act.setEnabled(False)
            return
        for path in recent:
            if os.path.exists(path):
                act = menu.addAction(os.path.basename(path))
                act.setToolTip(path)
                act.triggered.connect(lambda checked=False, p=path: self._open_recent(p))

    def _open_recent(self, path):
        if not os.path.exists(path):
            self.status.showMessage("File not found", 3000)
            return
        if not self._check_save():
            return
        try:
            if path.lower().endswith('.csv'):
                from .file_io import load_csv
                self.workbook = load_csv(path)
            else:
                from .file_io import load_xlsx
                self.workbook = load_xlsx(path)
            self.workbook.file_path = path
            self.undo_stack.clear()
            self._switch_workbook()
            self._add_recent_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Could not open file:\n{e}")

    # ── Toggle auto-filter ──

    def toggle_filter(self):
        """Toggle filter dropdown on the current column."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        col = idx.column()
        sheet = self.model.worksheet
        if col in sheet.filters:
            sheet.filters.pop(col)
            self.status.showMessage(f"Filter cleared on column {col_index_to_letters(col)}", 2000)
        else:
            values = sheet.unique_values_in_col(col)
            sheet.filters[col] = set(values)
            self.status.showMessage(f"Filter enabled on column {col_index_to_letters(col)}", 2000)
        self._apply_filters()
        self.view.horizontalHeader().viewport().update()

    # ── Cell styles ──

    def show_cell_styles(self):
        from .cell_styles_dialog import CellStylesDialog
        dlg = CellStylesDialog(self)
        if dlg.exec():
            name = dlg.get_style()
            if name:
                fmt = CellStylesDialog.get_format_dict(name)
                self.apply_format(fmt)
                self.status.showMessage(f"Applied style: {name}", 2000)

    # ── Multi-column sort ──

    def show_multi_sort_dialog(self):
        from .multi_sort_dialog import MultiSortDialog
        ws = self.model.worksheet
        if not ws.cells:
            return
        max_col = max(c for _, c in ws.cells)
        dlg = MultiSortDialog(max_col, self)
        if dlg.exec():
            keys = dlg.get_sort_keys()
            if keys:
                self._multi_sort(keys, dlg.has_headers())

    def _multi_sort(self, keys, has_headers):
        """Sort rows by multiple columns using stable sort (last key first)."""
        ws = self.model.worksheet
        rows_with_data = set()
        for (r, c), cell in ws.cells.items():
            if cell.raw:
                rows_with_data.add(r)
        if not rows_with_data:
            return
        rows = sorted(rows_with_data)
        if has_headers and 0 in rows:
            rows = rows[1:]

        def make_key(col):
            def key(row):
                cell = ws.get_cell_or_none(row, col)
                val = cell.value if cell else ""
                if isinstance(val, bool):
                    return (0, str(val).lower())
                if isinstance(val, (int, float)):
                    return (0, val)
                return (1, str(val).lower())
            return key

        # Stable sort from last key to first
        for col, ascending in reversed(keys):
            rows = sorted(rows, key=make_key(col), reverse=not ascending)

        all_cols = sorted(set(c for (_, c) in ws.cells.keys()))
        row_data = {}
        for r in rows:
            row_data[r] = {}
            for c in all_cols:
                cell = ws.get_cell_or_none(r, c)
                if cell:
                    row_data[r][c] = cell.raw

        orig_rows = sorted(rows_with_data)
        if has_headers and 0 in orig_rows:
            orig_rows = orig_rows[1:]

        changes = []
        for old_idx, new_row in enumerate(rows):
            old_row = orig_rows[old_idx] if old_idx < len(orig_rows) else new_row
            if old_row == new_row:
                continue
            for c in all_cols:
                old_cell = ws.get_cell(old_row, c)
                new_raw = row_data.get(new_row, {}).get(c, "")
                if old_cell.raw != new_raw:
                    changes.append((old_row, c, old_cell.raw, new_raw))

        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)
            self.status.showMessage(f"Sorted by {len(keys)} key(s)", 3000)

    # ── Drag-to-move cells ──

    def move_cells(self, src_top, src_left, src_bottom, src_right,
                   dst_row, dst_col):
        """Move a rectangular range of cells to a new location."""
        ws = self.model.worksheet
        changes = []
        # Collect source cells
        src_data = {}
        for r in range(src_top, src_bottom + 1):
            for c in range(src_left, src_right + 1):
                cell = ws.get_cell_or_none(r, c)
                if cell and cell.raw:
                    src_data[(r - src_top, c - src_left)] = (cell.raw, cell.fmt.to_dict())
        # Clear source
        for r in range(src_top, src_bottom + 1):
            for c in range(src_left, src_right + 1):
                old = ws.get_cell(r, c).raw
                if old:
                    changes.append((r, c, old, ""))
        # Write to destination
        for (dr, dc), (raw, fmt_dict) in src_data.items():
            target_r = dst_row + dr
            target_c = dst_col + dc
            old = ws.get_cell(target_r, target_c).raw
            changes.append((target_r, target_c, old, raw))
        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)
            self.status.showMessage("Cells moved", 2000)

    # ── Right-drag fill options ──

    def fill_series(self, start_row, start_col, end_row, end_col):
        """Fill with incrementing numbers (1, 2, 3...) instead of copying."""
        ws = self.model.worksheet
        src_cell = ws.get_cell_or_none(start_row, start_col)
        src_val = src_cell.value if src_cell else ""
        try:
            base = float(src_val)
        except (TypeError, ValueError):
            base = 1.0

        top = min(start_row, end_row)
        bottom = max(start_row, end_col)
        left = min(start_col, end_col)
        right = max(start_col, end_col)

        changes = []
        step = 1
        if start_row != end_row:
            step = 1 if end_row > start_row else -1
            delta = 0
            r = end_row
            while r != start_row:
                delta += step
                val = base + delta
                new_val = str(int(val)) if val == int(val) else str(val)
                old = ws.get_cell(r, start_col).raw
                if old != new_val:
                    changes.append((r, start_col, old, new_val))
                r -= step
        elif start_col != end_col:
            step = 1 if end_col > start_col else -1
            delta = 0
            c = end_col
            while c != start_col:
                delta += step
                val = base + delta
                new_val = str(int(val)) if val == int(val) else str(val)
                old = ws.get_cell(start_row, c).raw
                if old != new_val:
                    changes.append((start_row, c, old, new_val))
                c -= step

        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)