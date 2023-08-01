from graph_tool.all import *

def find_next_location(vlist, id_list):
    index = 1
    while 'c' in id_list[vlist[index]]:
        index=index+1
    return id_list[vlist[index]]

def poison(g, ipos, adjust):
    for num in range (0, 3):
        v = find_vertex(g, g.vp.ids, ipos[num])[0]
        
        for e in v.all_edges():
            #print ("Adjusting: " + str(g.ep.weight[e]))
            g.ep.weight[e] += adjust
            #print ("    New: " + str(g.ep.weight[e]))

def move_jack(g, ipos, pos, target):
    
    v1 = find_vertex(g, g.vp.ids, pos)[0]
    v2 = find_vertex(g, g.vp.ids, target)[0]
    
    # Poison the position of the inspectors (i.e. add weights)
    poison(g, ipos, 1000)
    
    vlist, elist = shortest_path(g, v1, v2, weights=g.ep.weight)
    print([g.vp.ids[v] for v in vlist])
    
    pos = find_next_location(vlist, g.vp.ids)
    
    #unposion the ipos edges
    poison(g, ipos, -1000)
    
    print("\nJack moves to -> " + pos + " and is " + str(shortest_distance(g, find_vertex(g, g.vp.ids, pos)[0], v2, weights=g.ep.weight)) + " away.")
    return pos


def find_next_ilocation(vlist, id_list):
    index = 1
    while (index < len(vlist)-1) and 'c' not in id_list[vlist[index]]:
        index=index+1
    
    # Don't move the inspector onto a destination
    if 'c' not in id_list[vlist[index]]:
        index = 0

    return id_list[vlist[index]]
    
# Let inspectors always move towards Jack to test Jack's algorithm
def move_inspectors(g, ipos, jack_pos):
    for num in range (0, 3):
        v1 = find_vertex(g, g.vp.ids, ipos[num])[0]
        v2 = find_vertex(g, g.vp.ids, jack_pos)[0]
        vlist, elist = shortest_path(g, v1, v2)
        #print([g.vp.ids[v] for v in vlist])
        
        pos = find_next_ilocation(vlist, g.vp.ids)
        ipos[num]=pos
        print("Inspector #" + str(num) + " moved to " + pos +" and is now " + 
            str(shortest_distance(g, find_vertex(g, g.vp.ids, pos)[0], v2)) + " distance")
            
        
        