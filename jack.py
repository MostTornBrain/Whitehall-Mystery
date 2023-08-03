from graph_tool.all import *
from graph_data import *
import random

class Jack:
    def __init__(self, g, ipos, godmode):
        self.graph = g
        self.godmode = godmode
        self.ipos = ipos
        self.reset()

    def reset(self):
        self.targets = []
        self.crimes = []
        self.clues = []
        
        for q in quads:
            self.targets.append(random.choice(q))
        # TODO: For now, only use two quads since the whole map has been entered
        del self.targets[3];
        del self.targets[2];
        if (self.godmode):
            print("Jack shall visit ", self.targets)
        
        # Determine starting position and announce it
        self.choose_closest_target()
        self.pos = self.active_target
        self.targets.remove(self.pos)
        self.crimes = [self.pos]
        self.path_used = [self.pos]
        print("Jack commits a crime at ", self.pos)
        
        self.choose_closest_target()
        self.completed_targets = [self.pos]
        
        if (self.godmode):
            print ("Jack starts at " + self.pos + " and is " + str(shortest_distance(g, find_vertex(g, g.vp.ids, self.pos)[0], 
                find_vertex(g, g.vp.ids, self.active_target)[0], weights=g.ep.weight)) + " away.")
        
    def choose_closest_target(self):
        # TODO: choose the optimal target based on current location and investigator positions
        # For now it is random
        self.active_target = random.choice(self.targets)
        if (self.godmode):
            print("Jack chooses ", self.active_target)
        
    def set_godmode(self, b):
        self.godmode = b

    def set_ipos(self, i):
        self.ipos = i
        print("ipos: ", self.ipos)

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

    def status(self):
        print()
        print("Crimes: ", self.crimes)
        print("Clues: ", self.clues)
        print("ipos: ", self.ipos)
        print("Moves remaining: ", 16 - len(self.path_used))
        print
        
    def move(self):
        # Always consider what is the best target to try
        self.choose_closest_target()
    
        v1 = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        v2 = find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0]
    
        # Poison the position of the inspectors (i.e. add weights)
        self.poison(1000)
    
        vlist, elist = shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
        if (self.godmode):
            print([self.graph.vp.ids[v] for v in vlist])
    
        self.pos = self.find_next_location(vlist)
        self.path_used.append(self.pos)
        
        # un-poison the ipos edges
        self.poison(-1000)
        
        if self.godmode:
            print("\nJack moves to -> " + self.pos + " and is " + 
                str(shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], v2, 
                                                            weights=self.graph.ep.weight)) + " away.")
        
        if self.pos == self.active_target:
            print("Jack has committed a crime at ", self.pos)
            print("Here is the path he took:", self.path_used)
            self.crimes.append(self.pos)
            self.path_used = [self.pos]
            self.targets.remove(self.pos)
            if len(self.targets) > 0:
                self.choose_closest_target()

        if (len(self.targets) == 0):
            print("Game over!  Jack won!")
            print("    Crime locations: ", self.crimes)
        else:
            print("Jack has ", 16 - len(self.path_used), " moves remaining.")

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
        
        