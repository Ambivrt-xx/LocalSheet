"""
InsertFunctionDialog — categorized formula builder with descriptions.
Lets users browse and insert functions into the formula bar.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QTextEdit, QPushButton, QDialogButtonBox, QSplitter
)


FUNCTION_CATEGORIES = {
    "Math": [
        ("SUM", "SUM(range)", "Adds all numbers in a range of cells."),
        ("AVERAGE", "AVERAGE(range)", "Returns the average of its arguments."),
        ("COUNT", "COUNT(range)", "Counts how many numbers are in the list."),
        ("MAX", "MAX(range)", "Returns the maximum value in a list."),
        ("MIN", "MIN(range)", "Returns the minimum value in a list."),
        ("ABS", "ABS(number)", "Returns the absolute value of a number."),
        ("ROUND", "ROUND(number, digits)", "Rounds a number to a specified number of digits."),
        ("ROUNDUP", "ROUNDUP(number, digits)", "Rounds a number up, away from zero."),
        ("ROUNDDOWN", "ROUNDDOWN(number, digits)", "Rounds a number down, toward zero."),
        ("SQRT", "SQRT(number)", "Returns the square root of a number."),
        ("POWER", "POWER(base, exponent)", "Returns the result of a number raised to a power."),
        ("MOD", "MOD(number, divisor)", "Returns the remainder from division."),
        ("STDEV", "STDEV(range)", "Estimates standard deviation based on a sample."),
        ("VAR", "VAR(range)", "Estimates variance based on a sample."),
        ("MEDIAN", "MEDIAN(range)", "Returns the median of the given numbers."),
        ("MODE", "MODE(range)", "Returns the most common value in a data set."),
    ],
    "Logical": [
        ("IF", "IF(test, val_if_true, val_if_false)", "Returns one value if true, another if false."),
        ("AND", "AND(cond1, cond2, ...)", "Returns TRUE if all arguments are TRUE."),
        ("OR", "OR(cond1, cond2, ...)", "Returns TRUE if any argument is TRUE."),
        ("NOT", "NOT(value)", "Reverses the logic of its argument."),
        ("IFERROR", "IFERROR(value, value_if_error)", "Returns a value if error, else the value."),
    ],
    "Text": [
        ("CONCATENATE", "CONCATENATE(text1, text2, ...)", "Joins several text items into one."),
        ("LEFT", "LEFT(text, num_chars)", "Returns the leftmost characters from a text."),
        ("RIGHT", "RIGHT(text, num_chars)", "Returns the rightmost characters from a text."),
        ("MID", "MID(text, start, length)", "Returns a specific number of characters from text."),
        ("LEN", "LEN(text)", "Returns the number of characters in a text string."),
        ("UPPER", "UPPER(text)", "Converts text to uppercase."),
        ("LOWER", "LOWER(text)", "Converts text to lowercase."),
        ("TRIM", "TRIM(text)", "Removes spaces from text."),
        ("SUBSTITUTE", "SUBSTITUTE(text, old, new, [n])", "Replaces text within a string."),
        ("TEXT", "TEXT(value, format)", "Formats a number and converts it to text."),
        ("REPT", "REPT(text, times)", "Repeats text a given number of times."),
    ],
    "Date & Time": [
        ("TODAY", "TODAY()", "Returns the current date."),
        ("NOW", "NOW()", "Returns the current date and time."),
        ("DATE", "DATE(year, month, day)", "Creates a date from year, month, day."),
        ("YEAR", "YEAR(date)", "Returns the year of a date."),
        ("MONTH", "MONTH(date)", "Returns the month of a date."),
        ("DAY", "DAY(date)", "Returns the day of a date."),
        ("HOUR", "HOUR(time)", "Returns the hour of a time."),
        ("MINUTE", "MINUTE(time)", "Returns the minute of a time."),
        ("SECOND", "SECOND(time)", "Returns the second of a time."),
        ("WEEKDAY", "WEEKDAY(date)", "Returns the day of the week (1-7)."),
        ("DATEDIF", "DATEDIF(date1, date2, unit)", "Returns the difference between two dates."),
    ],
    "Lookup": [
        ("VLOOKUP", "VLOOKUP(lookup, table, col, [range_lookup])", "Searches a column for a value."),
        ("HLOOKUP", "HLOOKUP(lookup, table, row, [range_lookup])", "Searches a row for a value."),
        ("XLOOKUP", "XLOOKUP(lookup, found, return, [not_found])", "Modern lookup with fallback."),
        ("INDEX", "INDEX(array, row, [col])", "Returns a value from a table by position."),
        ("MATCH", "MATCH(lookup, array, [type])", "Returns the position of an item in an array."),
    ],
    "Statistical": [
        ("COUNTIF", "COUNTIF(range, criteria)", "Counts cells that meet a condition."),
        ("SUMIF", "SUMIF(range, criteria, [sum_range])", "Adds cells that meet a condition."),
        ("AVERAGEIF", "AVERAGEIF(range, criteria, [avg_range])", "Averages cells that meet a condition."),
        ("SUMIFS", "SUMIFS(sum_range, crit_range, crit, ...)", "Sums cells that meet multiple conditions."),
        ("COUNTA", "COUNTA(range)", "Counts non-empty cells."),
        ("COUNTBLANK", "COUNTBLANK(range)", "Counts empty cells."),
        ("RANK", "RANK(number, range, [order])", "Returns the rank of a number in a list."),
    ],
}


class InsertFunctionDialog(QDialog):
    """Dialog for browsing and inserting spreadsheet functions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Function")
        self.setMinimumSize(480, 420)
        self._selected = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Category:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(sorted(FUNCTION_CATEGORIES.keys()))
        self.cat_combo.currentTextChanged.connect(self._populate_functions)
        top.addWidget(self.cat_combo, 1)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.func_list = QListWidget()
        self.func_list.currentRowChanged.connect(self._on_select)
        splitter.addWidget(self.func_list)

        self.desc_edit = QTextEdit()
        self.desc_edit.setReadOnly(True)
        self.desc_edit.setMaximumHeight(80)
        splitter.addWidget(self.desc_edit)

        layout.addWidget(splitter, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate_functions()

    def _populate_functions(self):
        cat = self.cat_combo.currentText()
        self.func_list.clear()
        for name, syntax, desc in FUNCTION_CATEGORIES.get(cat, []):
            self.func_list.addItem(f"{name}  -  {syntax}")
        if self.func_list.count() > 0:
            self.func_list.setCurrentRow(0)

    def _on_select(self, row):
        cat = self.cat_combo.currentText()
        funcs = FUNCTION_CATEGORIES.get(cat, [])
        if 0 <= row < len(funcs):
            name, syntax, desc = funcs[row]
            self.desc_edit.setPlainText(f"Syntax: {syntax}\n\n{desc}")
            self._selected = name
        else:
            self.desc_edit.clear()
            self._selected = None

    def _on_accept(self):
        if self._selected:
            self.accept()
        else:
            self.reject()

    def get_function(self):
        """Return the selected function name, or None."""
        return self._selected