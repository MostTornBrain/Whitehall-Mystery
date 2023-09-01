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


def process_command_helper(args):
    command = args[0]
    entry = args[1]
    text_view = args[2]
    
    # Get the text buffer from the text view
    buffer = text_view.get_buffer()

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
    entry.set_text("")
    entry.set_editable(True)
    return False
    
def process_command(entry, text_view):
    command = entry.get_text()

    # Clear the entry widget
    entry.set_text("Jack is thinking...")
    entry.set_position(-1)
    entry.set_editable(False)
    GLib.idle_add(process_command_helper, [command, entry, text_view])
    #GLib.timeout_add(1, process_command_helper, [command, entry, text_view])
    
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


def refresh_turn_track(turn_buttons, image_widget):
    curr_turn = wh.game_turn()
    load_image(image_widget)
    image_widget.queue_draw()
    turn_buttons[curr_turn].get_child().set_active(True)

    # Move the jack token to the current turn space
    curr_overlay = turn_buttons[curr_turn]        
    if (process_output.jack_token_pos == -1):
        image = Gtk.Image.new_from_file("jack-corner.png")
        curr_overlay.add_overlay(image)
    elif (process_output.jack_token_pos != curr_turn):
        prev_overlay = turn_buttons[process_output.jack_token_pos]
        jack_widget = prev_overlay.get_children()[-1]
        prev_overlay.remove(jack_widget)
        curr_overlay.add_overlay(jack_widget)

    curr_overlay.show_all()
    process_output.jack_token_pos = curr_turn
    

def process_output(handle, output_type, *msg):
    # handle = [text_view, image_widget]
    text_view = handle[0]
    image_widget = handle[1]
    turn_buttons = handle[2]
    if not hasattr(process_output, "jack_token_pos"):
        process_output.jack_token_pos = -1
        
    if (output_type == wh.TEXT_MSG):
        # Get the text buffer from the text view
        buffer = text_view.get_buffer()

        # Create a text tag table and add tags for bold and italic formatting
        tag_table = buffer.get_tag_table()
        bold_tag = Gtk.TextTag()
        bold_tag.set_property("weight", Pango.Weight.BOLD)
        tag_table.add(bold_tag)

        italic_tag = Gtk.TextTag()
        italic_tag.set_property("style", Pango.Style.ITALIC)
        tag_table.add(italic_tag)

        '''
            # Append the output to the text view with italic formatting
            for m in msg:
                #buffer.insert_with_tags_by_name(buffer.get_end_iter(), f"{msg}\n", "italic")
                #buffer.insert(buffer.get_end_iter(), f"{m}\n")
                add_text_with_tags(text_view, m)
        '''
        m = ' '.join(str(arg) for arg in msg)
        add_text_with_tags(text_view, f"{m}\n")
        
    elif (output_type == wh.SPECIAL_TRAVEL_MSG):
        overlay = turn_buttons[wh.game_turn()+1]
        travel_type = msg[0]
        image = Gtk.Image.new_from_file(travel_images[travel_type])
        overlay.add_overlay(image)
        overlay.show_all()
        
        # need a second image to cover the second turn the coach took
        if travel_type == wh.COACH_MOVE:
            overlay = turn_buttons[wh.game_turn()+2]
            image = Gtk.Image.new_from_file(travel_images[travel_type])
            overlay.add_overlay(image)
            overlay.show_all()
            
    elif (output_type == wh.NEW_ROUND_MSG):
        if (process_output.jack_token_pos != -1):
            # Temporarily remove the jack token so it isn't counted as an extra card overlay that needs to be removed.
            jack_overlay = turn_buttons[process_output.jack_token_pos]
            jack_widget = jack_overlay.get_children()[-1]
            jack_overlay.remove(jack_widget)
        
        # remove all special transportation cards from the turn track
        for overlay in turn_buttons:
            children = overlay.get_children()
            # There will only ever be at most one extra overlay per turn space
            if len(children) > 1:
                overlay.remove(children[-1])
        
        # put the jack token back
        if (process_output.jack_token_pos != -1):
            jack_overlay.add_overlay(jack_widget)
            jack_overlay.show_all()
            

    else:
        refresh_turn_track(turn_buttons, image_widget)
        
# Callback function to handle radio button press events - we control the turn order
def on_button_press_event(radio_button, event):
    if event.type == Gdk.EventType.BUTTON_PRESS and event.button == Gdk.BUTTON_PRIMARY:
        # Override the toggle behavior programmatically
        radio_button.set_active(radio_button.get_active())
        return True  # Prevent the default toggle behavior

# TODO: this isn't currently used
def resize_image(widget):
    print(turn_buttons)
    # Calculate the scaled height based on the width and aspect ratio
    original_width = image.get_pixbuf().get_width()
    original_height = image.get_pixbuf().get_height()
    scaled_width = radio_button.get_allocated_width()
    scaled_height = int(original_height * (scaled_width / original_width))

    # Scale the image to match the width and proportional height
    scaled_pixbuf = image.get_pixbuf().scale_simple(
        scaled_width,
        scaled_height,
        GdkPixbuf.InterpType.BILINEAR
    )
    scaled_image = Gtk.Image.new_from_pixbuf(scaled_pixbuf)
    overlay.add_overlay(scaled_image)

# Create an array to hold the buttons
turn_buttons = []

def _autoscroll(self, *args):
    """The actual scrolling method"""
    sw = self.get_parent()
    adj = sw.get_vadjustment()
    adj.set_value(adj.get_upper() - adj.get_page_size())

def setup_gui():
    # Create the main window
    window = Gtk.Window()
    window.set_title("Whitehall Mystery Jack Automaton")
    window.fullscreen()   # TODO: make this is a starting argument?
    # window.maximize() - This doesn't appear to work.
    window.connect("destroy", Gtk.main_quit)

    # Create a grid to contain the subwindows
    grid = Gtk.Grid()
    window.add(grid)

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
    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    text_view.set_cursor_visible(False)
    
    text_view.connect("size-allocate", _autoscroll)
    
    # Create a scrolled window to contain the text view
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.add(text_view)

    # Disable frame propagation for the scrolled window
    scrolled_window.set_shadow_type(Gtk.ShadowType.NONE)
    frame.add(scrolled_window)

    # Create a text buffer for the text view
    text_buffer = text_view.get_buffer()

    # Insert text with bold and italic styles
    bold_tag = text_buffer.create_tag("bold", weight=Pango.Weight.BOLD)
    italic_tag = text_buffer.create_tag("italic", style=Pango.Style.ITALIC)
    
    # Create an entry widget to receive user input
    entry = Gtk.Entry()

    # Create a box to hold the entry and button
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    box.pack_start(entry, True, True, 0)
    box.set_size_request(-1, 35)
    
    # Add the box and other widgets to the grid
    grid.attach(box, 0, 2, 1, 1)

    image_widget = Gtk.Image()
    
    # Create a scrolled window to contain the image widget
    image_scrolled_window = Gtk.ScrolledWindow()
    image_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    image_scrolled_window.add(image_widget)

    # Load the initial game board map view
    load_image(image_widget)
    
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
            button = Gtk.RadioButton.new_with_label_from_widget(turn_buttons[0].get_child(), f"{i}")
            button.set_active(False)

        # Set the alignment of the radio button
        button.set_halign(Gtk.Align.CENTER)
        button.set_valign(Gtk.Align.CENTER)

        overlay.add(button)
        button.connect("button-press-event", on_button_press_event)
        turn_buttons.append(overlay)
        
    grid.attach(panel, 0, GRID_HEIGHT, 3, 2)

    # Pressing enter in the entry widget triggers the process_command() function
    entry.connect("activate", lambda widget: process_command(entry, text_view))

    # Pass a function and some necessary UI elements to the game engine so it can post things to the GUI with the proper context
    wh.register_output_reporter(process_output, [text_view, image_widget, turn_buttons])    
    wh.welcome()
    refresh_turn_track(turn_buttons, image_widget)
    
    # Connect the resize_image function to the "realize" signal of the window
    #window.connect("realize", resize_image)

    # Show all the widgets and start the GTK+ main loop
    window.show_all()
    Gtk.main()

setup_gui()