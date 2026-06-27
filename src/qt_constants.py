"""
Centralised PyQt6 enum aliases so the rest of the code stays readable.
PyQt6 requires fully-scoped enum access (e.g. Qt.ItemDataRole.DisplayRole).
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QFrame
from PyQt6.QtGui import QItemSelectionModel

# ---- ItemDataRole ----
DisplayRole = Qt.ItemDataRole.DisplayRole
EditRole = Qt.ItemDataRole.EditRole
FontRole = Qt.ItemDataRole.FontRole
BackgroundRole = Qt.ItemDataRole.BackgroundRole
ForegroundRole = Qt.ItemDataRole.ForegroundRole
TextAlignmentRole = Qt.ItemDataRole.TextAlignmentRole
ToolTipRole = Qt.ItemDataRole.ToolTipRole
SizeHintRole = Qt.ItemDataRole.SizeHintRole

# ---- ItemFlag ----
ItemIsEnabled = Qt.ItemFlag.ItemIsEnabled
ItemIsSelectable = Qt.ItemFlag.ItemIsSelectable
ItemIsEditable = Qt.ItemFlag.ItemIsEditable

# ---- AlignmentFlag ----
AlignLeft = Qt.AlignmentFlag.AlignLeft
AlignCenter = Qt.AlignmentFlag.AlignCenter
AlignRight = Qt.AlignmentFlag.AlignRight
AlignVCenter = Qt.AlignmentFlag.AlignVCenter

# ---- Key ----
Key_Return = Qt.Key.Key_Return
Key_Enter = Qt.Key.Key_Enter
Key_Tab = Qt.Key.Key_Tab
Key_Backtab = Qt.Key.Key_Backtab
Key_Escape = Qt.Key.Key_Escape
Key_Delete = Qt.Key.Key_Delete
Key_Backspace = Qt.Key.Key_Backspace
Key_Insert = Qt.Key.Key_Insert
Key_C = Qt.Key.Key_C
Key_V = Qt.Key.Key_V
Key_X = Qt.Key.Key_X
Key_Z = Qt.Key.Key_Z
Key_Y = Qt.Key.Key_Y
Key_A = Qt.Key.Key_A
Key_F = Qt.Key.Key_F
Key_S = Qt.Key.Key_S
Key_O = Qt.Key.Key_O
Key_N = Qt.Key.Key_N
Key_Home = Qt.Key.Key_Home
Key_End = Qt.Key.Key_End
Key_Left = Qt.Key.Key_Left
Key_Right = Qt.Key.Key_Right
Key_Up = Qt.Key.Key_Up
Key_Down = Qt.Key.Key_Down
Key_F2 = Qt.Key.Key_F2
Key_PageUp = Qt.Key.Key_PageUp
Key_PageDown = Qt.Key.Key_PageDown

# ---- KeyboardModifier ----
ControlModifier = Qt.KeyboardModifier.ControlModifier
ShiftModifier = Qt.KeyboardModifier.ShiftModifier
NoModifier = Qt.KeyboardModifier.NoModifier
AltModifier = Qt.KeyboardModifier.AltModifier

# ---- MouseButton ----
LeftButton = Qt.MouseButton.LeftButton
RightButton = Qt.MouseButton.RightButton
MiddleButton = Qt.MouseButton.MiddleButton

# ---- ContextMenuPolicy ----
CustomContextMenu = Qt.ContextMenuPolicy.CustomContextMenu

# ---- ScrollBarPolicy ----
ScrollBarAlwaysOff = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
ScrollBarAsNeeded = Qt.ScrollBarPolicy.ScrollBarAsNeeded

# ---- Orientation ----
Horizontal = Qt.Orientation.Horizontal
Vertical = Qt.Orientation.Vertical

# ---- FocusPolicy ----
NoFocus = Qt.FocusPolicy.NoFocus
StrongFocus = Qt.FocusPolicy.StrongFocus

# ---- QAbstractItemView enums ----
SelectItems = QAbstractItemView.SelectionBehavior.SelectItems
SelectRows = QAbstractItemView.SelectionBehavior.SelectRows
SelectColumns = QAbstractItemView.SelectionBehavior.SelectColumns

SingleSelection = QAbstractItemView.SelectionMode.SingleSelection
ExtendedSelection = QAbstractItemView.SelectionMode.ExtendedSelection

MoveDown = QAbstractItemView.CursorAction.MoveDown
MoveUp = QAbstractItemView.CursorAction.MoveUp
MoveLeft = QAbstractItemView.CursorAction.MoveLeft
MoveRight = QAbstractItemView.CursorAction.MoveRight

EditingState = QAbstractItemView.State.EditingState

EditKeyPressed = QAbstractItemView.EditTrigger.EditKeyPressed
DoubleClicked = QAbstractItemView.EditTrigger.DoubleClicked
SelectedClicked = QAbstractItemView.EditTrigger.SelectedClicked
AnyKeyPressed = QAbstractItemView.EditTrigger.AnyKeyPressed

NoHint = QAbstractItemView.EndEditHint.NoHint

Interactive = QHeaderView.ResizeMode.Interactive
Fixed = QHeaderView.ResizeMode.Fixed
Stretch = QHeaderView.ResizeMode.Stretch

NoFrame = QFrame.Shape.NoFrame

# ---- QItemSelectionModel ----
ClearAndSelect = QItemSelectionModel.SelectionFlag.ClearAndSelect
Select = QItemSelectionModel.SelectionFlag.Select
Deselect = QItemSelectionModel.SelectionFlag.Deselect
Current = QItemSelectionModel.SelectionFlag.Current
Rows = QItemSelectionModel.SelectionFlag.Rows
Columns = QItemSelectionModel.SelectionFlag.Columns