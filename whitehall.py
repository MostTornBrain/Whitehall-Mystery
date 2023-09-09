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
import networkx as nx
from jack import *
from graph_data import *
import re

SCALE=2 # How much to scale all the x, y coordinates

ug = nx.DiGraph()
for edge in edge_list:
    ug.add_edge(edge[0], edge[1], weight=edge[2], transport=edge[3])

investigators = ["y", "b", "r"]

# Assign the x-y coordinates of everything
for pair in positions:
    #jack.print(pair)
    pair[1][1] += 871
    pair[1][0] *= SCALE
    pair[1][1] *= SCALE 
    ug.nodes[pair[0]]['pos'] = pair[1]

# Print out nodes with missing positions for help when editing by hand
for node in ug.nodes():
    if 'pos' not in (ug.nodes[node]):
        jack.print("        [\"%s\", [,-]]," % node)

# We don't want the water or alley paths (edges) to be visible
for u, v in ug.edges():
    if (ug.edges[u, v]['transport'] == BOAT_MOVE) or (ug.edges[u, v]['transport'] == ALLEY_MOVE):
        ug.edges[u, v]['color'] = "#ffffff"
    else:
        ug.edges[u, v]['color'] = "#000000"

reset_graph_color_and_shape(ug)

##########################################

ipos = ["87c1", "77c1", "86c1"]
jack = Jack(ug, ipos);

jack.make_image()

##########################################

def parse_ipos(user_input):
    match = user_input
    values = []
    # Extract the alphanumeric values
    if match:
        values = match.split(',')
        values = [value.strip() for value in values]
        for value in values:
            if 'c' not in value or not ug.has_node(value):
                values = []
                jack.print(value, " is not a valid investigator location.")
                break;
    return values;

def parse_clues(user_input):
    match = user_input
    values = []
    # Extract the alphanumeric values
    if match:
        values = match.split(',')
        values = [value.strip() for value in values]
        for value in values:
            if 'c' in value or not ug.has_node(value):
                values = []
                jack.print(value, " is not a valid location.")
                break;
    return values;

def parse_single_location(user_input):
    if user_input:
        value = user_input
        value.strip()
        if 'c' in value or not ug.has_node(value):
            jack.print(value, " is not a valid location.")
            value = "BAD"
    return value

def parse_single_crossing(user_input):
    if user_input:
        value = user_input
        value.strip()
        if 'c' not in value or not ug.has_node(value):
            jack.print(value, " is not a valid crossing.")
            value = "BAD"
    return value

def parse_cost(user_input):
    # Use regular expression to match the alphanumeric values
    match = user_input
    values = []
    # Extract the alphanumeric values
    if match:
        values = match.split(',')
        values = [value.strip() for value in values]
        if (len(values) != 2):
            jack.print("Must enter two (and only two) locations")
            return
        for value in values:
            if not ug.has_node(value):
                values = []
                jack.print(value, " is not a valid location.")
                return
        jack.print(jack.hop_count(values[0], values[1]))
                
                
                
def process_input(user_input):
    # NOTE: This does only very rudimentary syntax checking. It is NOT a feature-rich UI
    #       For example, it does simple substring matching for some commands.
    jack.log_to_file("\033[1m>", user_input, "\033[0m")
    
    split_input = user_input.split(" ", 1)
    command = split_input[0]
    parms = split_input[-1]   # Note: this can end up being the same as command if no arguments were supplied
    
    if "jack" == command:
        jack.move()
        process_input.player_move_allowed = True
        
    elif "start" == command:
        jack.reset()
        process_input.player_move_allowed = True
        
    elif "godmode" == command:
        if parms == "on":
            jack.godmode = True
            jack.print("Godmode is now on.")
        elif parms == "off":
            jack.godmode = False
            jack.print("Godmode is now off.")
        else:
            jack.print("Usage: godmode <on,off>")
        
    elif "ipos" == command:
        if (jack.godmode) or process_input.player_move_allowed:
            values = parse_ipos(parms)
            if (len(values) == 3):
                jack.set_ipos(values)
            else:
                jack.print("Usage: ipos <pos1>, <pos2>, <pos3>")
        else:
            jack.print("It's Jack's turn to move now, not yours.")
            
    elif "status" == command:
        jack.status()

    elif "map" == command:
        jack.make_image()
        
    elif "arrest" == command:
        pos = parse_single_location(parms)
        if (pos != "BAD"):
            jack.arrest(pos)
            process_input.player_move_allowed = False
        
    elif "clues" == command:
        pos_list = parse_clues(parms)
        if (len(pos_list) != 0):
            jack.clue_search(pos_list)
            process_input.player_move_allowed = False

    elif command in investigators:
        if (jack.godmode) or process_input.player_move_allowed:
            pos = parse_single_crossing(parms)
            if (pos != "BAD"):
                i = investigators.index(command)
                # I could just modify jack.ipos directly, but we use the API to ensure the map gets redrawn
                ipos = jack.ipos
                if pos in ipos and ipos.index(pos) != i:
                    jack.print("Cannot move investigator to an already occupied space.")
                else:
                    ipos[i] = pos
                    jack.set_ipos(ipos)
        else:
            jack.print("It's Jack's turn to move now, not yours.")
    
    elif jack.godmode and "jackpos" == command:
        pos = parse_single_location(parms)
        if (pos != "BAD"):
            jack.pos = pos
            jack.make_image()
            
    elif jack.godmode and "cost" == command:
        parse_cost(parms)
    
    elif jack.godmode and "self_test" == command:
        self_tests()
        
    elif "exit" == command:
        exit()
            
    elif "help" == command:
        jack.print("Commands are:")
        jack.print(" \033[1mjack\033[0m:    Jack takes his turn")
        jack.print(" \033[1mstart\033[0m:   Start a new game (CAUTION: typing this mid-game will RESTART the game)")
        
        jack.print(" \033[1mipos <pos1>, <pos2>, <pos3>\033[0m:  Enter the investigator locations")
        jack.print(" \033[1my <pos1>\033[0m:  Move the yellow investigator")
        jack.print(" \033[1mb <pos1>\033[0m:  Move the blue investigator")
        jack.print(" \033[1mr <pos1>\033[0m:  Move the red investigator")
        
        jack.print(" \033[1mstatus\033[0m:    View the current game status")
        jack.print(" \033[1marrest <pos>\033[0m:    Attempt arrest at the specified position")
        jack.print(" \033[1mclues <pos1>,..,<posX>\033[0m:    Search for clues at the supplied locations in the specified order")
        jack.print(" \033[1mmap\033[0m:    Force the map file to be updated immediately with the current game state")
        jack.print(" \033[1mexit\033[0m:    Completely exit the program.")
        jack.print(" \033[1mgodmode <on,off>\033[0m:    Toggle godmode")
        jack.godmode_print("  \033[1mjackpos <pos>\033[0m:    Move Jack to the specified location for debugging")
        jack.godmode_print("  \033[1mcost <pos1>, <pos2>\033[0m:    Show the distance between two vertices (for weight debugging)")
        jack.godmode_print("  \033[1mself_test\033[0m:    Run some self-tests")
    else:
        jack.print("Unknown command.")

process_input.player_move_allowed = True

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
    jack.print("   Use your mouse to drag the investigators to starting locations.")
    jack.print("   Then type \033[1mstart\033[0m to begin the game.")

def register_output_reporter(func):
    jack.register_output_reporter(func)

def register_gui_self_test(func):
    register_gui_self_test.gui_self_test_func = func
register_gui_self_test.gui_self_test_func = None
    
def game_turn():
    turn = jack.turn_count()-1
    if turn < 0:
        turn = 0
    return turn

#command_line_ui()

def check_edges():
    # Sanity check the map.  Make sure every edge is bi-directional.
    for edge in ug.edges():
        source = edge.source()
        target = edge.target()
        edge_back = ug.edge(target, source)
        if edge_back is None:
            print("No edge back for ", ug.vp.ids[source], ug.vp.ids[target])

def self_tests():
    check_edges()
    if register_gui_self_test.gui_self_test_func is not None:
        register_gui_self_test.gui_self_test_func()
    jack.print("Self test complete.")
    jack.print("Check shell console for any logged messages.")