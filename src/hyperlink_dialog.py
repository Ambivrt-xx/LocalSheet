"""
InsertHyperlinkDialog — dialog for adding/editing hyperlinks in cells.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel
)


class InsertHyperlinkDialog(QDialog):
    """Dialog for inserting or editing a hyperlink."""

    def __init__(self, current_url=None, current_text=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Hyperlink")
        self.setMinimumWidth(400)
        self._build_ui(current_url, current_text)

    def _build_ui(self, current_url, current_text):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.url_input = QLineEdit(current_url or "https://")
        self.url_input.setPlaceholderText("https://example.com")
        form.addRow("URL:", self.url_input)

        self.text_input = QLineEdit(current_text or "")
        self.text_input.setPlaceholderText("Display text (leave empty to show URL)")
        form.addRow("Display text:", self.text_input)

        layout.addLayout(form)
        layout.addWidget(QLabel(
            "<i>Tip: Clicking the cell with Ctrl will open the link in your browser.</i>"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_url(self):
        url = self.url_input.text().strip()
        if url and not url.startswith(("http://", "https://", "mailto:", "ftp://")):
            url = "https://" + url
        return url or None

    def get_display_text(self):
        return self.text_input.text().strip()