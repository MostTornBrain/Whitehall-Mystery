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
from gi.repository import Gtk, GdkPixbuf, Pango
import whitehall as wh
import re

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


def process_command(entry, text_view):
    command = entry.get_text()

    # Clear the entry widget
    entry.set_text("")

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

    # Scroll to the end of the text view
    text_view.scroll_to_iter(buffer.get_end_iter(), 0.0, True, 0.0, 0.0)

    # Perform actions based on the command
    wh.process_input(command)

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
    
def process_output(handle, output_type, *msg):
    # handle = [text_view, image_widget]
    text_view = handle[0]
    image_widget = handle[1]
    
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
        
        # Scroll to the end of the text view
        text_view.scroll_to_iter(buffer.get_end_iter(), 0.0, True, 0.0, 0.0)
        
    else:
        load_image(image_widget)
        image_widget.queue_draw()


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
    frame.set_hexpand(True)
    frame.set_vexpand(True)
    
    # Set padding around the frame
    frame.set_margin_top(5)
    frame.set_margin_bottom(5)
    frame.set_margin_start(5)
    frame.set_margin_end(5)
    
    grid.attach(frame, 0, 0, 1, 1)

    # Create a text view for displaying input and output history
    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    text_view.set_cursor_visible(False)
    
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

    # Add the box and other widgets to the grid
    grid.attach(box, 0, 1, 1, 1)

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
    grid.attach(frame2, 1, 0, 7, 2)

    # Pressing enter in the entry widget triggers the process_command() function
    entry.connect("activate", lambda widget: process_command(entry, text_view))

    wh.register_output_reporter(process_output, [text_view, image_widget])    
    wh.welcome()

    # Show all the widgets and start the GTK+ main loop
    window.show_all()
    Gtk.main()

setup_gui()