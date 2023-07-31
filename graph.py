from graph_tool.all import *

from graph_data import *

ug = Graph(edge_list, hashed=True, eprops=[("weight", "int"), ("water", "boolean")])
                
# We want directed edges
#ug.set_directed(False)
#assert ug.is_directed() == False

vcolor = ug.new_vp("string")     # creates a VertexPropertyMap of type string
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

for num in water:
    v=find_vertex(ug, ug.vp.ids, num)[0]    
    vcolor[v] = "#0000FF"


vpos = ug.new_vp("vector<double>")

for pair in positions:
    v=find_vertex(ug, ug.vp.ids, pair[0])[0]
    vpos[v] = pair[1]

# Print out nodes with missing positions
for node in ug.vertices():
    if not (vpos[node]):
        print("        [\"%s\", [,-]]," % ug.vp.ids[node])

# Make these properties part internal to the graph
ug.vp.pos = vpos
ug.vp.vcolor = vcolor
ug.vp.vshape = vshape
ug.vp.vsize = vsize
ug.vp.vfsize = vfsize

# Save it so I can debug the contents to make sure I'm building it correctly
ug.save("my_graph.graphml")

ug.list_properties()

# We don't want curved edges - define the Bezier controls so the lines are straight
control = ug.new_edge_property("vector<double>")
for e in ug.edges():
    d = 0
    control[e] = [0.3, d, 0.7, d]

graph_draw(ug,  vertex_text=ug.vp.ids, vertex_fill_color=vcolor, vertex_shape=vshape, vertex_size=vsize,
              vertex_font_size=vfsize,
              pos=vpos, output_size=(873,873), edge_pen_width=1,
              edge_marker_size=4,
              edge_control_points=control,
              output="graph-draw.pdf")

# Test finding shortest path between two nodes
v1 = find_vertex(ug, ug.vp.ids, "1")[0]
v2 = find_vertex(ug, ug.vp.ids, "41")[0]

vlist, elist = shortest_path(ug, v1, v2, weights=ug.ep.weight)
print([ug.vp.ids[v] for v in vlist])
