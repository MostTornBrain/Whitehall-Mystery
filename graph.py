from graph_tool.all import *
from graph_data import *
from jack import *

ug = Graph(edge_list, hashed=True, eprops=[("weight", "int"), ("transport", "int")])

vcolor = ug.new_vp("string")
vshape = ug.new_vp("string")
vsize = ug.new_vp("int")
vfsize = ug.new_vp("int")

# iterate over all the nodes
for node in ug.vertices():
    vcolor[node] = "#000000"
    
    if 'c' in ug.vp.ids[node]:
        vshape[node] = "square"
        vsize[node] = 5
        vfsize[node] = 5
    else:
        vshape[node] = "circle"
        vsize[node] = 18
        vfsize[node] = 10

# Color all the destinations in the four quadrant white
for num in q1:
    v=find_vertex(ug, ug.vp.ids, num)[0]    
    vcolor[v] = "#ffffff"

for num in q2:
    v=find_vertex(ug, ug.vp.ids, num)[0]    
    vcolor[v] = "#ffffff"

for num in q3:
    v=find_vertex(ug, ug.vp.ids, num)[0]    
    vcolor[v] = "#ffffff"

for num in q4:
    v=find_vertex(ug, ug.vp.ids, num)[0]    
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

# Make these properties part internal to the graph so they get saved if we save the graph to a file
ug.vp.pos = vpos
ug.vp.vcolor = vcolor
ug.vp.vshape = vshape
ug.vp.vsize = vsize
ug.vp.vfsize = vfsize

# Save it so I can debug the contents to make sure I'm building it correctly
ug.save("my_graph.graphml")

ug.list_properties()

# We don't want curved edges - define a common Bezier control so the lines are straight.
# This will make the two edges overlap and look like a single edge with an arrow on each end.
control = [0.3, 0, 0.7, 0]

graph_draw(ug,  vertex_text=ug.vp.ids, vertex_fill_color=vcolor, vertex_shape=vshape, vertex_size=vsize,
              vertex_font_size=vfsize,
              pos=vpos, output_size=(873,873), edge_pen_width=1,
              edge_marker_size=4,
              edge_control_points=control,
              output="graph-draw.pdf")

'''
v = find_vertex(ug, ug.vp.ids, "1c2")[0]

print(ug.ep.weight.a)
for e,f in ug.iter_all_edges(v):
    print(e,f)

print(ug.edge_properties["weight"].a)
'''
              
ipos = ["87c1", "91c1", "77c1"]

jack_pos = "79"
jack_target = "71"
print ("Jack starts at " + jack_pos + " and is " + str(shortest_distance(ug, find_vertex(ug, ug.vp.ids, jack_pos)[0], find_vertex(ug, ug.vp.ids, jack_target)[0], weights=ug.ep.weight)) + " away.")

while jack_pos != jack_target:
    move_inspectors(ug, ipos, jack_pos)
    jack_pos = move_jack(ug, ipos, jack_pos, jack_target)

# Save it so I can debug the contents to make sure I'm building it correctly
ug.save("my_graph_after.graphml")
