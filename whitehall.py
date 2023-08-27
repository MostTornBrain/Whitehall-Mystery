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
import graph_tool.all as gt
from jack import *
import re

LAND = 0
WATER = 1
ALLEY = 2

ug = gt.Graph(edge_list, hashed=True, eprops=[("weight", "float"), ("transport", "int")])

vcolor = ug.new_vp("string")
vshape = ug.new_vp("string")
vsize = ug.new_vp("int")
vfsize = ug.new_vp("int")
ecolor = ug.new_edge_property("string")

# Assign the x-y coordinates of everything
vpos = ug.new_vp("vector<double>")
for pair in positions:
    #jack.print(pair)
    v=gt.find_vertex(ug, ug.vp.ids, pair[0])[0]
    vpos[v] = pair[1]

# Print out nodes with missing positions for help when editing by hand
for node in ug.vertices():
    if not (vpos[node]):
        jack.print("        [\"%s\", [,-]]," % ug.vp.ids[node])

# We don't want the water or alley paths (edges) to be visible
for edge in ug.edges():
    if (ug.ep.transport[edge] == WATER) or (ug.ep.transport[edge] == ALLEY):
        ecolor[edge] = "#ffffff"
    else:
        ecolor[edge] = "#000000"

# Make these properties part internal to the graph so they get saved if we save the graph to a file
ug.vp.pos = vpos
ug.vp.vcolor = vcolor
ug.vp.vshape = vshape
ug.vp.vsize = vsize
ug.vp.vfsize = vfsize
ug.ep.ecolor = ecolor

reset_graph_color_and_shape(ug)

# Save it so I can debug the contents to make sure I'm building it correctly
ug.save("my_graph.graphml")

# ug.list_properties()

##########################################

ipos = ["87c1", "77c1", "86c1"]
jack = Jack(ug, ipos);

jack.make_image()

##########################################

def parse_ipos(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'ipos\s(.+)', user_input)
    values = []
    # Extract the alphanumeric values
    if match:
        values = match.group(1).split(',')
        values = [value.strip() for value in values]
        for value in values:
            if 'c' not in value or len(gt.find_vertex(ug, ug.vp.ids, value)) == 0:
                values = []
                jack.print(value, " is not a valid inspector location.")
                break;
    return values;

def parse_clues(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'clues\s(.+)', user_input)
    values = []
    # Extract the alphanumeric values
    if match:
        values = match.group(1).split(',')
        values = [value.strip() for value in values]
        for value in values:
            if 'c' in value or len(gt.find_vertex(ug, ug.vp.ids, value)) == 0:
                values = []
                jack.print(value, " is not a valid location.")
                break;
    return values;

def parse_arrest(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'arrest\s(.+)', user_input)
    # Extract the alphanumeric values
    if match:
        value = match.group(1)
        value.strip()
        if 'c' in value or len(gt.find_vertex(ug, ug.vp.ids, value)) == 0:
            jack.print(value, " is not a valid location.")
            value = "BAD"
    return value

def parse_jackpos(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'jackpos\s(.+)', user_input)
    # Extract the alphanumeric values
    if match:
        value = match.group(1)
        value.strip()
        if 'c' in value or len(gt.find_vertex(ug, ug.vp.ids, value)) == 0:
            jack.print(value, " is not a valid location.")
            value = "BAD"
    return value

def parse_cost(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'cost\s(.+)', user_input)
    values = []
    # Extract the alphanumeric values
    if match:
        values = match.group(1).split(',')
        values = [value.strip() for value in values]
        if (len(values) != 2):
            jack.print("Must enter two locations")
            return
        for value in values:
            if len(gt.find_vertex(ug, ug.vp.ids, value)) == 0:
                values = []
                jack.print(value, " is not a valid location.")
                return
        print (jack.hop_count(values[0], values[1]))
                
                
                
def process_input(user_input):
    # NOTE: This does only very rudimentary syntax checking. It is NOT a feature-rich UI
    #       For example, it does simple substring matching for some commands.
    if user_input == "jack":
        jack.move()
        
    elif user_input == "start":
        jack.reset()
        
    elif user_input == "godmode on":
        jack.godmode = True
        
    elif user_input == "godmode off":
        jack.godmode = False
        
    elif "ipos" in user_input:
        values = parse_ipos(user_input)
        if (len(values) == 3):
            jack.set_ipos(values)
        else:
            jack.print("Invalid input")
            
    elif user_input == "status":
        jack.status()

    elif user_input == "img":
        jack.make_image()
        
    elif "arrest" in user_input:
        pos = parse_arrest(user_input)
        if (pos != "BAD"):
            jack.arrest(pos)
        
    elif "clues" in user_input:
        pos_list = parse_clues(user_input)
        if (len(pos_list) != 0):
            jack.clue_search(pos_list)
        
    elif jack.godmode and "jackpos" in user_input:
        pos = parse_jackpos(user_input)
        if (pos != "BAD"):
            jack.pos = pos

    elif jack.godmode and "cost" in user_input:
        parse_cost(user_input)
        
    elif "exit" in user_input:
        exit()
            
    elif "help" in user_input:
        jack.print("Commands are:")
        jack.print(" \033[1mjack\033[0m:    Jack takes his turn")
        jack.print(" \033[1mstart\033[0m:   Start a new game (CAUTION: typing this mid-game will RESTART the game)")
        jack.print(" \033[1mipos <pos1>, <pos2>, <pos3>\033[0m:  Enter the inspector locations")
        jack.print(" \033[1mstatus\033[0m:    View the current game status")
        jack.print(" \033[1marrest <pos>\033[0m:    Attempt arrest at the specified position")
        jack.print(" \033[1mclues <pos1>,..,<posX>\033[0m:    Search for clues at the supplied locations in the specified order")
        jack.print(" \033[1mimg\033[0m:    Force the img file to be updated immediately with the current game state")
        jack.print(" \033[1mexit\033[0m:    Completely exit the program.")
        jack.print(" \033[1mgodmode <on,off>\033[0m:    Toggle godmode")
        jack.godmode_print("  \033[1mjackpos <pos>\033[0m:    Move Jack to the specified location for debugging")
        jack.godmode_print("  \033[1mcost <pos1>, <pos2>\033[0m:    Show the distance between two vertices (for weight debugging)")
    else:
        jack.print("Unknown command.")

def command_line_ui():
    # Input loop
    while True:
        if (jack.godmode):
            user_input = input("\033[1mgodmode > \033[0m")
        else:
            user_input = input("\033[1m> \033[0m")
    
        if user_input == "exit":
            jack.print("Goodbye!")
            break

        process_input(user_input)

def welcome():
    jack.print("   Welcome!")
    jack.print("   Type \033[1mhelp\033[0m at any time for a full list of commands.")
    jack.print("   Use the \033[1mipos\033[0m command to specify the investigator starting locations.")
    jack.print("   Then type \033[1mstart\033[0m to begin the game.")

def register_output_reporter(func, handle):
    jack.register_output_reporter(func, handle)
    
#command_line_ui()

# Save the graph so I can debug the contents to make sure I'm 
# building it correctly and restoring weights correctly
ug.save("my_graph_after.graphml")
