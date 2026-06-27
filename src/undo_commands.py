"""
QUndoCommand subclasses for cell edits, formatting, paste, and row/col operations.
Must inherit from QUndoCommand so QUndoStack.push() works correctly.
"""
from PyQt6.QtGui import QUndoCommand


class EditCellCommand(QUndoCommand):
    """Undoable edit of a single cell's raw value."""

    def __init__(self, model, row, col, old_value, new_value):
        super().__init__("Edit cell")
        self.model = model
        self.row = row
        self.col = col
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        self.model.worksheet.set_cell(self.row, self.col, self.old_value)
        self.model.recalc_and_notify()
        self.model.notify_cell(self.row, self.col)

    def redo(self):
        self.model.worksheet.set_cell(self.row, self.col, self.new_value)
        self.model.recalc_and_notify()
        self.model.notify_cell(self.row, self.col)


class FormatCommand(QUndoCommand):
    """Undoable formatting change applied to a list of (row, col) cells."""

    def __init__(self, model, cells, fmt_dict):
        super().__init__("Format cells")
        self.model = model
        self.cells = list(cells)
        self.fmt_dict = dict(fmt_dict)
        self.old_formats = []
        for (r, c) in self.cells:
            cell = model.worksheet.get_cell(r, c)
            self.old_formats.append(cell.fmt.to_dict())

    def undo(self):
        for (r, c), old in zip(self.cells, self.old_formats):
            cell = self.model.worksheet.get_cell(r, c)
            cell.fmt = type(cell.fmt)()
            cell.fmt.apply_dict(old)
            self.model.notify_cell(r, c)

    def redo(self):
        for (r, c) in self.cells:
            cell = self.model.worksheet.get_cell(r, c)
            cell.fmt.apply_dict(self.fmt_dict)
            self.model.notify_cell(r, c)


class PasteCommand(QUndoCommand):
    """Undoable paste of multiple cells."""

    def __init__(self, model, changes):
        super().__init__("Paste")
        self.model = model
        self.changes = changes  # [(row, col, old_raw, new_raw)]

    def undo(self):
        for (r, c, old, new) in self.changes:
            self.model.worksheet.set_cell(r, c, old)
        self.model.recalc_and_notify()
        for (r, c, _, _) in self.changes:
            self.model.notify_cell(r, c)

    def redo(self):
        for (r, c, old, new) in self.changes:
            self.model.worksheet.set_cell(r, c, new)
        self.model.recalc_and_notify()
        for (r, c, _, _) in self.changes:
            self.model.notify_cell(r, c)


class ClearCommand(QUndoCommand):
    """Undoable clear of multiple cells."""

    def __init__(self, model, cells):
        super().__init__("Clear")
        self.model = model
        self.cells = list(cells)  # [(row, col, old_raw)]

    def undo(self):
        for (r, c, old) in self.cells:
            self.model.worksheet.set_cell(r, c, old)
        self.model.recalc_and_notify()
        for (r, c, _) in self.cells:
            self.model.notify_cell(r, c)

    def redo(self):
        for (r, c, _) in self.cells:
            self.model.worksheet.clear_cell(r, c)
        self.model.recalc_and_notify()
        for (r, c, _) in self.cells:
            self.model.notify_cell(r, c)


class InsertRowCommand(QUndoCommand):
    def __init__(self, model, at):
        super().__init__("Insert Row")
        self.model = model
        self.at = at

    def undo(self):
        self.model.beginResetModel()
        self.model.worksheet.delete_row(self.at)
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()

    def redo(self):
        self.model.beginResetModel()
        self.model.worksheet.insert_row(self.at)
        self.model.worksheet.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()


class DeleteRowCommand(QUndoCommand):
    def __init__(self, model, at):
        super().__init__("Delete Row")
        self.model = model
        self.at = at
        self.deleted_cells = {}
        self.deleted_height = None

    def redo(self):
        self.deleted_cells = {}
        for (r, c), cell in list(self.model.worksheet.cells.items()):
            if r == self.at:
                self.deleted_cells[(r, c)] = (cell.raw, cell.value, cell.fmt.to_dict())
        self.deleted_height = self.model.worksheet.row_heights.get(self.at)
        self.model.beginResetModel()
        self.model.worksheet.delete_row(self.at)
        self.model.worksheet.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()

    def undo(self):
        self.model.beginResetModel()
        self.model.worksheet.insert_row(self.at)
        for (r, c), (raw, val, fmt_dict) in self.deleted_cells.items():
            cell = self.model.worksheet.get_cell(r, c)
            cell.raw = raw
            cell.value = val
            cell.fmt.apply_dict(fmt_dict)
        if self.deleted_height is not None:
            self.model.worksheet.row_heights[self.at] = self.deleted_height
        self.model.worksheet.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()


class InsertColCommand(QUndoCommand):
    def __init__(self, model, at):
        super().__init__("Insert Column")
        self.model = model
        self.at = at

    def undo(self):
        self.model.beginResetModel()
        self.model.worksheet.delete_col(self.at)
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()

    def redo(self):
        self.model.beginResetModel()
        self.model.worksheet.insert_col(self.at)
        self.model.worksheet.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()


class DeleteColCommand(QUndoCommand):
    def __init__(self, model, at):
        super().__init__("Delete Column")
        self.model = model
        self.at = at
        self.deleted_cells = {}
        self.deleted_width = None

    def redo(self):
        self.deleted_cells = {}
        for (r, c), cell in list(self.model.worksheet.cells.items()):
            if c == self.at:
                self.deleted_cells[(r, c)] = (cell.raw, cell.value, cell.fmt.to_dict())
        self.deleted_width = self.model.worksheet.col_widths.get(self.at)
        self.model.beginResetModel()
        self.model.worksheet.delete_col(self.at)
        self.model.worksheet.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()

    def undo(self):
        self.model.beginResetModel()
        self.model.worksheet.insert_col(self.at)
        for (r, c), (raw, val, fmt_dict) in self.deleted_cells.items():
            cell = self.model.worksheet.get_cell(r, c)
            cell.raw = raw
            cell.value = val
            cell.fmt.apply_dict(fmt_dict)
        if self.deleted_width is not None:
            self.model.worksheet.col_widths[self.at] = self.deleted_width
        self.model.worksheet.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()


class AddConditionalRuleCommand(QUndoCommand):
    """Undoable addition of a conditional formatting rule."""

    def __init__(self, model, rule):
        super().__init__("Add conditional rule")
        self.model = model
        self.rule = rule

    def redo(self):
        self.model.worksheet.conditional_rules.append(self.rule)
        self.model.rebuild_conditional_cache()
        self.model.notify_all()

    def undo(self):
        self.model.worksheet.conditional_rules.remove(self.rule)
        self.model.rebuild_conditional_cache()
        self.model.notify_all()


class ClearConditionalRulesCommand(QUndoCommand):
    """Undoable clearing of all conditional formatting rules."""

    def __init__(self, model):
        super().__init__("Clear conditional rules")
        self.model = model
        self.old_rules = []

    def redo(self):
        self.old_rules = list(self.model.worksheet.conditional_rules)
        self.model.worksheet.conditional_rules.clear()
        self.model.rebuild_conditional_cache()
        self.model.notify_all()

    def undo(self):
        self.model.worksheet.conditional_rules = list(self.old_rules)
        self.model.rebuild_conditional_cache()
        self.model.notify_all()


class SortCommand(QUndoCommand):
    """Undoable sort of rows by a column's values (ascending or descending)."""

    def __init__(self, model, col, ascending):
        super().__init__("Sort")
        self.model = model
        self.col = col
        self.ascending = ascending
        self._old_state = None

    def _snapshot(self, ws):
        cells_data = {}
        for (r, c), cell in ws.cells.items():
            cells_data[(r, c)] = (cell.raw, cell.value, cell.fmt.to_dict(), cell.note)
        return {
            'cells': cells_data,
            'row_heights': dict(ws.row_heights),
        }

    def _restore(self, ws, state):
        from .models import Cell
        ws.cells = {}
        for (r, c), (raw, val, fmt_dict, note) in state['cells'].items():
            cell = Cell(raw=raw, value=val, note=note)
            cell.fmt.apply_dict(fmt_dict)
            ws.cells[(r, c)] = cell
        ws.row_heights = dict(state['row_heights'])

    def _sort(self, ws, col, ascending):
        if not ws.cells:
            return
        max_row = max(r for r, _ in ws.cells)
        frozen = ws.frozen_rows

        def sort_key(row_idx):
            cell = ws.get_cell_or_none(row_idx, col)
            if cell is None or cell.raw == "":
                return (2, "")
            val = cell.value
            if isinstance(val, (int, float)):
                return (0, val)
            return (1, str(val))

        sortable = list(range(frozen, max_row + 1))
        sortable.sort(key=sort_key, reverse=not ascending)

        new_row_for = {}
        for i in range(frozen):
            new_row_for[i] = i
        for new_idx, old_row in enumerate(sortable):
            new_row_for[old_row] = frozen + new_idx

        new_cells = {}
        for (r, c), cell in ws.cells.items():
            new_cells[(new_row_for.get(r, r), c)] = cell
        ws.cells = new_cells

        new_heights = {}
        for old_row, h in ws.row_heights.items():
            new_heights[new_row_for.get(old_row, old_row)] = h
        ws.row_heights = new_heights

    def redo(self):
        ws = self.model.worksheet
        self._old_state = self._snapshot(ws)
        self.model.beginResetModel()
        self._sort(ws, self.col, self.ascending)
        ws.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()

    def undo(self):
        ws = self.model.worksheet
        self.model.beginResetModel()
        self._restore(ws, self._old_state)
        ws.recalc()
        self.model.endResetModel()
        self.model.rebuild_conditional_cache()