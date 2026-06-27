"""
MainWindow — ties together the workbook, model, view, toolbar, formula bar,
sheet tabs, search bar, menus, shortcuts, and all action handlers.
"""
import os
from PyQt6.QtCore import Qt, QFileInfo, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QMessageBox, QColorDialog, QDialog,
    QPushButton, QVBoxLayout as QVBox, QDialogButtonBox,
    QShortcut, QStatusBar
)
from .chart_dialog import ChartDialog
from .formula_engine import col_index_to_letters
from PyQt6.QtWidgets import QInputDialog, QTextEdit
from PyQt6.QtGui import QUndoStack
from . import qt_constants as C
from .models import Workbook, CellFormat, ConditionalRule
from .formula_engine import col_index_to_letters
from .file_io import save_xlsx, load_xlsx, export_csv, load_csv
from .spreadsheet_model import SpreadsheetModel
from .spreadsheet_view import SpreadsheetView
from .formula_bar import FormulaBar
from .search_bar import SearchBar
from .sheet_tabs import SheetTabs
from .toolbar import create_toolbar
from .filter_dialog import FilterDialog
from .spreadsheet_features import SpreadsheetFeaturesMixin
from .advanced_features import AdvancedFeaturesMixin
from . import undo_commands as UC


class MainWindow(QMainWindow, SpreadsheetFeaturesMixin, AdvancedFeaturesMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalSheet — Offline Spreadsheet")
        self.resize(1280, 800)

        # Restore window geometry from previous session
        from PyQt6.QtCore import QSettings
        self._settings = QSettings("LocalSheet", "LocalSheet")
        geom = self._settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)

        # Core data
        self.workbook = Workbook()
        # Restore locally stored data from previous session
        self._load_local()
        self.undo_stack = QUndoStack()
        self.undo_stack.cleanChanged.connect(self._on_clean_changed)

        # Model + view
        self.model = SpreadsheetModel(self.workbook.active_sheet, self.undo_stack, self)
        self.view = SpreadsheetView(self.model, self)

        # UI components
        self.formula_bar = FormulaBar(self)
        self.formula_bar.commit.connect(self._on_formula_bar_commit)
        self.search_bar = SearchBar(self)
        self.search_bar.search_changed.connect(self._on_search)
        self.search_bar.next_match.connect(self._search_next)
        self.search_bar.prev_match.connect(self._search_prev)
        self.search_bar.closed.connect(self._close_search)
        self.search_bar.replace_requested.connect(self._on_replace)
        self.search_bar.replace_all_requested.connect(self._on_replace_all)
        self.sheet_tabs = SheetTabs(self.workbook, self)
        self.sheet_tabs.sheet_changed.connect(self._on_sheet_changed)
        self.sheet_tabs.sheet_added.connect(self._on_sheet_added)
        self.sheet_tabs.sheet_deleted.connect(self._on_sheet_deleted)
        self.sheet_tabs.sheet_renamed.connect(self._on_sheet_renamed)
        self.sheet_tabs.sheet_duplicated.connect(self._on_sheet_duplicated)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._file_label = QLabel("Untitled")
        self.status.addWidget(self._file_label)

        # Layout
        self._setup_layout()

        # Toolbar + menu
        self.toolbar_actions = create_toolbar(self)
        self._create_menu()

        # Connect view signals
        self.view.selectionModel().currentChanged.connect(self._on_current_changed)
        self.view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.view.selectionModel().selectionChanged.connect(lambda: self._update_status_stats())

        # Search state
        self._search_matches_list = []
        self._search_index = 0

        # Theme
        self._dark_mode = False

        # Auto-save timer
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(30000)  # 30 seconds

        # Populate recent files menu
        self._rebuild_recent_menu(self._recent_menu)

        # Initial state
        self._on_current_changed(self.view.currentIndex(), self.view.currentIndex())
        self._update_title()

    # ── Layout ──

    def _setup_layout(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.formula_bar)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.sheet_tabs)
        self.setCentralWidget(central)

    # ── Menu ──

    def _maction(self, menu, text, handler, shortcut=None, checkable=False):
        """Create a QAction, wire it up, and add it to *menu*."""
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if checkable:
            act.setCheckable(True)
        act.triggered.connect(handler)
        menu.addAction(act)
        return act

    def _create_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._maction(file_menu, "New", self.on_new, "Ctrl+N")
        self._maction(file_menu, "Open…", self.on_open, "Ctrl+O")
        # Recent files submenu
        recent_menu = file_menu.addMenu("Open Recent")
        self._recent_menu = recent_menu
        file_menu.addSeparator()
        self._maction(file_menu, "Save", self.on_save, "Ctrl+S")
        self._maction(file_menu, "Save As…", self.on_save_as)
        file_menu.addSeparator()
        self._maction(file_menu, "Import…", self.on_import, "Ctrl+Shift+I")
        self._maction(file_menu, "Export as CSV…", self.on_export_csv)
        self._maction(file_menu, "Export as XLSX…", self.on_export_xlsx)
        file_menu.addSeparator()
        self._maction(file_menu, "Exit", self.close, "Ctrl+Q")

        # Edit
        edit_menu = mb.addMenu("&Edit")
        self._maction(edit_menu, "Undo", self.on_undo, "Ctrl+Z")
        self._maction(edit_menu, "Redo", self.on_redo, "Ctrl+Y")
        edit_menu.addSeparator()
        self._maction(edit_menu, "Cut", self.on_cut, "Ctrl+X")
        self._maction(edit_menu, "Copy", self.on_copy, "Ctrl+C")
        self._maction(edit_menu, "Paste", self.on_paste, "Ctrl+V")
        self._maction(edit_menu, "Paste Special…", self.paste_special, "Ctrl+Shift+V")
        self._maction(edit_menu, "Select All", self.on_select_all, "Ctrl+A")
        self._maction(edit_menu, "Find…", self.on_find, "Ctrl+F")
        self._maction(edit_menu, "Go To…", self.go_to, "Ctrl+G")
        edit_menu.addSeparator()
        self._maction(edit_menu, "Insert Row Above", lambda: self.insert_row(self.view.currentIndex().row()), "Ctrl+Shift++")
        self._maction(edit_menu, "Insert Row Below", lambda: self.insert_row(self.view.currentIndex().row() + 1))
        self._maction(edit_menu, "Delete Row", lambda: self.delete_row(self.view.currentIndex().row()), "Ctrl+-")
        self._maction(edit_menu, "Insert Column Left", lambda: self.insert_col(self.view.currentIndex().column()))
        self._maction(edit_menu, "Insert Column Right", lambda: self.insert_col(self.view.currentIndex().column() + 1))
        self._maction(edit_menu, "Delete Column", lambda: self.delete_col(self.view.currentIndex().column()))
        edit_menu.addSeparator()
        self._maction(edit_menu, "Clear Contents", self.clear_selected_cells, "Delete")

        # Format
        fmt_menu = mb.addMenu("&Format")
        self._maction(fmt_menu, "Format Cells\u2026", self.show_format_dialog, "Ctrl+1")
        self._maction(fmt_menu, "Cell Styles\u2026", self.show_cell_styles)
        self._maction(fmt_menu, "Format Painter", self.toggle_format_painter)
        self._maction(fmt_menu, "Merge Cells", self.toggle_merge)
        fmt_menu.addSeparator()
        self._maction(fmt_menu, "Bold", lambda: self.apply_format({'bold': True}), "Ctrl+B")
        self._maction(fmt_menu, "Italic", lambda: self.apply_format({'italic': True}), "Ctrl+I")
        self._maction(fmt_menu, "Underline", lambda: self.apply_format({'underline': True}), "Ctrl+U")
        self._maction(fmt_menu, "Strikethrough", self.toggle_strikethrough, "Ctrl+5")
        self._maction(fmt_menu, "Text Color…", self.on_text_color)
        self._maction(fmt_menu, "Fill Color…", self.on_bg_color)
        fmt_menu.addSeparator()
        self._maction(fmt_menu, "Align Left", lambda: self.apply_format({'align': 'left'}))
        self._maction(fmt_menu, "Align Center", lambda: self.apply_format({'align': 'center'}))
        self._maction(fmt_menu, "Align Right", lambda: self.apply_format({'align': 'right'}))
        self._maction(fmt_menu, "Increase Indent", self.increase_indent)
        self._maction(fmt_menu, "Decrease Indent", self.decrease_indent)
        fmt_menu.addSeparator()
        self._maction(fmt_menu, "All Borders", lambda: self.apply_format({'border': 'all'}))
        self._maction(fmt_menu, "No Borders", lambda: self.apply_format({'border': None}))
        fmt_menu.addSeparator()
        self._maction(fmt_menu, "Wrap Text", lambda: self.apply_format({'wrap_text': True}), checkable=False)
        self._maction(fmt_menu, "Currency Format", lambda: self.apply_format({'number_format': 'currency'}))
        self._maction(fmt_menu, "Percent Format", lambda: self.apply_format({'number_format': 'percent'}), "Ctrl+Shift+5")
        self._maction(fmt_menu, "Two Decimals", lambda: self.apply_format({'number_format': 'float2'}))
        self._maction(fmt_menu, "Integer Format", lambda: self.apply_format({'number_format': 'int'}))
        self._maction(fmt_menu, "Thousands Format", lambda: self.apply_format({'number_format': 'thousands'}))
        self._maction(fmt_menu, "Date Format", lambda: self.apply_format({'number_format': 'date'}))
        self._maction(fmt_menu, "Time Format", lambda: self.apply_format({'number_format': 'time'}))
        self._maction(fmt_menu, "Clear Number Format", lambda: self.apply_format({'number_format': None}))
        fmt_menu.addSeparator()
        self._maction(fmt_menu, "Conditional Formatting\u2026", self.show_conditional_format_dialog)
        self._maction(fmt_menu, "Clear Conditional Rules", self.clear_conditional_format)

        # Insert
        ins_menu = mb.addMenu("&Insert")
        self._maction(ins_menu, "Function\u2026", self.show_insert_function_dialog)
        self._maction(ins_menu, "Symbol\u2026", self.show_insert_symbol_dialog)
        ins_menu.addSeparator()
        self._maction(ins_menu, "Hyperlink\u2026", self.show_hyperlink_dialog)
        self._maction(ins_menu, "Remove Hyperlink", self.remove_hyperlink)
        ins_menu.addSeparator()
        self._maction(ins_menu, "Image\u2026", self.insert_image)
        self._maction(ins_menu, "Chart\u2026", self.show_chart_dialog)
        ins_menu.addSeparator()
        self._maction(ins_menu, "Named Ranges\u2026", self.show_named_ranges_dialog)
        ins_menu.addSeparator()
        self._maction(ins_menu, "Data Validation\u2026", self.show_data_validation_dialog)

        # Data
        data_menu = mb.addMenu("&Data")
        self._maction(data_menu, "Sort\u2026", self.show_multi_sort_dialog)
        self._maction(data_menu, "Sort A\u2192Z", lambda: self.sort_column(self.view.currentIndex().column(), True))
        self._maction(data_menu, "Sort Z\u2192A", lambda: self.sort_column(self.view.currentIndex().column(), False))
        data_menu.addSeparator()
        self._maction(data_menu, "Filter", self.toggle_filter, "Ctrl+Shift+L")
        self._maction(data_menu, "Clear Filter", self.clear_filter)
        data_menu.addSeparator()
        self._maction(data_menu, "Remove Duplicates", self.remove_duplicates)
        data_menu.addSeparator()
        self._maction(data_menu, "Group Rows", self.group_rows)
        self._maction(data_menu, "Group Columns", self.group_cols)
        self._maction(data_menu, "Ungroup All Rows", self.ungroup_all_rows)
        self._maction(data_menu, "Ungroup All Columns", self.ungroup_all_cols)

        # View
        view_menu = mb.addMenu("&View")
        self._maction(view_menu, "Freeze Top Row", self.toggle_freeze_row, checkable=True)
        self._maction(view_menu, "Freeze First Column", self.toggle_freeze_col, checkable=True)
        self._maction(view_menu, "Freeze at Current Cell", self.freeze_at_cell)
        self._maction(view_menu, "Unfreeze Panes", self.unfreeze_panes)
        view_menu.addSeparator()
        self._maction(view_menu, "Toggle Gridlines", self.toggle_gridlines, checkable=True)
        view_menu.addSeparator()
        self._maction(view_menu, "Zoom In", self.zoom_in, "Ctrl++")
        self._maction(view_menu, "Zoom Out", self.zoom_out, "Ctrl+-")
        self._maction(view_menu, "Reset Zoom (100%)", self.zoom_reset, "Ctrl+0")
        view_menu.addSeparator()
        self._maction(view_menu, "Page Setup\u2026", self.show_page_setup)
        self._maction(view_menu, "Print Preview\u2026", self.on_print_preview)
        self._maction(view_menu, "Print\u2026", self.on_print, "Ctrl+P")
        view_menu.addSeparator()
        self._maction(view_menu, "Show Formulas", self.toggle_show_formulas, checkable=True)
        self._maction(view_menu, "Dark Mode", self.toggle_theme, checkable=True)

        # Sheet
        sheet_menu = mb.addMenu("&Sheet")
        self._maction(sheet_menu, "Protect Sheet\u2026", self.protect_sheet)
        sheet_menu.addSeparator()
        self._maction(sheet_menu, "Tab Color\u2026", self.set_tab_color)
        self._maction(sheet_menu, "Clear Tab Color", self.clear_tab_color)
        sheet_menu.addSeparator()
        self._maction(sheet_menu, "Hide Sheet", self.hide_sheet)
        self._maction(sheet_menu, "Unhide Sheet\u2026", self.unhide_sheet)

        # Help
        help_menu = mb.addMenu("&Help")
        self._maction(help_menu, "About LocalSheet", self._show_about)

    # ── File actions ──

    def on_new(self):
        if not self._check_save():
            return
        self.workbook = Workbook()
        self.undo_stack.clear()
        self._switch_workbook()

    def on_open(self):
        if not self._check_save():
            return
        path, f = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "Spreadsheet Files (*.xlsx *.csv);;Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            if path.lower().endswith('.csv'):
                self.workbook = load_csv(path)
            else:
                self.workbook = load_xlsx(path)
            self.workbook.file_path = path
            self.undo_stack.clear()
            self._switch_workbook()
            self._add_recent_file(path)
            self._rebuild_recent_menu(self._recent_menu)
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Could not open file:\n{e}")

    def on_save(self):
        if self.workbook.file_path:
            self._save_to(self.workbook.file_path)
        else:
            self.on_save_as()

    def on_save_as(self):
        path, f = QFileDialog.getSaveFileName(
            self, "Save File", "Untitled.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if not path:
            return
        self._save_to(path)

    def _save_to(self, path):
        try:
            if path.lower().endswith('.csv'):
                export_csv(self.workbook.active_sheet, path)
            else:
                save_xlsx(self.workbook, path)
            self.workbook.file_path = path
            self.undo_stack.setClean()
            self._update_title()
            self._add_recent_file(path)
            self._rebuild_recent_menu(self._recent_menu)
            self.status.showMessage(f"Saved to {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")

    def on_export_csv(self):
        path, f = QFileDialog.getSaveFileName(
            self, "Export as CSV", "export.csv", "CSV Files (*.csv)")
        if path:
            try:
                export_csv(self.workbook.active_sheet, path)
                self.status.showMessage(f"Exported to {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def on_export_xlsx(self):
        path, f = QFileDialog.getSaveFileName(
            self, "Export as XLSX", "export.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                save_xlsx(self.workbook, path)
                self.status.showMessage(f"Exported to {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def on_import(self):
        """Import data from a CSV or XLSX file into the current sheet at the active cell."""
        path, f = QFileDialog.getOpenFileName(
            self, "Import File", "",
            "Spreadsheet Files (*.xlsx *.csv);;Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            if path.lower().endswith('.csv'):
                wb = load_csv(path)
            else:
                wb = load_xlsx(path)
            if not wb.sheets:
                return
            src_sheet = wb.sheets[0]
            idx = self.view.currentIndex()
            if not idx.isValid():
                return
            start_row, start_col = idx.row(), idx.column()
            changes = []
            for (r, c), cell in src_sheet.cells.items():
                target_r = start_row + r
                target_c = start_col + c
                old = self.model.worksheet.get_cell(target_r, target_c).raw
                if old != cell.raw:
                    changes.append((target_r, target_c, old, cell.raw))
            if changes:
                cmd = UC.PasteCommand(self.model, changes)
                self.undo_stack.push(cmd)
            self.model.recalc_and_notify()
            self.status.showMessage(f"Imported {len(changes)} cells from {os.path.basename(path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not import file:\n{e}")

    def _check_save(self):
        """Returns True if OK to proceed (saved or user said discard)."""
        if self.undo_stack.isClean():
            return True
        ret = QMessageBox.question(
            self, "Unsaved Changes",
            "Save changes before proceeding?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if ret == QMessageBox.StandardButton.Save:
            self.on_save()
            return self.undo_stack.isClean()
        elif ret == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _switch_workbook(self):
        self.sheet_tabs.refresh()
        self.model.set_worksheet(self.workbook.active_sheet)
        self.model.recalc_and_notify()
        self._update_title()
        self.view.set_frozen_rows(self.workbook.active_sheet.frozen_rows)
        self.view.set_frozen_cols(self.workbook.active_sheet.frozen_cols)
        self.view.setShowGrid(self.workbook.active_sheet.show_gridlines)
        self.view.refresh_spans()
        self.view.setCurrentIndex(self.model.index(0, 0))
        self._on_current_changed(self.view.currentIndex(), self.view.currentIndex())

    def _autosave_path(self):
        """Path to the local persistence file in the user's home directory."""
        home = os.path.expanduser("~")
        folder = os.path.join(home, ".localsheet")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "autosave.xlsx")

    def _load_local(self):
        """Restore workbook from local autosave if available."""
        path = self._autosave_path()
        if not os.path.exists(path):
            return
        try:
            wb = load_xlsx(path)
            wb.file_path = None  # autosave is not a user-chosen file
            self.workbook = wb
            self.status.showMessage("Restored from local storage", 3000)
        except Exception:
            pass  # corrupt autosave — start fresh

    def _save_local(self):
        """Persist current workbook to local autosave for next session."""
        try:
            save_xlsx(self.workbook, self._autosave_path())
        except Exception:
            pass

    def _auto_save(self):
        if self.undo_stack.isClean():
            return
        # Save to explicit file path if set
        if self.workbook.file_path:
            try:
                if self.workbook.file_path.lower().endswith('.csv'):
                    export_csv(self.workbook.active_sheet, self.workbook.file_path)
                else:
                    save_xlsx(self.workbook, self.workbook.file_path)
                self.status.showMessage("Auto-saved", 2000)
            except Exception:
                pass
        # Always persist locally for next session
        self._save_local()

    def _on_clean_changed(self, clean):
        self._update_title()

    def _update_title(self):
        name = os.path.basename(self.workbook.file_path) if self.workbook.file_path else "Untitled"
        modified = " *" if not self.undo_stack.isClean() else ""
        self.setWindowTitle(f"LocalSheet — {name}{modified}")
        self._file_label.setText(name + modified)

    # ── Undo / Redo ──

    def on_undo(self):
        self.undo_stack.undo()

    def on_redo(self):
        self.undo_stack.redo()

    # ── Clipboard ──

    def on_copy(self):
        from PyQt6.QtWidgets import QApplication
        text = self._selection_to_text()
        if text:
            QApplication.clipboard().setText(text)

    def on_cut(self):
        from PyQt6.QtWidgets import QApplication
        text = self._selection_to_text()
        if text:
            QApplication.clipboard().setText(text)
            self.clear_selected_cells()

    def on_paste(self):
        from PyQt6.QtWidgets import QApplication
        text = QApplication.clipboard().text()
        if not text:
            return
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        start_row, start_col = idx.row(), idx.column()
        rows = [line.split('\t') for line in text.split('\n')]
        # trim trailing empty lines
        while rows and rows[-1] == ['']:
            rows.pop()

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

    def on_select_all(self):
        self.view.selectAll()

    def _selection_to_text(self):
        selection = self.view.selectionModel().selection()
        if not selection:
            idx = self.view.currentIndex()
            if idx.isValid():
                cell = self.model.worksheet.get_cell_or_none(idx.row(), idx.column())
                return cell.display_value() if cell else ""
            return ""
        lines = []
        for rng in selection:
            for r in range(rng.top(), rng.bottom() + 1):
                row_vals = []
                for c in range(rng.left(), rng.right() + 1):
                    cell = self.model.worksheet.get_cell_or_none(r, c)
                    row_vals.append(cell.display_value() if cell else "")
                lines.append('\t'.join(row_vals))
        return '\n'.join(lines)

    # ── Clear ──

    def clear_selected_cells(self):
        selection = self.view.selectionModel().selection()
        cells = []
        if selection:
            for rng in selection:
                for r in range(rng.top(), rng.bottom() + 1):
                    for c in range(rng.left(), rng.right() + 1):
                        cell = self.model.worksheet.get_cell_or_none(r, c)
                        if cell and cell.raw != "":
                            cells.append((r, c, cell.raw))
        else:
            idx = self.view.currentIndex()
            if idx.isValid():
                cell = self.model.worksheet.get_cell_or_none(idx.row(), idx.column())
                if cell and cell.raw != "":
                    cells.append((idx.row(), idx.column(), cell.raw))

        if cells:
            cmd = UC.ClearCommand(self.model, cells)
            self.undo_stack.push(cmd)

    # ── Auto-fill ──

    def autofill(self, start_row, start_col, end_row, end_col):
        """Fill cells from the source range toward (end_row, end_col) via the fill handle."""
        ws = self.model.worksheet
        # The source is always a single cell (the current cell) in this implementation
        top = min(start_row, end_row)
        bottom = max(start_row, end_row)
        left = min(start_col, end_col)
        right = max(start_col, end_col)

        # Collect source values
        source_cell = ws.get_cell_or_none(start_row, start_col)
        source_raw = source_cell.raw if source_cell else ""
        source_val = source_cell.value if source_cell else ""

        changes = []

        # Try to detect a number series extension
        try:
            num = float(source_val)
            is_num = True
        except (TypeError, ValueError):
            is_num = False

        # Try date detection
        is_date_str = False
        parsed_date = None
        if isinstance(source_val, str) and source_val:
            import re
            # Common date patterns
            m = re.match(r'^(\d{1,4})[-/](\d{1,2})[-/](\d{1,4})$', source_val.strip())
            if m:
                import datetime
                parts = m.groups()
                try:
                    # try YYYY-MM-DD first
                    if len(parts[0]) == 4:
                        parsed_date = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                        is_date_str = True
                    elif len(parts[2]) == 4:
                        parsed_date = datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
                        is_date_str = True
                except ValueError:
                    pass

        if is_num and abs(end_row - start_row) >= 1 and start_col == end_col:
            # Vertical numeric series — increment by 1 in the drag direction
            step = 1 if end_row > start_row else -1
            delta = 0
            r = end_row
            while r != start_row:
                delta += step
                new_val = str(num + delta) if num != int(num) else str(int(num + delta))
                old = ws.get_cell(r, start_col).raw
                if old != new_val:
                    changes.append((r, start_col, old, new_val))
                r -= step
        elif is_date_str and parsed_date and abs(end_row - start_row) >= 1 and start_col == end_col:
            # Vertical date series — increment by 1 day
            import datetime
            step = 1 if end_row > start_row else -1
            delta = 0
            r = end_row
            while r != start_row:
                delta += step
                d = parsed_date + datetime.timedelta(days=delta)
                # match original format
                if len(str(parsed_date.year)) == 4:
                    new_val = d.strftime("%Y-%m-%d")
                else:
                    new_val = d.strftime("%m/%d/%Y")
                old = ws.get_cell(r, start_col).raw
                if old != new_val:
                    changes.append((r, start_col, old, new_val))
                r -= step
        else:
            # Default: copy the source value to all target cells
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    if r == start_row and c == start_col:
                        continue
                    old = ws.get_cell(r, c).raw
                    if old != source_raw:
                        changes.append((r, c, old, source_raw))

        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)

    def autofill_down(self, row, col):
        """Auto-fill down from the current cell to the end of adjacent data."""
        ws = self.model.worksheet
        for adj_col in (col - 1, col + 1):
            if adj_col < 0:
                continue
            end_row = row
            for r in range(row + 1, self.model.rowCount()):
                cell = ws.get_cell_or_none(r, adj_col)
                if cell and cell.raw:
                    end_row = r
                else:
                    break
            if end_row > row:
                self.autofill(row, col, end_row, col)
                return

    # ── Formatting ──

    def apply_format(self, fmt_dict):
        selection = self.view.selectionModel().selection()
        if not selection:
            idx = self.view.currentIndex()
            if idx.isValid():
                self.model.apply_format_to_range(
                    idx.row(), idx.column(), idx.row(), idx.column(), fmt_dict)
            return
        for rng in selection:
            self.model.apply_format_to_range(
                rng.top(), rng.left(), rng.bottom(), rng.right(), fmt_dict)

    def on_text_color(self):
        color = QColorDialog.getColor(QColor("#000000"), self, "Text Color")
        if color.isValid():
            self.apply_format({'text_color': color.name()})

    def on_bg_color(self):
        color = QColorDialog.getColor(QColor("#ffffff"), self, "Fill Color")
        if color.isValid():
            self.apply_format({'bg_color': color.name()})

    def show_format_dialog(self):
        """Comprehensive Format Cells dialog — font, alignment, number, border, fill."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            self.status.showMessage("Select a cell first", 3000)
            return
        from .format_dialog import FormatCellsDialog
        cell = self.model.worksheet.get_cell_or_none(idx.row(), idx.column())
        current_fmt = cell.fmt if cell else CellFormat()
        dlg = FormatCellsDialog(current_fmt, self)
        if dlg.exec():
            fmt = dlg.get_format()
            self.apply_format(fmt)

    # ── Conditional formatting ──

    def show_conditional_format_dialog(self):
        selection = self.view.selectionModel().selection()
        if selection:
            top = min(r.top() for r in selection)
            left = min(r.left() for r in selection)
            bottom = max(r.bottom() for r in selection)
            right = max(r.right() for r in selection)
        else:
            idx = self.view.currentIndex()
            if not idx.isValid():
                self.status.showMessage("Select a range first", 3000)
                return
            top, left = idx.row(), idx.column()
            bottom, right = idx.row(), idx.column()

        from .conditional_dialog import ConditionalFormatDialog
        dlg = ConditionalFormatDialog(top, left, bottom, right, self)
        if dlg.exec():
            params = dlg.get_rule_params()
            rule = ConditionalRule(top=top, left=left, bottom=bottom, right=right, **params)
            cmd = UC.AddConditionalRuleCommand(self.model, rule)
            self.undo_stack.push(cmd)

    def clear_conditional_format(self):
        if self.model.worksheet.conditional_rules:
            cmd = UC.ClearConditionalRulesCommand(self.model)
            self.undo_stack.push(cmd)

    # ── Auto-fit ──

    def autofit_column(self, col):
        """Resize a column to fit its widest cell content."""
        ws = self.model.worksheet
        max_w = 40
        fm = self.view.fontMetrics()
        for (r, c), cell in ws.cells.items():
            if c == col:
                text = cell.display_value()
                w = fm.horizontalAdvance(text) + 16
                if w > max_w:
                    max_w = w
        self.view.setColumnWidth(col, min(max_w, 500))

    def autofit_all_columns(self):
        """Auto-fit all columns that have content."""
        ws = self.model.worksheet
        cols_with_data = set(c for (_, c) in ws.cells.keys())
        for col in cols_with_data:
            self.autofit_column(col)

    def autofit_row(self, row):
        """Resize a row to fit its tallest cell content (considering wrap text)."""
        ws = self.model.worksheet
        max_h = 28
        fm = self.view.fontMetrics()
        col_width = 100
        for (r, c), cell in ws.cells.items():
            if r == row:
                text = cell.display_value()
                col_w = self.view.columnWidth(c)
                lines_needed = max(1, (fm.horizontalAdvance(text) + 8) // max(col_w - 8, 10))
                h = int(lines_needed * (fm.height() + 4) + 6)
                if h > max_h:
                    max_h = h
        self.view.setRowHeight(row, min(max_h, 400))

    # ── Zoom ──

    def zoom_in(self):
        self.view.zoom_in()

    def zoom_out(self):
        self.view.zoom_out()

    def zoom_reset(self):
        self.view.zoom_reset()

    # ── Status bar quick stats ──

    def _update_status_stats(self):
        """Show SUM, AVERAGE, COUNT of selected numeric cells in the status bar."""
        selection = self.view.selectionModel().selection()
        nums = []
        count = 0
        if selection:
            for rng in selection:
                for r in range(rng.top(), rng.bottom() + 1):
                    for c in range(rng.left(), rng.right() + 1):
                        cell = self.model.worksheet.get_cell_or_none(r, c)
                        if cell and cell.raw != "":
                            count += 1
                            try:
                                v = float(cell.value) if cell.value is not None else float(cell.raw)
                                if not isinstance(cell.value, bool):
                                    nums.append(v)
                            except (ValueError, TypeError):
                                pass
        if not nums:
            if count > 0:
                self.status.showMessage(f"Count: {count}", 0)
            else:
                self.status.clearMessage()
            return
        total = sum(nums)
        avg = total / len(nums)
        self.status.showMessage(
            f"Sum: {total:.2f}  |  Average: {avg:.2f}  |  Count: {len(nums)}", 0)

    # ── Merge cells ──

    def toggle_merge(self):
        """Merge/unmerge cells in the current selection."""
        selection = self.view.selectionModel().selection()
        if not selection or len(selection) != 1:
            self.status.showMessage("Select a range to merge", 3000)
            return
        rng = selection[0]
        ws = self.model.worksheet
        existing = ws.get_merge(rng.top(), rng.left())
        if existing:
            ws.remove_merge(rng.top(), rng.left())
            self.status.showMessage("Unmerged cells", 2000)
        else:
            ws.add_merge(rng.top(), rng.left(), rng.bottom(), rng.right())
            self.status.showMessage("Merged cells", 2000)
        self.model.notify_all()
        self.view.refresh_spans()

    # ── Format painter ──

    def toggle_format_painter(self):
        """Copy formatting from current cell, ready to paint on next click."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        cell = self.model.worksheet.get_cell_or_none(idx.row(), idx.column())
        if not cell:
            return
        self._format_painter_fmt = cell.fmt.to_dict()
        self._format_painter_active = True
        from PyQt6.QtGui import QCursor
        self.view.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.status.showMessage("Format painter: click a cell to apply formatting", 0)

    def _apply_format_painter(self, row, col):
        if not getattr(self, '_format_painter_active', False):
            return False
        from .undo_commands import FormatCommand
        cells = [(row, col)]
        cmd = FormatCommand(self.model, cells, self._format_painter_fmt)
        self.undo_stack.push(cmd)
        self._format_painter_active = False
        self.view.unsetCursor()
        self.status.clearMessage()
        return True

    # ── Data validation ──

    def show_data_validation_dialog(self):
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        from .data_validation_dialog import DataValidationDialog
        ws = self.model.worksheet
        existing = ws.data_validations.get((idx.row(), idx.column()))
        dlg = DataValidationDialog(existing, self)
        if dlg.exec():
            params = dlg.get_params()
            if params is None:
                ws.data_validations.pop((idx.row(), idx.column()), None)
            else:
                from .models import DataValidation
                ws.data_validations[(idx.row(), idx.column())] = DataValidation(**params)
            self.status.showMessage("Data validation updated", 2000)

    def get_validation_values(self, row, col):
        """Return list of dropdown values for a cell, or None."""
        ws = self.model.worksheet
        dv = ws.data_validations.get((row, col))
        if dv and dv.dv_type == 'list':
            return [v.strip() for v in dv.formula1.split(',')]
        return None

    # ── Named ranges ──

    def show_named_ranges_dialog(self):
        from .named_ranges_dialog import NamedRangesDialog
        ws = self.model.worksheet
        dlg = NamedRangesDialog(dict(ws.named_ranges), self)
        if dlg.exec():
            ws.named_ranges = dlg.get_ranges()
            self.status.showMessage("Named ranges updated", 2000)

    # ── Text to columns ──

    def text_to_columns(self):
        idx = self.view.currentIndex()
        if not idx.isValid():
            self.status.showMessage("Select a cell first", 3000)
            return
        from PyQt6.QtWidgets import QInputDialog
        delimiter, ok = QInputDialog.getText(
            self, "Text to Columns",
            "Delimiter (e.g., comma, semicolon, tab, space):",
            text=",")
        if not ok or not delimiter:
            return
        if delimiter.lower() == 'tab':
            delimiter = '\t'
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(idx.row(), idx.column())
        if not cell or not cell.raw:
            return
        parts = cell.raw.split(delimiter)
        changes = []
        for i, part in enumerate(parts):
            val = part.strip()
            col = idx.column() + i
            old = ws.get_cell(idx.row(), col).raw
            if old != val:
                changes.append((idx.row(), col, old, val))
        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)
            self.status.showMessage(f"Split into {len(changes)} columns", 3000)

    # ── Print ──

    def on_print_preview(self):
        from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(getattr(self, '_page_orientation', QPrinter.PageOrientation.Portrait))
        dlg = QPrintPreviewDialog(printer, self)
        dlg.paintRequested.connect(lambda p: self._render_print(p))
        dlg.exec()

    def on_print(self):
        from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(getattr(self, '_page_orientation', QPrinter.PageOrientation.Portrait))
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            self._render_print(printer)

    def _render_print(self, printer):
        from PyQt6.QtGui import QPainter, QFont
        ws = self.model.worksheet
        if not ws.cells:
            return
        max_row = max(r for r, _ in ws.cells)
        max_col = max(c for _, c in ws.cells)
        painter = QPainter(printer)
        font = QFont("Arial", 10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        x = 50
        y = 50
        row_h = 22
        col_w = 90
        for r in range(max_row + 1):
            if y + row_h > printer.height() - 50:
                printer.newPage()
                y = 50
            painter.drawLine(x, y, x + col_w * (max_col + 1), y)
            for c in range(max_col + 1):
                cell = ws.get_cell_or_none(r, c)
                text = cell.display_value() if cell else ""
                painter.drawText(x + c * col_w + 2, y + 16, text[:12])
            y += row_h
        painter.drawLine(x, y, x + col_w * (max_col + 1), y)
        # vertical lines
        for c in range(max_col + 2):
            painter.drawLine(x + c * col_w, 50, x + c * col_w, y)
        painter.end()

    # ── Page setup ──

    def show_page_setup(self):
        from .page_setup_dialog import PageSetupDialog
        from PyQt6.QtPrintSupport import QPrinter
        current = getattr(self, '_page_orientation', QPrinter.PageOrientation.Portrait)
        dlg = PageSetupDialog(current, self)
        if dlg.exec():
            self._page_orientation = dlg.get_orientation()

    # ── Theme ──

    def toggle_theme(self, checked):
        self._dark_mode = checked
        from .themes import apply_theme
        from PyQt6.QtWidgets import QApplication
        apply_theme(QApplication.instance(), checked)

    # ── Row / Column operations ──

    def insert_row(self, at):
        cmd = UC.InsertRowCommand(self.model, at)
        self.undo_stack.push(cmd)

    def delete_row(self, row):
        cmd = UC.DeleteRowCommand(self.model, row)
        self.undo_stack.push(cmd)

    def insert_col(self, at):
        cmd = UC.InsertColCommand(self.model, at)
        self.undo_stack.push(cmd)

    def delete_col(self, col):
        cmd = UC.DeleteColCommand(self.model, col)
        self.undo_stack.push(cmd)

    # ── Freeze panes ──

    def toggle_freeze_row(self):
        sheet = self.workbook.active_sheet
        if sheet.frozen_rows > 0:
            sheet.frozen_rows = 0
            self.view.set_frozen_rows(0)
        else:
            sheet.frozen_rows = 1
            self.view.set_frozen_rows(1)

    def toggle_freeze_col(self):
        sheet = self.workbook.active_sheet
        if sheet.frozen_cols > 0:
            sheet.frozen_cols = 0
            self.view.set_frozen_cols(0)
        else:
            sheet.frozen_cols = 1
            self.view.set_frozen_cols(1)

    def freeze_at_cell(self):
        """Freeze all rows above and all columns left of the current cell."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            self.status.showMessage("Select a cell first", 3000)
            return
        row, col = idx.row(), idx.column()
        sheet = self.workbook.active_sheet
        sheet.frozen_rows = row
        sheet.frozen_cols = col
        self.view.set_frozen_rows(row)
        self.view.set_frozen_cols(col)
        if row == 0 and col == 0:
            self.status.showMessage("No panes frozen (cell is A1)", 3000)
        else:
            self.status.showMessage(
                f"Froze {row} row(s) and {col} column(s)", 3000)

    def unfreeze_panes(self):
        """Clear all frozen rows and columns."""
        sheet = self.workbook.active_sheet
        sheet.frozen_rows = 0
        sheet.frozen_cols = 0
        self.view.set_frozen_rows(0)
        self.view.set_frozen_cols(0)
        self.status.showMessage("Panes unfrozen", 2000)

    # ── Sort ──

    def sort_column(self, col, ascending):
        cmd = UC.SortCommand(self.model, col, ascending)
        self.undo_stack.push(cmd)
        direction = "A\u2192Z" if ascending else "Z\u2192A"
        self.status.showMessage(f"Sorted column {col_index_to_letters(col)} {direction}", 3000)

    # ── Search ──

    def on_find(self):
        self.search_bar.focus_input()

    def _on_search(self, text):
        self.model.clear_search()
        self._search_matches_list = []
        if not text:
            self.search_bar.set_match_count(0, 0)
            return

        text_lower = text.lower()
        search_formulas = self.search_bar.is_formula_search()
        matches = set()
        for (r, c), cell in self.model.worksheet.cells.items():
            search_text = cell.raw if search_formulas else cell.display_value()
            if text_lower in (search_text or "").lower():
                matches.add((r, c))
                self._search_matches_list.append((r, c))

        self._search_matches_list.sort()
        self.model.set_search_matches(matches)
        self._search_index = 0
        if matches:
            self._goto_match(0)
        self.search_bar.set_match_count(
            len(matches), len(matches))

    def _goto_match(self, idx):
        if not self._search_matches_list:
            return
        idx = idx % len(self._search_matches_list)
        self._search_index = idx
        r, c = self._search_matches_list[idx]
        self.view.setCurrentIndex(self.model.index(r, c))
        self.search_bar.set_match_count(idx + 1, len(self._search_matches_list))

    def _search_next(self):
        if self._search_matches_list:
            self._goto_match(self._search_index + 1)

    def _search_prev(self):
        if self._search_matches_list:
            self._goto_match(self._search_index - 1)

    def _close_search(self):
        self.model.clear_search()
        self._search_matches_list = []
        self.search_bar.hide()
        self.view.setFocus()

    # ── Replace ──

    def _on_replace(self, find_text, replace_text):
        if not find_text or not self._search_matches_list:
            return
        idx = self._search_index
        if idx < 0 or idx >= len(self._search_matches_list):
            return
        r, c = self._search_matches_list[idx]
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(r, c)
        if not cell:
            return
        search_formulas = self.search_bar.is_formula_search()
        old_raw = cell.raw
        if search_formulas:
            new_raw = old_raw.replace(find_text, replace_text)
        else:
            new_raw = old_raw.replace(find_text, replace_text)
        if old_raw == new_raw:
            return
        cmd = UC.PasteCommand(self.model, [(r, c, old_raw, new_raw)])
        self.undo_stack.push(cmd)
        # Refresh search and advance to next match
        self._on_search(self.search_bar.input.text())
        if self._search_matches_list:
            self._goto_match(self._search_index)

    def _on_replace_all(self, find_text, replace_text):
        if not find_text:
            return
        ws = self.model.worksheet
        search_formulas = self.search_bar.is_formula_search()
        changes = []
        for (r, c), cell in ws.cells.items():
            search_text = cell.raw if search_formulas else cell.display_value()
            if find_text in (search_text or ""):
                old_raw = cell.raw
                new_raw = old_raw.replace(find_text, replace_text)
                if old_raw != new_raw:
                    changes.append((r, c, old_raw, new_raw))
        if changes:
            cmd = UC.PasteCommand(self.model, changes)
            self.undo_stack.push(cmd)
            self.status.showMessage(f"Replaced {len(changes)} cells", 3000)
        else:
            self.status.showMessage("No matches found", 3000)

    # ── Filter ──

    def filter_column(self, col):
        sheet = self.model.worksheet
        values = sheet.unique_values_in_col(col)
        current = sheet.filters.get(col)
        dlg = FilterDialog(values, current, self)
        if dlg.exec():
            selected = dlg.selected_values()
            if len(selected) == len(values):
                # all selected = no filter
                sheet.filters.pop(col, None)
            else:
                sheet.filters[col] = selected
            self._apply_filters()

    def clear_filter(self):
        sheet = self.model.worksheet
        sheet.filters.clear()
        self._apply_filters()
        self.status.showMessage("Filters cleared", 2000)

    def _apply_filters(self):
        sheet = self.model.worksheet
        if not sheet.filters:
            for r in range(self.model.rowCount()):
                self.view.setRowHidden(r, False)
        else:
            for r in range(self.model.rowCount()):
                hidden = False
                for col, allowed in sheet.filters.items():
                    cell = sheet.get_cell_or_none(r, col)
                    val = cell.display_value() if cell else ""
                    if val not in allowed:
                        hidden = True
                        break
                if r not in sheet.hidden_rows:
                    self.view.setRowHidden(r, hidden)
        # Refresh header to show/hide filter arrows
        self.model.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, self.model.columnCount() - 1)

    # ── Sheet management ──

    def _on_sheet_changed(self, index):
        if 0 <= index < len(self.workbook.sheets):
            self.model.set_worksheet(self.workbook.sheets[index])
            self.model.recalc_and_notify()
            self.view.set_frozen_rows(self.workbook.sheets[index].frozen_rows)
            self.view.set_frozen_cols(self.workbook.sheets[index].frozen_cols)
            self.view.setShowGrid(self.workbook.sheets[index].show_gridlines)
            self.view.refresh_spans()
            self._apply_filters()
            self._on_current_changed(self.view.currentIndex(), self.view.currentIndex())

    def _on_sheet_added(self):
        sheet = self.workbook.add_sheet()
        self.sheet_tabs.refresh()
        self.sheet_tabs.tab_bar.setCurrentIndex(len(self.workbook.sheets) - 1)

    def _on_sheet_deleted(self, index):
        if self.workbook.delete_sheet(index):
            self.sheet_tabs.refresh()
            self.model.set_worksheet(self.workbook.active_sheet)
            self._update_title()

    def _on_sheet_renamed(self, index, name):
        self.workbook.rename_sheet(index, name)
        self.sheet_tabs.refresh()

    def _on_sheet_duplicated(self, index):
        self.workbook.duplicate_sheet(index)
        self.sheet_tabs.refresh()
        self.sheet_tabs.tab_bar.setCurrentIndex(index + 1)

    # ── Selection / formula bar ──

    def _on_current_changed(self, current, previous):
        if not current.isValid():
            return
        row, col = current.row(), current.column()
        cell = self.model.worksheet.get_cell_or_none(row, col)
        raw = cell.raw if cell else ""
        self.formula_bar.update_cell(row, col, raw)

    def _on_selection_changed(self, selected, deselected):
        current = self.view.currentIndex()
        if current.isValid():
            row, col = current.row(), current.column()
            cell = self.model.worksheet.get_cell_or_none(row, col)
            raw = cell.raw if cell else ""
            self.formula_bar.update_cell(row, col, raw)

    def _on_formula_bar_commit(self, text):
        idx = self.view.currentIndex()
        if idx.isValid():
            self.model.setData(idx, text, Qt.ItemDataRole.EditRole)
            self.view.setFocus()

    # ── Cell notes ──

    def edit_cell_note(self):
        """Add or edit a note on the current cell."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(idx.row(), idx.column())
        current_note = cell.note if cell and cell.note else ""
        text, ok = QInputDialog.getMultiLineText(
            self, "Cell Note",
            f"Note for {col_index_to_letters(idx.column())}{idx.row()+1}:",
            current_note
        )
        if ok:
            if cell:
                cell.note = text if text.strip() else None
            else:
                cell = ws.get_cell(idx.row(), idx.column())
                cell.note = text if text.strip() else None
            self.model.refresh_cell(idx.row(), idx.column())

    def clear_cell_note(self):
        """Remove the note from the current cell."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        ws = self.model.worksheet
        cell = ws.get_cell_or_none(idx.row(), idx.column())
        if cell:
            cell.note = None
            self.model.refresh_cell(idx.row(), idx.column())

    # ── Chart ──

    def show_chart_dialog(self):
        """Extract data from the current selection and show a chart."""
        ws = self.model.worksheet
        sm = self.view.selectionModel()
        if not sm or not sm.hasSelection():
            QMessageBox.information(self, "Chart", "Please select a range of data first.")
            return
        sr = sm.selection()
        if sr.isEmpty():
            return
        top = sr.top()
        bottom = sr.bottom()
        left = sr.left()
        right = sr.right()

        labels = []
        values = []

        # If multiple rows, use first column as labels, second as values
        # If single row, use column headers as labels
        if bottom - top >= 1 and right - left >= 1:
            # First column = labels, second column = values
            label_col = left
            val_col = left + 1
            for r in range(top, bottom + 1):
                lc = ws.get_cell_or_none(r, label_col)
                vc = ws.get_cell_or_none(r, val_col)
                label = str(lc.value) if lc and lc.value else f"Row {r+1}"
                try:
                    val = float(vc.value) if vc and vc.value is not None else 0
                except (ValueError, TypeError):
                    val = 0
                labels.append(label)
                values.append(val)
        elif bottom - top >= 1:
            # Single column — use row numbers as labels
            val_col = left
            for r in range(top, bottom + 1):
                vc = ws.get_cell_or_none(r, val_col)
                try:
                    val = float(vc.value) if vc and vc.value is not None else 0
                except (ValueError, TypeError):
                    val = 0
                labels.append(f"Row {r+1}")
                values.append(val)
        elif right - left >= 1:
            # Single row — use column letters as labels
            val_row = top
            for c in range(left, right + 1):
                vc = ws.get_cell_or_none(val_row, c)
                try:
                    val = float(vc.value) if vc and vc.value is not None else 0
                except (ValueError, TypeError):
                    val = 0
                labels.append(col_index_to_letters(c))
                values.append(val)
        else:
            QMessageBox.information(self, "Chart", "Please select a range with more than one cell.")
            return

        if not values:
            QMessageBox.information(self, "Chart", "No numeric data found in selection.")
            return

        title = f"Chart ({col_index_to_letters(left)}{top+1}:{col_index_to_letters(right)}{bottom+1})"
        dialog = ChartDialog(labels, values, title, self)
        dialog.exec()

    # ── Window events ──

    def closeEvent(self, event):
        if self._check_save():
            self._settings.setValue("geometry", self.saveGeometry())
            self._save_local()
            event.accept()
        else:
            event.ignore()

    # ── Drag-and-drop file open ──

    def open_dropped_file(self, path):
        """Open a file that was dragged onto the window."""
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
            self._rebuild_recent_menu(self._recent_menu)
            self.status.showMessage(f"Opened {os.path.basename(path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Could not open file:\n{e}")

    def _show_about(self):
        QMessageBox.about(self, "About LocalSheet",
                          "<h3>LocalSheet</h3>"
                          "<p>A fully offline, self-contained desktop spreadsheet.</p>"
                          "<p>Built with Python &amp; PyQt6.</p>"
                          "<p>No internet, no cloud, no account required.</p>")