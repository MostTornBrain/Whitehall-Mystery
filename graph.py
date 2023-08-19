from graph_tool.all import *
from jack import *
import re

LAND = 0
WATER = 1
ALLEY = 2

ug = Graph(edge_list, hashed=True, eprops=[("weight", "int"), ("transport", "int")])

vcolor = ug.new_vp("string")
vshape = ug.new_vp("string")
vsize = ug.new_vp("int")
vfsize = ug.new_vp("int")
ecolor = ug.new_edge_property("string")

# iterate over all the nodes
for node in ug.vertices():
    vcolor[node] = "#000000"
    
    if 'c' in ug.vp.ids[node]:
        vshape[node] = "square"
        vsize[node] = 8
        vfsize[node] = 8
    else:
        vshape[node] = "circle"
        vsize[node] = 18
        vfsize[node] = 10

# Color ispector starting positions yellow
for node in starting_ipos:
    # TODO: maybe insert another unconnected node here and make it slightly bigger to get the yellow frame?
    v = find_vertex(ug, ug.vp.ids, node)[0]
    vcolor[v] = "#FFD700"

# Color all the destinations in the four quadrants white
for q in quads:
    for num in q:
        v = find_vertex(ug, ug.vp.ids, num)[0]    
        vcolor[v] = "#ffffff"

# Make water destinations blue
for num in water:
    v=find_vertex(ug, ug.vp.ids, num)[0]    
    vcolor[v] = "#0000FF"

# Assign the x-y coordinates of everything
vpos = ug.new_vp("vector<double>")
for pair in positions:
    #print(pair)
    v=find_vertex(ug, ug.vp.ids, pair[0])[0]
    vpos[v] = pair[1]

# Print out nodes with missing positions for help when editing by hand
for node in ug.vertices():
    if not (vpos[node]):
        print("        [\"%s\", [,-]]," % ug.vp.ids[node])

# We don't want the water or alley paths (edges) to be visible
for edge in ug.edges():
    if ug.ep.transport[edge] == WATER:
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

# Save it so I can debug the contents to make sure I'm building it correctly
ug.save("my_graph.graphml")

# ug.list_properties()

# We don't want curved edges - define a common Bezier control so the lines are straight.
# This will make the two edges overlap and look like a single edge with an arrow on each end.
control = [0.3, 0, 0.7, 0]
    
graph_draw(ug,  vertex_text=ug.vp.ids, vertex_fill_color=vcolor, vertex_shape=vshape, vertex_size=vsize,
              vertex_font_size=vfsize,
              pos=vpos, output_size=(873,873), edge_pen_width=1, edge_color=ecolor,
              edge_marker_size=4,
              edge_control_points=control,
              output="graph-draw.pdf")

##########################################

ipos = ["87c1", "77c1", "86c1"]
jack = Jack(ug, ipos, godmode=False);

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
            if 'c' not in value or len(find_vertex(ug, ug.vp.ids, value)) == 0:
                values = []
                print(value, " is not a valid inspector location.")
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
            if 'c' in value or len(find_vertex(ug, ug.vp.ids, value)) == 0:
                values = []
                print(value, " is not a valid location.")
                break;
    return values;

def parse_arrest(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'arrest\s(.+)', user_input)
    # Extract the alphanumeric values
    if match:
        value = match.group(1)
        value.strip()
        if 'c' in value or len(find_vertex(ug, ug.vp.ids, value)) == 0:
            print(value, " is not a valid location.")
            value = "BAD"
    return value

def parse_jackpos(user_input):
    # Use regular expression to match the alphanumeric values
    match = re.search(r'jackpos\s(.+)', user_input)
    # Extract the alphanumeric values
    if match:
        value = match.group(1)
        value.strip()
        if 'c' in value or len(find_vertex(ug, ug.vp.ids, value)) == 0:
            print(value, " is not a valid location.")
            value = "BAD"
    return value

def process_input(user_input):
    if user_input == "jack":
        jack.move()
        
    elif user_input == "reset":
        jack.reset()
        
    elif user_input == "godmode on":
        jack.set_godmode(True)
        
    elif user_input == "godmode off":
        jack.set_godmode(False)
        
    elif "ipos" in user_input:
        values = parse_ipos(user_input)
        if (len(values) == 3):
            jack.set_ipos(values)
        else:
            print("Invalid input")
            
    elif user_input == "status":
        jack.status()
        
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
            
    elif "help" in user_input:
        print("Commands are:")
        print("   jack:                         Jack takes his turn")
        print("   reset:                        Restart the game")
        print("   godmode <on,off>:             Toggle godmode")
        print("   ipos <pos1>, <pos2>, <pos3>:  Enter the inspector locations")
        print("   status:                       View the current game status")
        print("   arrest <pos>:                 Attempt arrest at the specified position")
        print("   clues <pos1>,..,<posX>:       Search for clues at the supplied locations in the specified order")
        if (jack.godmode):
            print("   jackpos <pos>:       Move Jack to the specified location for debugging")
    else:
        print("Unknown command.")

# Input loop
while True:
    user_input = input("> ")
    
    if user_input == "exit":
        print("Goodbye!")
        break

    process_input(user_input)

# Save the graph so I can debug the contents to make sure I'm 
# building it correctly and restoring weights correctly
ug.save("my_graph_after.graphml")
