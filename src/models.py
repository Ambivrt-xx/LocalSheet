"""
Data models: CellFormat, Cell, Worksheet, Workbook.
No Qt dependency here — pure Python so the formula engine and file I/O stay clean.
"""
from .formula_engine import parse_value, format_value, recalculate


def _apply_custom_format(val, fmt_str):
    """Apply a custom number format string like '#,##0.00' or '$#,##0.00;[Red]-#,##0.00'."""
    # Split on semicolons for positive;negative;zero;text sections
    sections = fmt_str.split(';')
    if val > 0:
        section = sections[0] if len(sections) > 0 else 'General'
    elif val < 0:
        section = sections[1] if len(sections) > 1 else sections[0]
    else:
        section = sections[2] if len(sections) > 2 else sections[0]
    # Simple format application
    s = section
    has_thousands = '#,##0' in s or '0,000' in s
    decimals = 0
    if '.' in s:
        decimals = len(s.split('.')[1].replace('0', '0').replace('#', ''))
        decimals = s.count('0', s.index('.') + 1)
    abs_val = abs(val)
    if has_thousands:
        formatted = f"{abs_val:,.{decimals}f}"
    else:
        formatted = f"{abs_val:.{decimals}f}"
    # Handle currency symbols
    s = s.replace('#', '').replace(',', '').replace('0' * (decimals + 1), '').replace('.', '')
    s = s.replace('"', '')
    if val < 0:
        formatted = '-' + formatted
    return s.replace('Red', '').strip() + formatted if s.strip() and s.strip() not in ('-', '+') else formatted


# ───────────────────── CellFormat ─────────────────────

class CellFormat:
    __slots__ = ('bold', 'italic', 'underline', 'font_size', 'font_family',
                 'text_color', 'bg_color', 'align', 'border', 'number_format',
                 'wrap_text', 'strikethrough', 'indent', 'text_rotation',
                 'custom_format', 'locked')

    def __init__(self):
        self.bold = False
        self.italic = False
        self.underline = False
        self.font_size = 11
        self.font_family = None      # font name or None (uses default)
        self.text_color = None       # hex "#RRGGBB" or None
        self.bg_color = None          # hex or None
        self.align = None             # 'left' | 'center' | 'right' | None
        self.border = None            # None | 'all' | 'bottom' | 'top' | 'left' | 'right' | 'outline' | 'grid'
        self.number_format = None     # None | 'int' | 'float2' | 'percent' | 'currency' | 'thousands' | 'date' | 'time' | 'datetime'
        self.wrap_text = False        # wrap long text within cell
        self.strikethrough = False    # strikethrough text
        self.indent = 0               # indentation level (0-15)
        self.text_rotation = 0        # degrees (0-180; 0=none, 1-90=up, 91-180=down)
        self.custom_format = None     # custom number format string or None
        self.locked = True            # cell locked (when sheet is protected)

    def copy(self):
        c = CellFormat()
        for attr in self.__slots__:
            setattr(c, attr, getattr(self, attr))
        return c

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}

    def apply_dict(self, d):
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)


# ───────────────────── Cell ─────────────────────

class Cell:
    __slots__ = ('raw', 'value', 'fmt', 'note', 'hyperlink')

    def __init__(self, raw="", value=None, fmt=None, note=None, hyperlink=None):
        self.raw = raw
        self.value = value
        self.fmt = fmt or CellFormat()
        self.note = note           # comment string or None
        self.hyperlink = hyperlink  # URL string or None

    def is_formula(self):
        return isinstance(self.raw, str) and self.raw.startswith('=')

    def display_value(self):
        val = self.value
        if self.is_formula():
            base = format_value(val)
        else:
            base = format_value(val if val is not None else parse_value(self.raw))

        nf = self.fmt.number_format
        if nf and isinstance(val, (int, float)) and not isinstance(val, bool):
            if nf == 'currency':
                return f"${val:,.2f}"
            elif nf == 'percent':
                return f"{val * 100:.0f}%"
            elif nf == 'float2':
                return f"{val:.2f}"
            elif nf == 'int':
                return f"{int(round(val))}"
            elif nf == 'thousands':
                return f"{val:,.0f}"
            elif nf == 'date':
                import datetime as _dt
                try:
                    return (_dt.date(1899, 12, 30) + _dt.timedelta(days=int(val))).strftime("%m/%d/%Y")
                except (ValueError, OverflowError):
                    return base
            elif nf == 'time':
                frac = val - int(val)
                total_seconds = int(frac * 86400)
                h, rem = divmod(total_seconds, 3600)
                m, s = divmod(rem, 60)
                return f"{h:02d}:{m:02d}:{s:02d}"
            elif nf == 'datetime':
                import datetime as _dt
                try:
                    dt = _dt.date(1899, 12, 30) + _dt.timedelta(days=val)
                    return dt.strftime("%m/%d/%Y %H:%M")
                except (ValueError, OverflowError):
                    return base
        if self.fmt.custom_format and isinstance(val, (int, float)) and not isinstance(val, bool):
            return _apply_custom_format(val, self.fmt.custom_format)
        return base


# ───────────────────── ConditionalRule ─────────────────────

class ConditionalRule:
    """A conditional formatting rule applied to a rectangular range."""

    __slots__ = ('rule_type', 'top', 'left', 'bottom', 'right',
                 'min_color', 'mid_color', 'max_color', 'bar_color')

    def __init__(self, rule_type='color_scale', top=0, left=0, bottom=0, right=0, **kwargs):
        self.rule_type = rule_type
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right
        self.min_color = kwargs.get('min_color', '#f8696b')
        self.mid_color = kwargs.get('mid_color', '#ffeb84')
        self.max_color = kwargs.get('max_color', '#63be7b')
        self.bar_color = kwargs.get('bar_color', '#638ec6')

    def contains(self, row, col):
        return self.top <= row <= self.bottom and self.left <= col <= self.right

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


# ───────────────────── DataValidation ─────────────────────

class DataValidation:
    """A data validation rule on a cell (e.g., dropdown list)."""
    __slots__ = ('dv_type', 'formula1', 'allow_blank', 'prompt', 'error')

    def __init__(self, dv_type='list', formula1='', allow_blank=True, prompt='', error=''):
        self.dv_type = dv_type      # 'list' | 'whole' | 'decimal' | 'textLength'
        self.formula1 = formula1   # comma-separated values for 'list'
        self.allow_blank = allow_blank
        self.prompt = prompt
        self.error = error

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


# ───────────────────── Worksheet ─────────────────────

class Worksheet:
    def __init__(self, name="Sheet1"):
        self.name = name
        self.cells = {}          # {(row, col): Cell}
        self.col_widths = {}     # {col: pixels}
        self.row_heights = {}    # {row: pixels}
        self.frozen_rows = 0
        self.frozen_cols = 0
        self.hidden_rows = set()
        self.hidden_cols = set()
        self.filters = {}        # {col: set(values) or None}
        self.conditional_rules = []  # list of ConditionalRule
        self.named_ranges = {}   # {name: (r1, c1, r2, c2)}
        self.merged_cells = []  # list of (r1, c1, r2, c2)
        self.data_validations = {}  # {(r, c): DataValidation}
        self.tab_color = None      # hex color for the sheet tab
        self.sheet_hidden = False  # hide the entire sheet
        self.sheet_protected = False  # cell protection enabled
        self.show_gridlines = True # gridlines visibility
        self.row_groups = []       # list of (start_row, end_row, collapsed_bool)
        self.col_groups = []       # list of (start_col, end_col, collapsed_bool)
        self.images = {}           # {(row, col): (image_path, width, height)}

    # ── cell access ──

    def get_cell(self, row, col):
        key = (row, col)
        if key not in self.cells:
            self.cells[key] = Cell()
        return self.cells[key]

    def get_cell_or_none(self, row, col):
        return self.cells.get((row, col))

    def set_cell(self, row, col, raw):
        cell = self.get_cell(row, col)
        cell.raw = raw
        if cell.is_formula():
            cell.value = None
        else:
            cell.value = parse_value(raw)

    def clear_cell(self, row, col):
        key = (row, col)
        if key in self.cells:
            self.cells[key].raw = ""
            self.cells[key].value = ""

    def get_cell_value(self, row, col):
        cell = self.cells.get((row, col))
        if cell is None:
            return ""
        return cell.value if cell.value is not None else ""

    def get_display_value(self, row, col):
        cell = self.cells.get((row, col))
        if cell is None:
            return ""
        return cell.display_value()

    # ── recalculation ──

    def recalc(self):
        return recalculate(self)

    # ── formatting ──

    def apply_format(self, row, col, fmt_dict):
        cell = self.get_cell(row, col)
        cell.fmt.apply_dict(fmt_dict)

    def get_format(self, row, col):
        return self.get_cell(row, col).fmt

    # ── row / column operations ──

    def insert_row(self, at):
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if r >= at:
                new_cells[(r + 1, c)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        new_heights = {}
        for r, h in self.row_heights.items():
            if r >= at:
                new_heights[r + 1] = h
            else:
                new_heights[r] = h
        self.row_heights = new_heights
        self.hidden_rows = {r + 1 if r >= at else r for r in self.hidden_rows}
        for rule in self.conditional_rules:
            if rule.top >= at:
                rule.top += 1
                rule.bottom += 1
            elif rule.bottom >= at:
                rule.bottom += 1

    def delete_row(self, at):
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if r == at:
                continue
            new_cells[(r - 1, c) if r > at else (r, c)] = cell
        self.cells = new_cells
        new_heights = {}
        for r, h in self.row_heights.items():
            if r == at:
                continue
            new_heights[r - 1 if r > at else r] = h
        self.row_heights = new_heights
        self.hidden_rows = {(r - 1 if r > at else r) for r in self.hidden_rows if r != at}
        new_rules = []
        for rule in self.conditional_rules:
            if rule.bottom < at:
                new_rules.append(rule)
            elif rule.top > at:
                rule.top -= 1
                rule.bottom -= 1
                new_rules.append(rule)
            else:
                rule.bottom -= 1
                if rule.bottom >= rule.top:
                    new_rules.append(rule)
        self.conditional_rules = new_rules

    def insert_col(self, at):
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if c >= at:
                new_cells[(r, c + 1)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        new_widths = {}
        for c, w in self.col_widths.items():
            if c >= at:
                new_widths[c + 1] = w
            else:
                new_widths[c] = w
        self.col_widths = new_widths
        self.hidden_cols = {c + 1 if c >= at else c for c in self.hidden_cols}
        for rule in self.conditional_rules:
            if rule.left >= at:
                rule.left += 1
                rule.right += 1
            elif rule.right >= at:
                rule.right += 1

    def delete_col(self, at):
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if c == at:
                continue
            new_cells[(r, c - 1) if c > at else (r, c)] = cell
        self.cells = new_cells
        new_widths = {}
        for c, w in self.col_widths.items():
            if c == at:
                continue
            new_widths[c - 1 if c > at else c] = w
        self.col_widths = new_widths
        self.hidden_cols = {(c - 1 if c > at else c) for c in self.hidden_cols if c != at}
        new_rules = []
        for rule in self.conditional_rules:
            if rule.right < at:
                new_rules.append(rule)
            elif rule.left > at:
                rule.left -= 1
                rule.right -= 1
                new_rules.append(rule)
            else:
                rule.right -= 1
                if rule.right >= rule.left:
                    new_rules.append(rule)
        self.conditional_rules = new_rules

    # ── dimensions ──

    def get_col_width(self, col, default=100):
        return self.col_widths.get(col, default)

    def get_row_height(self, row, default=28):
        return self.row_heights.get(row, default)

    def used_range(self):
        if not self.cells:
            return 0, 0, 0, 0
        max_r = max(r for r, _ in self.cells)
        max_c = max(c for _, c in self.cells)
        return 0, 0, max_r, max_c

    def unique_values_in_col(self, col, max_rows=10000):
        seen = set()
        for (r, c), cell in self.cells.items():
            if c == col and r < max_rows:
                v = cell.display_value()
                if v != "":
                    seen.add(v)
        return sorted(seen)

    # ── merged cells ──

    def add_merge(self, r1, c1, r2, c2):
        rect = (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))
        self.remove_merge(rect[0], rect[1])
        self.merged_cells.append(rect)
        return rect

    def remove_merge(self, row, col):
        self.merged_cells = [m for m in self.merged_cells
                              if not (m[0] <= row <= m[2] and m[1] <= col <= m[3])]

    def get_merge(self, row, col):
        for m in self.merged_cells:
            if m[0] <= row <= m[2] and m[1] <= col <= m[3]:
                return m
        return None

    def is_merged_origin(self, row, col):
        for m in self.merged_cells:
            if m[0] == row and m[1] == col:
                return True
        return False

    def is_merged_covered(self, row, col):
        for m in self.merged_cells:
            if m[0] <= row <= m[2] and m[1] <= col <= m[3]:
                return not (m[0] == row and m[1] == col)
        return False


# ───────────────────── Workbook ─────────────────────

class Workbook:
    def __init__(self):
        self.sheets = []
        self.active_index = 0
        self.file_path = None
        self.add_sheet("Sheet1")

    @property
    def active_sheet(self):
        if 0 <= self.active_index < len(self.sheets):
            return self.sheets[self.active_index]
        return None

    def add_sheet(self, name=None):
        if name is None or name.strip() == "":
            name = f"Sheet{len(self.sheets) + 1}"
        # ensure unique
        base = name
        i = 1
        existing = {s.name for s in self.sheets}
        while name in existing:
            name = f"{base}({i})"
            i += 1
        sheet = Worksheet(name)
        self.sheets.append(sheet)
        return sheet

    def delete_sheet(self, index):
        if len(self.sheets) <= 1:
            return False
        self.sheets.pop(index)
        if self.active_index >= len(self.sheets):
            self.active_index = len(self.sheets) - 1
        return True

    def rename_sheet(self, index, name):
        if 0 <= index < len(self.sheets):
            self.sheets[index].name = name

    def move_sheet(self, from_idx, to_idx):
        if 0 <= from_idx < len(self.sheets) and 0 <= to_idx < len(self.sheets):
            sheet = self.sheets.pop(from_idx)
            self.sheets.insert(to_idx, sheet)

    def duplicate_sheet(self, index):
        if 0 <= index < len(self.sheets):
            import copy
            original = self.sheets[index]
            new_name = f"{original.name}_copy"
            new_sheet = Worksheet(new_name)
            for (r, c), cell in original.cells.items():
                new_cell = Cell(raw=cell.raw, value=cell.value, fmt=cell.fmt.copy())
                new_sheet.cells[(r, c)] = new_cell
            new_sheet.col_widths = dict(original.col_widths)
            new_sheet.row_heights = dict(original.row_heights)
            new_sheet.frozen_rows = original.frozen_rows
            new_sheet.frozen_cols = original.frozen_cols
            new_sheet.conditional_rules = [ConditionalRule(**r.to_dict()) for r in original.conditional_rules]
            self.sheets.insert(index + 1, new_sheet)
            return new_sheet
        return None