"""
MIT License

Copyright (c) 2023 Brian Stormont

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sys
import signal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QTextEdit, QLabel, QRadioButton, QSizePolicy, QSplitter, QLineEdit
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt
from pyqtree import Index
import whitehall as wh

travel_images = ["nothing", "boat-100-white.png", "alley-100.png", "coach-100.png"]
investigators = ["yellow.png", "blue.png", "red.png"]
positions_dict = {}
quadtree = Index(bbox=(0, 0, 1500, 1500))

INVESTIGATOR_HEIGHT = 47
INVESTIGATOR_WIDTH = 10
MAP_BOARD_IMG = "images/jack.png"
MAP_SCALE = 2   # scale relative to the map bitmap image and the original x, y coordinate database for the locations and crossings

class WhiteHallGui(QWidget):
    def __init__(self):
        super().__init__()

        # Create the dictionary and quadtree for quick location lookups
        create_positions_dictionary()
        
        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a QSplitter widget for dividing the window
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Widget Layout
        left_layout = QVBoxLayout()
        
        # Set the layout for the left widget
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable Text Widget on the Left
        text_scroll_area = QScrollArea()
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_scroll_area.setWidgetResizable(True)
        text_scroll_area.setWidget(text_widget)

        # Set the size policy of the text scroll area to occupy 1/3 of the available width
        text_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        # Set the minimum and maximum width of the text scroll area
        text_scroll_area.setMinimumWidth(int(self.width() / 4))

        # One-Line Text Entry Window
        self.text_entry = QLineEdit()
        self.text_entry.setMinimumWidth(int(self.width() / 4))
        self.text_entry.returnPressed.connect(self.processText)
        
        # Add the text scroll area and text entry to the left layout
        left_layout.addWidget(text_scroll_area)
        left_layout.addWidget(self.text_entry)
        
        # Scrollable Image Widget on the Right
        self.image_scroll_area = QScrollArea()
        self.image_widget = QLabel()
        self.update_pixmap()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setWidget(self.image_widget)
        
        # Add the widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(self.image_scroll_area)
        
        # Set the size policy and Collapsible attribute of the left and right widgets
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, True)
        
        # Set the size policy of the splitter
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Set the sizes of the widgets in the splitter
        splitter.setSizes([self.width() // 3, 2 * self.width() // 3])
        
        splitter.splitterMoved.connect(self.update_pixmap)
        main_layout.addWidget(splitter)

        # Longer Widget with Radio Buttons below
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout()
        bottom_widget.setLayout(bottom_layout)
        
        radio_buttons = []
        for i in range(15):
            radio_button = QRadioButton(f"{i+1}")
            radio_button.setEnabled(False)
            bottom_layout.addWidget(radio_button)
            radio_buttons.append(radio_button)

        main_layout.addWidget(bottom_widget)

        self.setLayout(main_layout)
        self.setWindowTitle("Whitehall Mystery Jack Automaton")

    def processText(self):
        text = self.text_entry.text()
        self.text_entry.setText("")
        # Add your text processing logic here
        print(f"Entered Text: {text}")
        
    def resizeEvent(self, event):
        self.update_pixmap()

    def update_pixmap(self):
        pixmap = QPixmap(MAP_BOARD_IMG)
        if pixmap.isNull():
            print("Error: can not load map image.")
            exit()
        width = min(pixmap.width(), self.image_scroll_area.width())
        scaled_pixmap = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        self.image_widget.setPixmap(scaled_pixmap)
        
    def create_positions_dictionary(self):
        for item in wh.positions:
            id_value = item[0]
            x, y = item[1]
            x = x * MAP_SCALE
            y = y * MAP_SCALE
            positions_dict[id_value] = [x, y]
        
        # Also create a quad tree for efficient hit detection the crossings
        for id, (x, y) in positions_dict.items():
            quadtree.insert(item=id, bbox=(x-20, y-20, x+20, y+20))
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window = WhiteHallGui()
    window.show()



    sys.exit(app.exec_())
