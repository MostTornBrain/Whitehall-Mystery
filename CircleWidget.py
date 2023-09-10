from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QFontMetrics
from PyQt5.QtCore import Qt, QSize

class CircleLabelWidget(QWidget):
    def __init__(self, text, diameter=50, parent=None):
        super().__init__(parent)
        self.text = text
        self.diameter = diameter
        self.setMinimumSize(diameter, diameter)  # Set a minimum size for visibility
        self._checked = False
        
    def resizeEvent(self, event):
        # Adjust the size of the widget to maintain a circular shape
        size = min(self.width(), self.height())
        self.setFixedSize(QSize(size, size))
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        if (self._checked):
            brush_color = Qt.black
            pen_color = Qt.white
        else:
            brush_color = Qt.white
            pen_color = Qt.black
            
        # Draw the circular shape
        painter.setPen(QPen(Qt.black, 2))  # Set black pen with width 2
        painter.setBrush(brush_color)  # Replace with desired color
        painter.drawEllipse(self.rect().adjusted(3, 3, -3, -3))

        # Calculate the ideal font size to fit the text within the rectangle
        font_size = self.calculate_font_size(self.rect().adjusted(10, 10, -10, -10))
                
        # Draw the label
        painter.setPen(pen_color)
        painter.setFont(QFont("Arial", font_size))  # Replace with desired font and size
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

    def calculate_font_size(self, rect):
        # Start with a large font size
        font_size = 100

        # Create a QFontMetrics object to measure the text size
        font = QFont("Arial", font_size)  # Replace with desired font family
        font_metrics = QFontMetrics(font)

        # Reduce the font size until the text fits within the rectangle
        while font_metrics.width(self.text) > rect.width() or font_metrics.height() > rect.height():
            font_size -= 1
            font.setPointSize(font_size)
            font_metrics = QFontMetrics(font)

        return font_size

    def setChecked(self, value):
        self._checked = value
        self.update()  # Trigger a repaint of the widget
    
    @property
    def checked(self):
        return self._checked

    
    
if __name__ == "__main__":
    def run_standalone():
        app = QApplication([])

        window = QWidget()
        layout = QVBoxLayout(window)

        circle_label = CircleLabelWidget("1", 40)
        circle_label.setChecked(True)
        layout.addWidget(circle_label)

        window.show()
        app.exec()
    run_standalone()