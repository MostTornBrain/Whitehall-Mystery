'''
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
'''
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, Pango, Gdk, GLib
import whitehall as wh
import re
import random

travel_images = ["nothing", "boat-100-white.png", "alley-100.png", "coach-100.png"]
        
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
    image_path = "jack.png"
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)

    # Calculate the scaling factor to fit the image in the canvas
    scale_factor = 0.8

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

class WhiteHallGui:
    
    def __init__(self):
        self.jack_token_pos = -1
        self.turn_buttons = []            
    
    def on_motion_notify(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        image_x, image_y = widget.translate_coordinates(self.image_widget, x, y)
        # Handle mouse movement
        print(f"Mouse moved to ({x}, {y}) which is really ({image_x}), {image_y}")

    def on_button_press(self, widget, event):
        # Handle mouse button press
        if event.button == Gdk.BUTTON_PRIMARY:
            print("Left mouse button pressed")
        elif event.button == Gdk.BUTTON_SECONDARY:
            print("Right mouse button pressed")
            
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
            image = Gtk.Image.new_from_file(travel_images[travel_type])
            overlay.add_overlay(image)
            overlay.show_all()
    
            # need a second image to cover the second turn the coach took
            if travel_type == wh.COACH_MOVE:
                overlay = self.turn_buttons[wh.game_turn()+2]
                image = Gtk.Image.new_from_file(travel_images[travel_type])
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
            self.refresh_turn_track()
    
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

    def refresh_turn_track(self):
        curr_turn = wh.game_turn()
        load_image(self.image_widget)
        self.image_widget.queue_draw()
        self.turn_buttons[curr_turn].get_child().set_active(True)

        # Move the jack token to the current turn space
        curr_overlay = self.turn_buttons[curr_turn]        
        if (self.jack_token_pos == -1):
            image = Gtk.Image.new_from_file("jack-corner.png")
            curr_overlay.add_overlay(image)
        elif (self.jack_token_pos != curr_turn):
            prev_overlay = self.turn_buttons[self.jack_token_pos]
            jack_widget = prev_overlay.get_children()[-1]
            prev_overlay.remove(jack_widget)
            curr_overlay.add_overlay(jack_widget)

        curr_overlay.show_all()
        self.jack_token_pos = curr_turn
    
    def setup(self):
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
    
        # Create a scrolled window to contain the image widget
        image_scrolled_window = Gtk.ScrolledWindow()
        image_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        image_scrolled_window.add(self.image_widget)

        # Load the initial game board map view
        load_image(self.image_widget)
    
        # TODO: this is just a test
        image_scrolled_window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        image_scrolled_window.connect("motion-notify-event", self.on_motion_notify)
        image_scrolled_window.connect("button-press-event", self.on_button_press)
        
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

        # Pass a function and some necessary UI elements to the game engine so it can post things to the GUI with the proper context
        wh.register_gui_self_test(self.self_test)
        wh.register_output_reporter(self.process_output)    
        wh.welcome()
        self.refresh_turn_track()
    
        # Connect the resize_image function to the "realize" signal of the window
        #window.connect("realize", resize_image)

        # Show all the widgets and start the GTK+ main loop
        self.window.show_all()
        Gtk.main()

    def self_test(self):
        print("GUI self tests completed.")
        
gui = WhiteHallGui()
gui.setup()

