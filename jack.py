from graph_tool.all import *

class Jack:
    def __init__(self, g, ipos, godmode):
        self.graph = g
        self.ipos = ipos
        self.godmode = godmode
        
        self.pos = ""
        self.target = []
        self.target_quad = 0
        self.completed_target = []
        self.quads_remaining = [1, 2]  # TODO: add 3, 4 when the map is finished being entered
        
        #TODO: choose target via choose_new_target()
        # right now just hardcode one for testing
        self.pos = "79"
        self.target = "71"
        self.target_quad = 1
        self.completed_targets = ["79"]
        self.quads_remaining = [ 3, 4]
        
        if (self.godmode):
            print ("Jack starts at " + self.pos + " and is " + str(shortest_distance(g, find_vertex(g, g.vp.ids, self.pos)[0], 
                find_vertex(g, g.vp.ids, self.target)[0], weights=g.ep.weight)) + " away.")

    def choose_new_target(self):
        # Figure out which quadrants haven't been completed and choose the optimal one
        # based on current location and investigator positions
        print("Not implemented yet")

    def set_godmode(self, b):
        self.godmode = b

    def find_next_location(self, vlist):
        index = 1
        while 'c' in self.graph.vp.ids[vlist[index]]:
            index=index+1
        return self.graph.vp.ids[vlist[index]]

    def poison(self, adjust):
        for num in range (0, 3):
            v = find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
        
            for e in v.all_edges():
                #print ("Adjusting: " + str(g.ep.weight[e]))
                self.graph.ep.weight[e] += adjust
                #print ("    New: " + str(g.ep.weight[e]))

        
        
    def move(self):
    
        v1 = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        v2 = find_vertex(self.graph, self.graph.vp.ids, self.target)[0]
    
        # Poison the position of the inspectors (i.e. add weights)
        self.poison(1000)
    
        vlist, elist = shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
        if (self.godmode):
            print([self.graph.vp.ids[v] for v in vlist])
    
        self.pos = self.find_next_location(vlist)
    
        # un-poison the ipos edges
        self.poison(-1000)
        
        if self.godmode:
            print("\nJack moves to -> " + self.pos + " and is " + 
                str(shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], v2, 
                                                            weights=self.graph.ep.weight)) + " away.")
        
        if self.pos == self.target:
            print("Jack has committed a crime at ", self.pos)
            self.completed_targets.append(self.target)
            self.choose_new_target()

    def do(self):
        self.move()
        

'''
    def find_next_ilocation(self, vlist, id_list):
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
'''            
        
        