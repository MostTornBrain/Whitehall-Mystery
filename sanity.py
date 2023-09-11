# Quick and dirty utility for visually detecting if I have duplicate nodes defined for the same map location.
# (I did have one which I conicidentally discovered while playing the game - the game was claiming a space
# wasn't adjacent to an inspector while I was searching for clues.)

from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt5.QtGui import QColor
from graph_data import *

# Create the application and main window
app = QApplication([])
scene = QGraphicsScene()
view = QGraphicsView(scene)


# Draw the nodes
for node in positions:
    node_id, (x, y) = node
    rect_item = QGraphicsRectItem(x, y, 10, 10)
    rect_item.setBrush(QColor(0, 0, 0, 128))  # Black color with 50% alpha
    scene.addItem(rect_item)

# Show the view
view.show()

# Run the application event loop
app.exec_()
