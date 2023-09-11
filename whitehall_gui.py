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
from CircleWidget import *
from pyqtree import Index
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
    QGraphicsView, 
    QGraphicsScene, 
    QGraphicsProxyWidget, 
    QGraphicsPixmapItem, 
    QGridLayout
)
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt, QObject, QEvent


travel_images = ["nothing", "boat-100-white.png", "alley-100.png", "coach-100.png"]
investigators = ["yellow.png", "blue.png", "red.png"]
positions_dict = {}
quadtree = Index(bbox=(0, 0, 1800, 1800))

INVESTIGATOR_HEIGHT = 47
INVESTIGATOR_WIDTH = 10
OVERLAY_WIDTH = 22
MAP_BOARD_IMG = "images/jack.png"
JACK_FIG_IMG = "images/jack_fig.png"

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

class DragData:
    def __init__(self, item, x, y):
         self.item = item
         self.start_x = x
         self.start_y = y
         self.offset_x = 0
         self.offset_y = 0
         self.investigator_id = None
         self.crossing = None
         self.valid_crossings = []


class CustomGraphicsView(QGraphicsView):
    def __init__(self, gui, parent=None):
        super().__init__(parent)
        self.gui = gui
        self.drag_data = DragData(None, 0, 0)

    def mousePressEvent(self, event):
        mapped_pos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            if not wh.jack.godmode and wh.jack.it_is_jacks_turn:
                self.drag_data.item = None
                self.drag_data.investigator_id = None
                self.drag_data.crossing = None
                wh.jack.print("Investigators may not move after searching for clues or attempting an arrest.")
                wh.jack.print("Type <b>jack</b> when you are ready to have Jack take his turn.")
                return
            #print("Left button pressed")
            item = self.scene().itemAt(mapped_pos, self.transform())
            #print("Clicked on:", item)
            #print("Bounding rectangle:", item.boundingRect())
            for num in range(0,3):
                if item == self.gui.investigator_imgs[num]:
                    #print("You clicked on investigator:", num)
                    self.drag_data.investigator_id = num
                    self.drag_data.crossing = wh.jack.ipos[num]  # Save starting crossing in case investigator is released before being on a new crossing
                    self.drag_data.item = self.gui.investigator_imgs[num]
                    #allocation = self.investigator_imgs[num].get_allocation()
                    self.drag_data.start_x = self.drag_data.item.pos().x()
                    self.drag_data.start_y = self.drag_data.item.pos().y()
                    self.drag_data.offset_x = self.drag_data.start_x - mapped_pos.x()
                    self.drag_data.offset_y = self.drag_data.start_y - mapped_pos.y()
                    # Get a list of all crossings 2 away and save it to the drag_data
                    if not wh.jack.game_in_progress:
                        self.drag_data.valid_crossings = wh.starting_ipos
                    else:
                        self.drag_data.valid_crossings = wh.jack.investigator_crossing_options(num)
                        # Remove crossings that are occupied by other investigators
                        for pos in wh.jack.ipos:
                            if (pos != self.drag_data.crossing) and (pos in self.drag_data.valid_crossings):
                                self.drag_data.valid_crossings.remove(pos)
                    break;
        elif event.button() == Qt.RightButton:
            print("Right button pressed")
        # Handle other mouse buttons if needed
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            #print("Left button released")
            if self.drag_data.crossing != None and self.drag_data.investigator_id != None:
                # Save the ipos for this widget to the game state
                wh.jack.ipos[self.drag_data.investigator_id] = self.drag_data.crossing
            
                (x, y) = positions_dict[self.drag_data.crossing]
                self.gui.investigator_imgs[self.drag_data.investigator_id].setPos(
                    (x - INVESTIGATOR_WIDTH)/self.gui.scale, (y - INVESTIGATOR_HEIGHT)/self.gui.scale)
            
                # clear the dragging info - we have released the investigator
                self.drag_data.offset_x = 0
                self.drag_data.offset_y = 0
                self.drag_data.item = None
                self.drag_data.investigator_id = None
                self.drag_data.crossing = None
            
        elif event.button() == Qt.RightButton:
            print("Right button released")
        # Handle other mouse buttons if needed
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        mapped_pos = self.mapToScene(event.pos())
        #print("Mouse moved to scene coordinates:", mapped_pos.x(), mapped_pos.y())
        if None != self.drag_data.item :
            x = mapped_pos.x() + self.drag_data.offset_x
            y = mapped_pos.y() + self.drag_data.offset_y
                        
            # Check if we are over a crossing
            qx = mapped_pos.x()*self.gui.scale
            qy = mapped_pos.y()*self.gui.scale
            #print("Looking for crossing at:", qx, qy)
            id_list = quadtree.intersect((qx, qy, qx, qy))
            if id_list and ("c" in id_list[0]) and (id_list[0] in self.drag_data.valid_crossings or wh.jack.godmode):
                # Enforce a 2 crossing movement limit unless game hasn't started or in godmode
                
                (id_x, id_y) = positions_dict[ id_list[0]]
                #print("Found at location with ID:", id_list[0], positions_dict[ id_list[0]])
                self.drag_data.crossing = id_list[0]
                #Snap the image widget to the location so it looks like it is standing on it
                x = (id_x - INVESTIGATOR_WIDTH)/self.gui.scale
                y = (id_y - INVESTIGATOR_HEIGHT)/self.gui.scale
                # Save this new crossing as the place of origin for the inspector widget (in case we release it slightly off a crossing later)
                self.drag_data.start_x = x
                self.drag_data.start_y = y
                
            self.drag_data.item.setPos(x, y)
            self.gui.view.viewport().update() # On Windows 10, the pixmap would sometime leave behind ghost pieces.  Hopefully this fixes that.
        super().mouseMoveEvent(event)

def loadQPixmap(path):
    pixmap = QPixmap(path)
    if pixmap.isNull():
        print("Error: can not load pixmap:", path)
        exit()
    else:
        return pixmap
    
class WhiteHallGui(QWidget):
    def __init__(self):
        super().__init__()

        self.jack_token_pos = -1
        self.turn_buttons = []
        self.scale = 1
        
        self.crime_dictionary = {}
        self.crime_ref_pixmap = loadQPixmap("images/crime_overlay.png")
        
        self.clue_dictionary = {}
        self.clue_ref_pixmap = loadQPixmap("images/clue_overlay.png")
        
        self.jack_path_dictionary = {}
        self.jack_path_ref_pixmap = loadQPixmap("images/jack_path_overlay.png")
        
        # Create the dictionary and quadtree for quick location lookups
        self.create_positions_dictionary()
        
        # Create pixmaps for the investigators
        self.investigator_imgs = []
        self.investigator_ref_pixmaps = []
        for num in range (0,3):
            pixmap = QPixmap(f"images/{investigators[num]}")
            i_img = QGraphicsPixmapItem(pixmap)
            self.investigator_imgs.append(i_img)
            self.investigator_ref_pixmaps.append(pixmap)
            # TODO: Neeed some event handling for PyQt
            #i_img.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
            #i_img.connect("motion-notify-event", self.on_motion_notify)
            #i_img.connect("button-press-event", self.on_button_press)
        
        pixmap = QPixmap(JACK_FIG_IMG)
        self.jack_fig_ref_pixmap = pixmap
        self.jack_fig_item = QGraphicsPixmapItem(pixmap)
        
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
        self.image_scroll_area.setWidgetResizable(True)
        
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self, parent=self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
       
        scroll_content = QWidget()
        self.image_scroll_area.setWidget(self.view)
        
        self.pixmap_item = QGraphicsPixmapItem()

        self.scene.addItem(self.pixmap_item)
        self.position_investigators(add=True)
        
        # Add the widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(self.image_scroll_area)
        
        # Set the size policy and Collapsible attribute of the left and right widgets
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, True)
        
        # Set the size policy of the splitter
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set the sizes of the widgets in the splitter
        splitter.setSizes([self.width() // 8, 7 * self.width() // 8])
        
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
            radio_holder = QWidget()
            #radio_holder_layout= QGridLayout(radio_holder)
            radio_holder_layout= QVBoxLayout(radio_holder)
            radio_button = CircleLabelWidget(f"{i}", 40)
            #label = QLabel(f"{i}")
            #radio_holder_layout.addWidget(label, alignment=Qt.AlignCenter)
            radio_holder_layout.addWidget(radio_button, alignment=Qt.AlignCenter)
            
            #radio_button.setEnabled(True)
            overlay.addWidget(radio_holder)
            bottom_layout.addLayout(overlay)
            self.turn_buttons.append(overlay)
        
        main_layout.addWidget(bottom_widget)

        self.setLayout(main_layout)
        self.setWindowTitle("Whitehall Mystery Jack Automaton")
        
        # Pass a function and some necessary UI elements to the game engine 
        # so it can post things to the GUI with the proper context
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
        pixmap = loadQPixmap(MAP_BOARD_IMG)
        width = min(pixmap.width(), self.image_scroll_area.width())
        self.scale = pixmap.width()/width
        scaled_pixmap = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        self.pixmap_item.setPixmap(scaled_pixmap) 
        #print("Calling refresh board from update_pixmap")
        self.refresh_board()
        

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
            self.text_view.verticalScrollBar().setValue(self.text_view.verticalScrollBar().maximum())
    
        elif (output_type == wh.SPECIAL_TRAVEL_MSG):
            overlay = self.turn_buttons[wh.game_turn()+1]
            travel_type = msg[0]
            image = QPixmap(f"images/{travel_images[travel_type]}")
            image_widget = QLabel()
            image_widget.setPixmap(image)
            overlay.addWidget(image_widget)
            
            # Hide the radio button
            for i in range (0, overlay.count()):
                widget = overlay.widget(i)
                if not (isinstance(widget, QLabel)):
                    widget.hide()
            
            # need a second image to cover the second turn the coach took
            if travel_type == wh.COACH_MOVE:
                overlay = self.turn_buttons[wh.game_turn()+2]
                image_widget = QLabel()
                image_widget.setPixmap(image)
                overlay.addWidget(image_widget)
                
                # Hide the radio button
                for i in range (0, overlay.count()):
                    widget = overlay.widget(i)
                    if not (isinstance(widget, QLabel)):
                        widget.hide()
            
        elif (output_type == wh.NEW_ROUND_MSG):
            if (self.jack_token_pos != -1):
                # Temporarily remove the jack token so it isn't counted as an extra card overlay that needs to be removed.
                jack_overlay = self.turn_buttons[self.jack_token_pos]
                jack_widget = jack_overlay.widget(jack_overlay.count()-1)
                jack_overlay.removeWidget(jack_widget)
                #print("Temporarilly removing", jack_widget)
    
            # remove all special transportation cards from the turn track
            for overlay in self.turn_buttons:
                # There will only ever be at most one extra overlay per turn space
                if overlay.count() > 1:
                    widget = overlay.widget(1)
                    #print("Removing:", widget)
                    overlay.removeWidget(widget)
    
            # put the jack token back
            if (self.jack_token_pos != -1):
                jack_overlay.addWidget(jack_widget)
                #jack_overlay.show_all()
            
            # Make all the radio buttons visible again
            for overlay in self.turn_buttons:
                for i in range (0, overlay.count()):
                    widget = overlay.widget(i)
                    if not (isinstance(widget, QLabel)):
                        widget.setVisible(True)
            
            # Remove all clues
            for loc, item in self.clue_dictionary.items():
                self.scene.removeItem(item)
            self.clue_dictionary = {}
            
            # Remove all crimes
            for loc, item in self.crime_dictionary.items():
                self.scene.removeItem(item)
            self.crime_dictionary = {}
            
            # Remove all godmode Jack path indicators
            for loc, item in self.jack_path_dictionary.items():
                self.scene.removeItem(item)
            self.jack_path_dictionary = {}

        else:
            #print("Calling refresh board from process_outpt")
            self.refresh_board()
    
    def show_current_turn(self, curr_turn):
        # Reset all the buttons since they are not part of a group - we have to set each one manually
        for overlay in self.turn_buttons:
            for i in range (0, overlay.count()):
                widget = overlay.widget(i)
                if not (isinstance(widget, QLabel)):
                    widget.children()[1].setChecked(False)
        self.turn_buttons[curr_turn].widget(0).children()[1].setChecked(True)
    
    def place_jack_on_turn_track(self, curr_turn):        
        # Move the jack token to the current turn space
        #print("Curr turn:", curr_turn)
        curr_overlay = self.turn_buttons[curr_turn]        
        if (self.jack_token_pos == -1):
            image = QPixmap("images/jack-corner.png")
            image_widget = QLabel()
            #image_widget.setStyleSheet("border: 1px solid black;")  # Set the border style
            image_widget.setPixmap(image)
            jack_layer = curr_overlay.addWidget(image_widget)
        else:
            #print("Jack token pos:", self.jack_token_pos)
            prev_overlay = self.turn_buttons[self.jack_token_pos]
            jack_widget = prev_overlay.widget(prev_overlay.count()-1)
            #print("Jack widget is:", jack_widget)
            prev_overlay.removeWidget(jack_widget)
            jack_layer = curr_overlay.addWidget(jack_widget)
        #print("Jack layer is: ", jack_layer)

        self.jack_token_pos = curr_turn
        #print("  Jack token pos is now: ", self.jack_token_pos, "\n")
            
        curr_overlay.setCurrentIndex(jack_layer)
    
    
    def show_crimes(self):
        # We need a common scaled version of the crime indication overlay
        new_width = self.crime_ref_pixmap.width()/self.scale
        scaled_pixmap = self.crime_ref_pixmap.scaledToWidth(int(new_width), Qt.SmoothTransformation)
        
        # Reposition all the overlays based on the current map scale, adding any newly discovered crimes as needed
        for crime in wh.jack.crimes:
            if crime not in self.crime_dictionary:
                crime_img = QGraphicsPixmapItem()
                self.crime_dictionary[crime] = crime_img
                self.scene.addItem(crime_img)
                
            self.crime_dictionary[crime].setPixmap(scaled_pixmap)
            x, y = positions_dict[crime]
            self.crime_dictionary[crime].setPos((x - OVERLAY_WIDTH)/self.scale, (y - OVERLAY_WIDTH)/self.scale)
    
    def show_clues(self):
        # We need a common scaled version of the clue indication overlay
        new_width = self.clue_ref_pixmap.width()/self.scale
        scaled_pixmap = self.clue_ref_pixmap.scaledToWidth(int(new_width), Qt.SmoothTransformation)
        
        # Reposition all the overlays based on the current map scale, adding any newly discovered clues as needed
        for clue in wh.jack.clues:
            if clue not in self.clue_dictionary:
                clue_img = QGraphicsPixmapItem()
                self.clue_dictionary[clue] = clue_img
                self.scene.addItem(clue_img)
                
            self.clue_dictionary[clue].setPixmap(scaled_pixmap)
            x, y = positions_dict[clue]
            self.clue_dictionary[clue].setPos((x - OVERLAY_WIDTH)/self.scale, (y - OVERLAY_WIDTH)/self.scale)
        
    def refresh_board(self):
        curr_turn = wh.game_turn()
        
        self.show_current_turn(curr_turn)
        self.place_jack_on_turn_track(curr_turn)
        self.position_investigators()
        
        self.show_crimes()
        self.show_clues()
        
        self.do_godmode_board_update()
        
        # Adjust the scene size to match the content size
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
    

    def position_investigators(self, add=False):
        # Put the investigator playing pieces on the board
        for num in range (0,3):
            if add:
                self.scene.addItem(self.investigator_imgs[num])
            ipos = wh.jack.ipos[num]
            x, y = positions_dict[ipos]
            pixmap = self.investigator_ref_pixmaps[num]
            new_width = pixmap.width()/self.scale
            scaled_pixmap = pixmap.scaledToWidth(int(new_width), Qt.SmoothTransformation)
            self.investigator_imgs[num].setPixmap(scaled_pixmap)
            self.investigator_imgs[num].setPos((x - INVESTIGATOR_WIDTH)/self.scale, (y - INVESTIGATOR_HEIGHT)/self.scale)
    

    def do_godmode_board_update(self):
        if wh.jack.pos == 0:
            self.jack_fig_item.setVisible(False)
        else:
            if not self.jack_fig_item in self.scene.items():
                self.scene.addItem(self.jack_fig_item)
            x, y = positions_dict[wh.jack.pos]
            pixmap = self.jack_fig_ref_pixmap
            new_width = pixmap.width()/self.scale
            scaled_pixmap = pixmap.scaledToWidth(int(new_width), Qt.SmoothTransformation)
            self.jack_fig_item.setPixmap(scaled_pixmap)
            self.jack_fig_item.setPos((x - INVESTIGATOR_WIDTH)/self.scale, (y - INVESTIGATOR_HEIGHT)/self.scale)
            if not wh.jack.godmode:
                self.jack_fig_item.setVisible(False)
            else:
                self.jack_fig_item.setVisible(True)
                
                # Show Jack's prior movements
                # We need a common scaled version of the clue indication overlay
                new_width = self.jack_path_ref_pixmap.width()/self.scale
                scaled_pixmap = self.jack_path_ref_pixmap.scaledToWidth(int(new_width), Qt.SmoothTransformation)
    
                for path in wh.jack.path_used:
                    if path not in self.jack_path_dictionary:
                        path_img = QGraphicsPixmapItem()
                        self.jack_path_dictionary[path] = path_img
                        self.scene.addItem(path_img)
            
                    self.jack_path_dictionary[path].setPixmap(scaled_pixmap)
                    x, y = positions_dict[path]
                    self.jack_path_dictionary[path].setPos((x - OVERLAY_WIDTH)/self.scale, (y - OVERLAY_WIDTH)/self.scale)
            
    
    def self_test(self):
        print("GUI self tests completed.")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window = WhiteHallGui()
    window.showMaximized()



    sys.exit(app.exec_())
