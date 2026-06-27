"""
ChartWidget — renders bar, line, and pie charts using QPainter.
Self-contained, no QtCharts dependency required.
"""
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QWidget


# Palette of distinct chart colors
CHART_COLORS = [
    "#4285f4", "#ea4335", "#fbbc04", "#34a853",
    "#ff6d01", "#46bdc6", "#7e57c2", "#ec407a",
    "#9ccc65", "#5c6bc0", "#ffca28", "#26a69a",
]


class ChartWidget(QWidget):
    """Renders a chart from a list of (label, value) pairs."""

    def __init__(self, chart_type='bar', labels=None, values=None, title="", parent=None):
        super().__init__(parent)
        self.chart_type = chart_type
        self.labels = labels or []
        self.values = values or []
        self.title = title
        self.setMinimumSize(500, 350)
        self.setStyleSheet("background: white;")

    def set_data(self, chart_type, labels, values, title=""):
        self.chart_type = chart_type
        self.labels = labels
        self.values = values
        self.title = title
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(self.rect(), QColor("white"))

        if not self.values:
            painter.setPen(QColor("#999"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data to display")
            return

        # Draw title
        title_h = 30 if self.title else 0
        if self.title:
            font = QFont("Arial", 12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#333"))
            painter.drawText(QRectF(0, 5, w, title_h), Qt.AlignmentFlag.AlignCenter, self.title)

        chart_rect = QRectF(40, title_h + 10, w - 80, h - title_h - 40)

        if self.chart_type == 'bar':
            self._draw_bar(painter, chart_rect)
        elif self.chart_type == 'line':
            self._draw_line(painter, chart_rect)
        elif self.chart_type == 'pie':
            self._draw_pie(painter, chart_rect)

    def _draw_bar(self, painter, rect):
        n = len(self.values)
        max_val = max(self.values) if self.values else 1
        if max_val == 0:
            max_val = 1
        min_val = min(min(self.values), 0) if self.values else 0

        painter.setPen(QPen(QColor("#e0e0e0"), 1, Qt.PenStyle.DashLine))
        font = QFont("Arial", 8)
        painter.setFont(font)
        grid_steps = 5
        for i in range(grid_steps + 1):
            y = rect.bottom() - (rect.height() / grid_steps) * i
            val = min_val + (max_val - min_val) * i / grid_steps
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(QColor("#999"))
            painter.drawText(QRectF(rect.left() - 38, y - 8, 35, 16),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             self._format_num(val))
            painter.setPen(QPen(QColor("#e0e0e0"), 1, Qt.PenStyle.DashLine))

        painter.setPen(QPen(QColor("#666"), 1))
        painter.drawLine(QPointF(rect.left(), rect.top()), QPointF(rect.left(), rect.bottom()))
        painter.drawLine(QPointF(rect.left(), rect.bottom()), QPointF(rect.right(), rect.bottom()))

        bar_w = rect.width() / (n * 1.5) if n > 0 else 0
        gap = bar_w * 0.5
        zero_y = rect.bottom() - (0 - min_val) / (max_val - min_val) * rect.height() if max_val != min_val else rect.bottom()

        for i, val in enumerate(self.values):
            x = rect.left() + gap + i * (bar_w + gap)
            bar_h = (val - min_val) / (max_val - min_val) * rect.height() if max_val != min_val else 0
            if val >= 0:
                y_top = zero_y - (val / max_val) * (zero_y - rect.top()) if max_val > 0 else zero_y
                bar_rect = QRectF(x, y_top, bar_w, zero_y - y_top)
            else:
                bar_rect = QRectF(x, zero_y, bar_w, abs(val) / abs(min_val) * (rect.bottom() - zero_y) if min_val < 0 else 0)

            color = QColor(CHART_COLORS[i % len(CHART_COLORS)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(110), 1))
            painter.drawRect(bar_rect)

            painter.setPen(QColor("#333"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(QRectF(x, bar_rect.top() - 14, bar_w, 12),
                             Qt.AlignmentFlag.AlignCenter, self._format_num(val))

            if i < len(self.labels):
                painter.setPen(QColor("#666"))
                painter.drawText(QRectF(x - gap, rect.bottom() + 4, bar_w + gap * 2, 16),
                                 Qt.AlignmentFlag.AlignCenter, str(self.labels[i]))

    def _draw_line(self, painter, rect):
        n = len(self.values)
        max_val = max(self.values) if self.values else 1
        min_val = min(self.values) if self.values else 0
        if max_val == min_val:
            max_val = min_val + 1

        painter.setPen(QPen(QColor("#e0e0e0"), 1, Qt.PenStyle.DashLine))
        painter.setFont(QFont("Arial", 8))
        grid_steps = 5
        for i in range(grid_steps + 1):
            y = rect.bottom() - (rect.height() / grid_steps) * i
            val = min_val + (max_val - min_val) * i / grid_steps
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            painter.setPen(QColor("#999"))
            painter.drawText(QRectF(rect.left() - 38, y - 8, 35, 16),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             self._format_num(val))
            painter.setPen(QPen(QColor("#e0e0e0"), 1, Qt.PenStyle.DashLine))

        painter.setPen(QPen(QColor("#666"), 1))
        painter.drawLine(QPointF(rect.left(), rect.top()), QPointF(rect.left(), rect.bottom()))
        painter.drawLine(QPointF(rect.left(), rect.bottom()), QPointF(rect.right(), rect.bottom()))

        if n < 2:
            return

        step_x = rect.width() / (n - 1)
        points = []
        for i, val in enumerate(self.values):
            x = rect.left() + i * step_x
            y = rect.bottom() - (val - min_val) / (max_val - min_val) * rect.height()
            points.append(QPointF(x, y))

        path = QPainterPath()
        path.moveTo(points[0])
        for p in points:
            path.lineTo(p)
        path.lineTo(QPointF(points[-1].x(), rect.bottom()))
        path.lineTo(QPointF(points[0].x(), rect.bottom()))
        path.closeSubpath()
        fill_color = QColor(CHART_COLORS[0])
        fill_color.setAlpha(40)
        painter.fillPath(path, QBrush(fill_color))

        painter.setPen(QPen(QColor(CHART_COLORS[0]), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path2 = QPainterPath()
        path2.moveTo(points[0])
        for p in points:
            path2.lineTo(p)
        painter.drawPath(path2)

        for p in points:
            painter.setBrush(QBrush(QColor(CHART_COLORS[0])))
            painter.setPen(QPen(QColor("white"), 2))
            painter.drawEllipse(p, 4, 4)

        painter.setPen(QColor("#666"))
        painter.setFont(QFont("Arial", 8))
        for i, p in enumerate(points):
            if i < len(self.labels):
                painter.drawText(QRectF(p.x() - step_x / 2, rect.bottom() + 4, step_x, 16),
                                 Qt.AlignmentFlag.AlignCenter, str(self.labels[i]))

    def _draw_pie(self, painter, rect):
        total = sum(v for v in self.values if v > 0)
        if total == 0:
            painter.setPen(QColor("#999"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No positive values")
            return

        side = min(rect.width() * 0.6, rect.height())
        pie_rect = QRectF(rect.left() + 20, rect.top(), side, side)
        legend_x = pie_rect.right() + 30

        start_angle = 90 * 16
        for i, val in enumerate(self.values):
            if val <= 0:
                continue
            angle = int(val / total * 360 * 16)
            color = QColor(CHART_COLORS[i % len(CHART_COLORS)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("white"), 2))
            painter.drawPie(pie_rect, start_angle, -angle)
            start_angle -= angle

        painter.setFont(QFont("Arial", 9))
        ly = rect.top()
        for i, val in enumerate(self.values):
            if val <= 0:
                continue
            color = QColor(CHART_COLORS[i % len(CHART_COLORS)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            painter.drawRect(QRectF(legend_x, ly + 2, 12, 12))
            label = self.labels[i] if i < len(self.labels) else f"Item {i+1}"
            pct = val / total * 100
            painter.setPen(QColor("#333"))
            painter.drawText(QRectF(legend_x + 18, ly, 150, 16),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             f"{label} ({pct:.1f}%)")
            ly += 22

    @staticmethod
    def _format_num(val):
        if val == int(val):
            return str(int(val))
        return f"{val:.1f}"