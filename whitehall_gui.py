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
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Pango, Gdk, GLib
from pyqtree import Index
import whitehall as wh

travel_images = ["nothing", "boat-100-white.png", "alley-100.png", "coach-100.png"]
investigators = ["yellow.png", "blue.png", "red.png"]
positions_dict = {}
quadtree = Index(bbox=(0, 0, 1500, 1500))
SCALE = 0.78
INVESTIGATOR_HEIGHT = 45

def is_point_within_widget(widget, x, y):
    allocation = widget.get_allocation()
    x_bounds = allocation.x, allocation.x + allocation.width
    y_bounds = allocation.y, allocation.y + allocation.height

    return x_bounds[0] <= x <= x_bounds[1] and y_bounds[0] <= y <= y_bounds[1]

def create_positions_dictionary():
    for item in wh.positions:
        id_value = item[0]
        x, y = item[1]
        x = x * SCALE
        y = y * SCALE
        positions_dict[id_value] = [x, y]
        
    # Also create a quad tree for efficient hit detection the crossings
    for id, (x, y) in positions_dict.items():
        quadtree.insert(item=id, bbox=(x-20, y-20, x+20, y+20))

# Recognize the ANSI escape sequence for BOLD text
def add_text_with_tags(text_view, text):
    buffer = text_view.get_buffer()

    segments = text.split("\x1b[1m")
    for segment in segments:
        if "\x1b[0m" in segment:
            parts = segment.split("\x1b[0m")
            buffer.insert_with_tags_by_name(buffer.get_end_iter(), parts[0], "bold")
            if len(parts) > 1:
                buffer.insert(buffer.get_end_iter(), parts[1])
        else:
            buffer.insert(buffer.get_end_iter(), segment)

def _autoscroll(self, *args):
    """The actual scrolling method"""
    sw = self.get_parent()
    adj = sw.get_vadjustment()
    adj.set_value(adj.get_upper() - adj.get_page_size())

def load_image(image_widget):
    # Load the bitmap image
    image_path = "images/jack.png"
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)

    # Calculate the scaling factor to fit the image in the canvas
    scale_factor = SCALE

    # Calculate the new width and height of the scaled image
    new_width = int(pixbuf.get_width() * scale_factor)
    new_height = int(pixbuf.get_height() * scale_factor)

    # Scale the pixbuf
    scaled_pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)

    image_widget.clear()
    image_widget.set_from_pixbuf(scaled_pixbuf)

# Callback function to handle radio button press events - we control the turn order and don't want the user to toggle any buttons.
def on_button_press_event(radio_button, event):
    if event.type == Gdk.EventType.BUTTON_PRESS and event.button == Gdk.BUTTON_PRIMARY:
        # Override the toggle behavior programmatically
        radio_button.set_active(radio_button.get_active())
        return True  # Prevent the default toggle behavior

class DragData:
    def __init__(self, widget, x, y):
         self.widget = widget
         self.start_x = x
         self.start_y = y
         self.offset_x = 0
         self.offset_y = 0
         self.investigator_id = None
         self.crossing = None
         self.valid_crossings = []

class WhiteHallGui:
    
    def __init__(self):
        self.jack_token_pos = -1
        self.turn_buttons = []            
    
    def on_motion_notify(self, widget, event, drag_data):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        image_x, image_y = widget.translate_coordinates(self.image_widget, x, y)
        # Handle mouse movement
        if event.window == widget.get_window():
            pass
            #print(f"Mouse moved to ({x}, {y}) which is really ({image_x}, {image_y})")
            if event.state & Gdk.EventMask.BUTTON_PRESS_MASK and None != drag_data.widget :
                drag_data.widget.set_valign(Gtk.Align.START)
                x = int(event.x + drag_data.offset_x)
                y = int(event.y + drag_data.offset_y)
                
                allocation = Gdk.Rectangle()
                allocation.x = x
                allocation.y = y
                allocation.width = drag_data.widget.get_allocation().width
                allocation.height = drag_data.widget.get_allocation().height
                
                # Check if we are over a crossing
                ids = quadtree.intersect((image_x, image_y, image_x, image_y))
                if ids and ("c" in ids[0]) and ids[0] in drag_data.valid_crossings:
                    # TODO:Enforce a 2 crossing movement limit unless game hasn't started or in godmode
                    
                    (id_x, id_y) = positions_dict[ids[0]]
                    #print("Found at location with ID:", ids[0], positions_dict[ids[0]])
                    drag_data.crossing = ids[0]
                    #Snap the image widget to the location so it looks like it is standing on it
                    allocation.x = id_x - 5
                    allocation.y = id_y - INVESTIGATOR_HEIGHT
                    # Save this new crossing as the place of origin for the inspector widget (in case we release it slightly off a crossing later)
                    drag_data.start_x = allocation.x
                    drag_data.start_y = allocation.y
                    
                drag_data.widget.size_allocate(allocation)

    def on_button_press(self, widget, event, drag_data):
        # Handle mouse button press
        x, y = widget.translate_coordinates(self.image_widget, event.x, event.y)
        if event.button == Gdk.BUTTON_PRIMARY:
            #print("Left mouse button pressed at (x={}, y={})".format(x, y))
            for num in range(0,3):
                if is_point_within_widget(self.investigator_imgs[num], x, y):
                    #print("Yo!  You clicked on ", num)
                    drag_data.investigator_id = num
                    drag_data.crossing = wh.jack.ipos[num]  # Save starting crossing in case investigator is released before being on a new crossing
                    drag_data.widget = self.investigator_imgs[num]
                    allocation = self.investigator_imgs[num].get_allocation()
                    drag_data.start_x = allocation.x
                    drag_data.start_y = allocation.y
                    drag_data.offset_x = drag_data.start_x - event.x
                    drag_data.offset_y = drag_data.start_y - event.y
                    # Get a list of all crossings 2 away and save it to the drag_data
                    drag_data.valid_crossings = wh.jack.investigator_crossing_options(num)
                    # Remove crossings that are occupied by other investigators
                    for pos in wh.jack.ipos:
                        if (pos != drag_data.crossing) and (pos in drag_data.valid_crossings):
                            drag_data.valid_crossings.remove(pos)
                    #print(drag_data.valid_crossings)
                    
        elif event.button == Gdk.BUTTON_SECONDARY:
            print("Right mouse button pressed")
    
    def button_release_event(self, widget, event, drag_data):
        if event.button == Gdk.BUTTON_PRIMARY and drag_data.crossing != None:
            # Save the ipos for this widget to the game state
            wh.jack.ipos[drag_data.investigator_id] = drag_data.crossing
            
            self.fixed_frame.remove(self.investigator_imgs[drag_data.investigator_id])
            (x, y) = positions_dict[drag_data.crossing]
            self.fixed_frame.put(self.investigator_imgs[drag_data.investigator_id], x - 5, y - INVESTIGATOR_HEIGHT)
            
            # clear the dragging info - we have released the investigator
            drag_data.offset_x = 0
            drag_data.offset_y = 0
            drag_data.widget = None
            drag_data.investigator_id = None
            drag_data.crossing = None
            
    
    def process_output(self, output_type, *msg):
    
        if (output_type == wh.TEXT_MSG):
            # Get the text buffer from the text view
            buffer = self.text_view.get_buffer()

            # Create a text tag table and add tags for bold and italic formatting
            tag_table = buffer.get_tag_table()
            bold_tag = Gtk.TextTag()
            bold_tag.set_property("weight", Pango.Weight.BOLD)
            tag_table.add(bold_tag)

            italic_tag = Gtk.TextTag()
            italic_tag.set_property("style", Pango.Style.ITALIC)
            tag_table.add(italic_tag)

            m = ' '.join(str(arg) for arg in msg)
            add_text_with_tags(self.text_view, f"{m}\n")
    
        elif (output_type == wh.SPECIAL_TRAVEL_MSG):
            overlay = self.turn_buttons[wh.game_turn()+1]
            travel_type = msg[0]
            image = Gtk.Image.new_from_file(f"images/{travel_images[travel_type]}")
            overlay.add_overlay(image)
            overlay.show_all()
    
            # need a second image to cover the second turn the coach took
            if travel_type == wh.COACH_MOVE:
                overlay = self.turn_buttons[wh.game_turn()+2]
                image = Gtk.Image.new_from_file(f"images/{travel_images[travel_type]}")
                overlay.add_overlay(image)
                overlay.show_all()
        
        elif (output_type == wh.NEW_ROUND_MSG):
            if (self.jack_token_pos != -1):
                # Temporarily remove the jack token so it isn't counted as an extra card overlay that needs to be removed.
                jack_overlay = self.turn_buttons[self.jack_token_pos]
                jack_widget = jack_overlay.get_children()[-1]
                jack_overlay.remove(jack_widget)
    
            # remove all special transportation cards from the turn track
            for overlay in self.turn_buttons:
                children = overlay.get_children()
                # There will only ever be at most one extra overlay per turn space
                if len(children) > 1:
                    overlay.remove(children[-1])
    
            # put the jack token back
            if (self.jack_token_pos != -1):
                jack_overlay.add_overlay(jack_widget)
                jack_overlay.show_all()
        else:
            self.refresh_board()
    
    def process_command_helper(self, command):    
        # Get the text buffer from the text view
        buffer = self.text_view.get_buffer()

        # Create a text tag table and add tags for bold and italic formatting
        tag_table = buffer.get_tag_table()
        bold_tag = Gtk.TextTag()
        bold_tag.set_property("weight", Pango.Weight.BOLD)
        tag_table.add(bold_tag)

        italic_tag = Gtk.TextTag()
        italic_tag.set_property("style", Pango.Style.ITALIC)
        tag_table.add(italic_tag)

        # Append the command to the text view with bold formatting
        buffer.insert_with_tags_by_name(buffer.get_end_iter(), f"> {command}\n", "bold")
    
        # Perform actions based on the command
        wh.process_input(command)
        self.entry.set_text("")
        self.entry.set_editable(True)
        return False
    
    def process_command(self, widget):
        command = widget.get_text()

        # Clear the entry widget
        widget.set_text("Jack is thinking...")
        widget.set_position(-1)
        widget.set_editable(False)
        GLib.idle_add(self.process_command_helper, command)
        #GLib.timeout_add(1, process_command_helper, command)

    def refresh_board(self):
        curr_turn = wh.game_turn()
        load_image(self.image_widget)
        self.image_widget.queue_draw()
        self.turn_buttons[curr_turn].get_child().set_active(True)

        # Move the jack token to the current turn space
        curr_overlay = self.turn_buttons[curr_turn]        
        if (self.jack_token_pos == -1):
            image = Gtk.Image.new_from_file("images/jack-corner.png")
            curr_overlay.add_overlay(image)
        elif (self.jack_token_pos != curr_turn):
            prev_overlay = self.turn_buttons[self.jack_token_pos]
            jack_widget = prev_overlay.get_children()[-1]
            prev_overlay.remove(jack_widget)
            curr_overlay.add_overlay(jack_widget)

        curr_overlay.show_all()
        self.jack_token_pos = curr_turn

        # Put the investigator playing pieces on the board
        fixed_children = self.fixed_frame.get_children()
        for num in range (0,3):
            if self.investigator_imgs[num] in fixed_children:
                self.fixed_frame.remove(self.investigator_imgs[num]) 
        for num in range (0,3):
            ipos = wh.jack.ipos[num]
            x, y = positions_dict[ipos]
            self.fixed_frame.put(self.investigator_imgs[num], x - 5, y - INVESTIGATOR_HEIGHT)


    
    def setup(self):
        create_positions_dictionary()
        
        # Create the main window
        self.window = Gtk.Window()
        self.window.set_title("Whitehall Mystery Jack Automaton")
        self.window.fullscreen()   # TODO: make this is a starting argument?
        # window.maximize() - This doesn't appear to work.
        self.window.connect("destroy", Gtk.main_quit)

        # Create a grid to contain the subwindows
        grid = Gtk.Grid()
        self.window.add(grid)

        # Create a frame to contain the text widget
        frame = Gtk.Frame()
        #frame.set_hexpand(True)
        frame.set_vexpand(True)
    
        # Set padding around the frame
        frame.set_margin_top(5)
        frame.set_margin_bottom(5)
        frame.set_margin_start(5)
        frame.set_margin_end(5)
    
        GRID_HEIGHT = 3
        grid.attach(frame, 0, 0, 1, 1)

        # Create a text view for displaying input and output history
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_cursor_visible(False)
    
        self.text_view.connect("size-allocate", _autoscroll)
    
        # Create a scrolled window to contain the text view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.text_view)

        # Disable frame propagation for the scrolled window
        scrolled_window.set_shadow_type(Gtk.ShadowType.NONE)
        frame.add(scrolled_window)

        # Create a text buffer for the text view
        text_buffer = self.text_view.get_buffer()

        # Create tags with bold and italic styles
        bold_tag = text_buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        italic_tag = text_buffer.create_tag("italic", style=Pango.Style.ITALIC)
        
        # Create an entry widget to receive user input
        self.entry = Gtk.Entry()

        # Create a box to hold the entry and button
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.pack_start(self.entry, True, True, 0)
        box.set_size_request(-1, 35)
    
        # Add the box and other widgets to the grid
        grid.attach(box, 0, 2, 1, 1)

        self.image_widget = Gtk.Image()
        self.fixed_frame = Gtk.Fixed()
        self.fixed_frame.add(self.image_widget)

        # Create a scrolled window to contain the image widget
        image_scrolled_window = Gtk.ScrolledWindow()
        image_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        image_scrolled_window.add(self.fixed_frame)

        # Load the initial game board map view
        load_image(self.image_widget)
    
        # TODO: this is just a test
        drag_data1 = DragData(None, 0, 0)
        image_scrolled_window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        image_scrolled_window.connect("motion-notify-event", self.on_motion_notify, drag_data1)
        image_scrolled_window.connect("button-press-event", self.on_button_press, drag_data1)
        image_scrolled_window.connect("button-release-event", self.button_release_event, drag_data1)
        
        frame2 = Gtk.Frame()
        frame2.set_hexpand(True)
        frame2.set_vexpand(True)
        frame2.add(image_scrolled_window)

        # Add the scrolled window to the grid
        grid.attach(frame2, 1, 0, 2, GRID_HEIGHT)
    
        # Create panel for the turn track - as radio buttons
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        panel.set_size_request(-1, 70)
    
        # Create and add buttons
        for i in range(16):
            # Create an overlay for each button so we can display a special travel image when needed
            overlay = Gtk.Overlay()
            panel.pack_start(overlay, True, True, 0)
        
            if (i == 0):
                button = Gtk.RadioButton.new_with_label_from_widget(None, f"{i}")
                button.set_active(True)
            else:
                button = Gtk.RadioButton.new_with_label_from_widget(self.turn_buttons[0].get_child(), f"{i}")
                button.set_active(False)

            # Set the alignment of the radio button
            button.set_halign(Gtk.Align.CENTER)
            button.set_valign(Gtk.Align.CENTER)

            overlay.add(button)
            button.connect("button-press-event", on_button_press_event)
            self.turn_buttons.append(overlay)
        
        grid.attach(panel, 0, GRID_HEIGHT, 3, 2)

        # Pressing enter in the entry widget triggers the process_command() function
        self.entry.connect("activate", self.process_command)

        self.investigator_imgs = []
        for num in range (0,3):
            i_img = Gtk.Image.new_from_file(f"images/{investigators[num]}")
            self.investigator_imgs.append(i_img)
            i_img.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
            i_img.connect("motion-notify-event", self.on_motion_notify)
            i_img.connect("button-press-event", self.on_button_press)
            
        # Pass a function and some necessary UI elements to the game engine so it can post things to the GUI with the proper context
        wh.register_gui_self_test(self.self_test)
        wh.register_output_reporter(self.process_output)    
        wh.welcome()
        self.refresh_board()
    
        # Connect the resize_image function to the "realize" signal of the window
        #window.connect("realize", resize_image)

        # Show all the widgets and start the GTK+ main loop
        self.window.show_all()
        Gtk.main()

    def self_test(self):
        print("GUI self tests completed.")
        
gui = WhiteHallGui()
gui.setup()

