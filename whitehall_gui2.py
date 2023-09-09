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
from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QScrollArea, 
    QTextEdit, 
    QLabel, 
    QRadioButton, 
    QSizePolicy, 
    QSplitter, 
    QLineEdit,
    QStackedLayout,
    QButtonGroup
)
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt, QObject, QEvent
from pyqtree import Index
import whitehall as wh

travel_images = ["nothing", "boat-100-white.png", "alley-100.png", "coach-100.png"]
investigators = ["yellow.png", "blue.png", "red.png"]
positions_dict = {}
quadtree = Index(bbox=(0, 0, 1700, 1700))

INVESTIGATOR_HEIGHT = 47
INVESTIGATOR_WIDTH = 10
MAP_BOARD_IMG = "images/jack.png"

class ReadOnlyRadioButton(QRadioButton):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)  # Make the radio button checkable
        #self.setEnabled(False)  # Disable user interaction

    def mousePressEvent(self, event):
        event.ignore()  # Ignore the mouse press event

    def mouseReleaseEvent(self, event):
        event.ignore()  # Ignore the mouse release event

    def keyPressEvent(self, event):
        event.ignore()  # Ignore key press events

    def keyReleaseEvent(self, event):
        event.ignore()  # Ignore key release events

# Recognize the ANSI escape sequence for BOLD text
def add_text_with_tags(text_view, text):
    # Get the current text cursor position
    cursor = text_view.textCursor()

    # Move the cursor to the end of the text
    cursor.movePosition(cursor.End)

    # Set the new position of the text cursor
    text_view.setTextCursor(cursor)
    
    msg = ""
    segments = text.split("\x1b[1m")
    for segment in segments:
        if "\x1b[0m" in segment:
            parts = segment.split("\x1b[0m")
            msg = msg + "<b>"
            msg = msg + parts[0]
            msg = msg + "</b>"
            if len(parts) > 1:
                msg = msg + parts[1]
        else:
            msg = msg + segment
    
    text_view.append(msg.replace("\n", "<br/>"))


class ImageLabel(QLabel):
    def __init__(self, master, parent=None):
        super().__init__(parent)
        self.master = master
        
    def event(self, event):
        if event.type() == QEvent.MouseMove:
            position = event.pos()
            print(position.x() * self.master.scale, position.y() * self.master.scale)
        return super().event(event)

class WhiteHallGui(QWidget):
    def __init__(self):
        super().__init__()

        self.jack_token_pos = -1
        self.turn_buttons = []
        
        # Create the dictionary and quadtree for quick location lookups
        self.create_positions_dictionary()
        
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
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        text_scroll_area.setWidgetResizable(True)
        text_scroll_area.setWidget(self.text_view)

        # Set the size policy of the text scroll area to occupy 1/3 of the available width
        text_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
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
        self.image_widget = ImageLabel(self)
                
        self.update_pixmap()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setWidget(self.image_widget)

        image_overlay = QStackedLayout()
        image_overlay.setStackingMode(QStackedLayout.StackAll)
        image_overlay.addWidget(self.image_scroll_area)
        
        right_widget = QWidget()
        #right_layout = QHBoxLayout()
        right_widget.setLayout(image_overlay)
        
        # Add the widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
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
        bottom_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Set fixed vertical size policy
        
        for i in range(0, 16):
            overlay = QStackedLayout()
            overlay.setStackingMode(QStackedLayout.StackAll)
            radio_button = ReadOnlyRadioButton(f"{i}")
            radio_button.setEnabled(True)
            overlay.addWidget(radio_button)
            overlay.setAlignment(radio_button, Qt.AlignCenter)
            bottom_layout.addLayout(overlay)
            self.turn_buttons.append(overlay)
        
        bottom_layout.setAlignment(Qt.AlignCenter)  # Align the bottom_layout to center
        main_layout.addWidget(bottom_widget)

        self.setLayout(main_layout)
        self.setWindowTitle("Whitehall Mystery Jack Automaton")
        
        # Pass a function and some necessary UI elements to the game engine so it can post things to the GUI with the proper context
        wh.register_gui_self_test(self.self_test)
        wh.register_output_reporter(self.process_output)    
        wh.welcome()
        self.refresh_board()
    
    def process_command_helper(self, command):    
        # Append the command to the text view with bold formatting
        self.text_view.insertHtml(f"<br/><b>> {command}</b><br/>")
    
        # Perform actions based on the command
        wh.process_input(command)
        self.text_entry.setText("")
        self.text_entry.setReadOnly(False)
        return False

    def processText(self):
        text = self.text_entry.text()
        self.text_entry.setText("Jack is thinking...")
        # Add your text processing logic here
        self.text_entry.setReadOnly(True)
        self.process_command_helper(text)
        
    def resizeEvent(self, event):
        self.update_pixmap()

    def update_pixmap(self):
        pixmap = QPixmap(MAP_BOARD_IMG)
        if pixmap.isNull():
            print("Error: can not load map image.")
            exit()
        width = min(pixmap.width(), self.image_scroll_area.width())
        self.scale = pixmap.width()/width
        scaled_pixmap = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        self.image_widget.setPixmap(scaled_pixmap)
        

    def create_positions_dictionary(self):
        for item in wh.positions:
            id_value = item[0]
            x, y = item[1]
            positions_dict[id_value] = [x, y]
        
        # Also create a quad tree for efficient hit detection the crossings
        for id, (x, y) in positions_dict.items():
            quadtree.insert(item=id, bbox=(x-20, y-20, x+20, y+20))


    def process_output(self, output_type, *msg):
        if (output_type == wh.TEXT_MSG):
            m = ' '.join(str(arg) for arg in msg)
            add_text_with_tags(self.text_view, f"{m}\n")
    
        elif (output_type == wh.SPECIAL_TRAVEL_MSG):
            # FIXME
            overlay = self.turn_buttons[wh.game_turn()+1]
            travel_type = msg[0]
            image = Gtk.Image.new_from_file(f"images/{travel_images[travel_type]}")
            overlay.add_overlay(image)
            overlay.show_all()
    
            # need a second image to cover the second turn the coach took
            if travel_type == wh.COACH_MOVE:
                # FIXME
                overlay = self.turn_buttons[wh.game_turn()+2]
                image = Gtk.Image.new_from_file(f"images/{travel_images[travel_type]}")
                overlay.add_overlay(image)
                #overlay.show_all()
        
        elif (output_type == wh.NEW_ROUND_MSG):
            if (self.jack_token_pos != -1):
                # Temporarily remove the jack token so it isn't counted as an extra card overlay that needs to be removed.
                jack_overlay = self.turn_buttons[self.jack_token_pos]
                jack_widget = jack_overlay.widget(jack_overlay.count()-1)
                jack_overlay.removeWidget(jack_widget)
                print("Temporarilly removing", jack_widget)
    
            # remove all special transportation cards from the turn track
            for overlay in self.turn_buttons:
                # There will only ever be at most one extra overlay per turn space
                if overlay.count() > 1:
                    widget = overlay.widget(1)
                    print("Removing:", widget)
                    overlay.removeWidget(widget)
    
            # put the jack token back
            if (self.jack_token_pos != -1):
                jack_overlay.addWidget(jack_widget)
                #jack_overlay.show_all()
        else:
            self.refresh_board()
    
    def refresh_board(self):
        curr_turn = wh.game_turn()
        # Reset all the buttons since they are not part of a group - we have to set each one manually
        for overlay in self.turn_buttons:
            for i in range (0, overlay.count()):
                widget = overlay.widget(i)
                if (isinstance(widget, QRadioButton)):
                    widget.setChecked(False)
        self.turn_buttons[curr_turn].widget(0).setChecked(True)
                
        # Move the jack token to the current turn space
        curr_overlay = self.turn_buttons[curr_turn]        
        if (self.jack_token_pos == -1):
            image = QPixmap("images/jack-corner.png")
            image_widget = QLabel()
            image_widget.setStyleSheet("border: 1px solid black;")  # Set the border style
            image_widget.setPixmap(image)
            jack_layer = curr_overlay.addWidget(image_widget)
        else:
            prev_overlay = self.turn_buttons[self.jack_token_pos]
            jack_widget = prev_overlay.widget(prev_overlay.count()-1)
            prev_overlay.removeWidget(jack_widget)
            jack_layer = curr_overlay.addWidget(jack_widget)
        print("Jack layer is", jack_layer)
        curr_overlay.setCurrentIndex(jack_layer)
        
        #curr_overlay.show_all()
        self.jack_token_pos = curr_turn
        
        return # FIXME
        
        # Put the investigator playing pieces on the board
        fixed_children = self.fixed_frame.get_children()
        for num in range (0,3):
            if self.investigator_imgs[num] in fixed_children:
                self.fixed_frame.remove(self.investigator_imgs[num]) 
        for num in range (0,3):
            ipos = wh.jack.ipos[num]
            x, y = positions_dict[ipos]
            self.fixed_frame.put(self.investigator_imgs[num], x - INVESTIGATOR_WIDTH, y - INVESTIGATOR_HEIGHT)
    
    def self_test(self):
        print("GUI self tests completed.")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window = WhiteHallGui()
    window.show()



    sys.exit(app.exec_())
