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
import whitehall as wh
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPixmap

MAP_BOARD_IMG = "images/jack.png"

def string_present(s, nested_array):
    for sublist in nested_array:
        if s in sublist:
            return True
    return False
    
# Class to render the graph image of the playing board
class BaseGraphView(QMainWindow):
    def __init__(self, positions, edges):
        super().__init__()
        self.positions = positions
        self.edges = edges
        self.initGraph()

    def initGraph(self):
        self.setGeometry(0, 0, 800, 600)
        self.setWindowTitle('Graph Visualizer')

        self.view = QGraphicsView(self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.setCentralWidget(self.view)

        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)

        # Convert positions to a dictionary for easy lookup
        position_dict = {name: (x, y) for name, [x, y] in self.positions}

        line_pen = QPen(QColor("black"), 2)

        # Draw edges
        for start, end, _, edge_type in self.edges:
            if edge_type == 0:
                x1, y1 = position_dict[start]
                x2, y2 = position_dict[end]
                line_item = QGraphicsLineItem(x1, y1, x2, y2)
                line_item.setPen(line_pen)
                self.scene.addItem(line_item)

        # Node properties
        r = 19
        white_brush = QBrush(QColor("white"))  
        water_brush = QBrush(QColor(wh.WATER_COLOR))
        box_size = r / 1.5
        black_brush = QBrush(QColor("black"))  # Fill color for the small crossings
        gold_brush = QBrush(QColor(wh.STARTING_CROSSINGS_COLOR))  # Fill color for the starting crossings
    
        # Outline properties
        outline_color = QColor(173,173,173)
        outline_width = 3
        pen = QPen(outline_color, outline_width)


        # Draw nodes
        for name, [x, y] in self.positions:
            if 'c' in name:
                # draw a small black box
                rect = QGraphicsRectItem(QRectF(x - box_size/2, y - box_size/2, box_size, box_size))
                if name in wh.starting_ipos:
                    rect.setBrush(gold_brush)
                else:
                    rect.setBrush(black_brush)
                rect.setPen(pen)
                self.scene.addItem(rect)
            else:
                ellipse = QGraphicsEllipseItem(QRectF(x-r, y-r, 2*r, 2*r))
                font_color = QColor("black");
                if string_present(name, wh.quads):
                    ellipse.setBrush(white_brush)
                elif name in wh.water:
                    ellipse.setBrush(water_brush)
                else:
                    font_color = QColor("white");
                    ellipse.setBrush(black_brush)
                ellipse.setPen(pen)
                self.scene.addItem(ellipse)
            
                # Draw node label (centered)
                label = QGraphicsTextItem(name)
                font = QFont()
                font.setPixelSize(18)
                label.setFont(font)
                label.setDefaultTextColor(font_color)
                label_bound = label.boundingRect()
                label.setPos(x - label_bound.width() / 2, y - label_bound.height() / 2)
                self.scene.addItem(label)

                self.pixmap = QPixmap(1770, 1770)
                
        self.pixmap.fill(Qt.white)  # Fill pixmap with white color

        # Create a QPainter object and render the scene onto it
        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable anti-aliasing for the QPainter
        
        # Calculate the offset to center the scene within the QPixmap
        offset_x = (1770 - self.scene.sceneRect().width()) / 2
        offset_y = (1770 - self.scene.sceneRect().height()) / 2 - 12

        # Render the scene to the QPixmap, centered
        self.scene.render(painter, QRectF(offset_x, offset_y, self.scene.sceneRect().width(), self.scene.sceneRect().height()))

        # End painting
        painter.end()

    def getPixmap(self):
        return self.pixmap
        
    def save_to_png(self, filename):
        # Save the image to a file
        self.pixmap.save(filename)
        
if __name__ == '__main__':


    app = QApplication(sys.argv)
    ex = BaseGraphView(wh.positions, wh.edge_list)
    
    # save graph view to a PNG file
    ex.save_to_png(MAP_BOARD_IMG)
    
    sys.exit(app.exec_())
