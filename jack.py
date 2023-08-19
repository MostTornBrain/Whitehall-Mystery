from graph_tool.all import *
from graph_data import *
import random

WATER = 1


def reset_graph_color_and_shape(ug):
    # iterate over all the nodes
    for node in ug.vertices():
        ug.vp.vcolor[node] = "#000000"
    
        if 'c' in ug.vp.ids[node]:
            ug.vp.vshape[node] = "square"
            ug.vp.vsize[node] = 8
            ug.vp.vfsize[node] = 8
        else:
            ug.vp.vshape[node] = "circle"
            ug.vp.vsize[node] = 18
            ug.vp.vfsize[node] = 10

    # Color ispector starting positions yellow
    for node in starting_ipos:
        # TODO: maybe insert another unconnected node here and make it slightly bigger to get the yellow frame?
        v = find_vertex(ug, ug.vp.ids, node)[0]
        ug.vp.vcolor[v] = "#FFD700"

    # Color all the destinations in the four quadrants white
    for q in quads:
        for num in q:
            v = find_vertex(ug, ug.vp.ids, num)[0]    
            ug.vp.vcolor[v] = "#ffffff"

    # Make water destinations blue
    for num in water:
        v=find_vertex(ug, ug.vp.ids, num)[0]    
        ug.vp.vcolor[v] = "#0000FF"


class Jack:
    def __init__(self, g, ipos, godmode):
        self.graph = g
        self.godmode = godmode
        self.ipos = ipos
        
        self.game_in_progress = False
        
        self.targets = []
        self.crimes = []
        self.clues = []
        
        self.boat_cards = []
        self.alley_cards = []
        self.coach_cards = []
        
        self.path_used = []
        
        print("   Welcome!")
        print("   Type \033[1mhelp\033[0m at any time for a full list of commands.")
        print("   Use the \033[1mipos\033[0m command to specify the investigator starting locations.")
        print("   Then type \033[1mstart\033[0m to begin the game.")

    def reset(self):
        self.game_in_progress = True
        self.targets = []
        self.crimes = []
        self.clues = []
        reset_graph_color_and_shape(self.graph)
        
        # Jack gets two of each - track use by length of the array as the array will hold the turn the card was used.
        self.boat_cards = []
        self.alley_cards = []
        self.coach_cards = []
        
        self.set_water_weight(10)
        
        for q in quads:
            self.targets.append(random.choice(q))
        
        if (self.godmode):
            print("Jack shall visit ", self.targets)
        
        # Determine starting position and announce it
        self.choose_random_target()
        self.pos = self.active_target
        self.targets.remove(self.pos)
        self.crimes = [self.pos]
        self.path_used = [self.pos]
        print("Jack commits a crime at ", self.pos)
        
        self.completed_targets = [self.pos]
        
        if (self.godmode):
            print ("Jack starts at " + self.pos + " and is " + 
                str(shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], 
                                      find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0], weights=self.graph.ep.weight)) + 
                " away.")


    # Compute the travel cost for Jack to move from his current location 
    # to the supplied target.  This cost is weighted, not just a counting of vertices.
    def distance(self, target):
        v1 = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        v2 = find_vertex(self.graph, self.graph.vp.ids, target)[0]
            
        vlist, elist = shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
        
        distance = shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], v2, 
                                                                    weights=self.graph.ep.weight)
        return distance


    # choose the optimal target based on current location and investigator positions
    def choose_closest_target(self):
        best_distance = 10000000
        best_option = 0
        
        for option in self.targets:
            d = self.hop_count(option)
            if d < best_distance:
                best_option = option
                best_distance = d
                
        if best_option == 0:
            print("Woah! That's wrong!")
        
        self.active_target = best_option
        if (self.godmode):
            print("Best distance", best_distance)
            print("Jack chooses ", self.active_target)

    def choose_random_target(self):            
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

    # Find the second vertex in the vlist
    def find_second_location(self, vlist):
        index = 1
        while 'c' in self.graph.vp.ids[vlist[index]]:
            index=index+1
        index = index+1   # Skip over the first vertex
        while 'c' in self.graph.vp.ids[vlist[index]]:
            index=index+1        
        return self.graph.vp.ids[vlist[index]]

    # Poison all the paths (i.e. edges) that go through an inspector (i.e. ipos) as Jack isn't allowed to use those
    def poison(self, adjust):
        for num in range (0, 3):
            v = find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
        
            for e in v.all_edges():
                self.graph.ep.weight[e] += adjust

    # Discourage Jack from taking paths near inspectors by increasing the weights
    # This couldbe written recursivesly to allow more easy fine-tuning of the radiating weights over a distance
    # rather than being hardcoded to be only across a distance of 2
    def discourage(self, adjust):
        for num in range (0, 3):
            # Find the vertex belonging to the `num` inspector
            v = find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
            
            # Add a weight to all the edges one vertex away from the inspector
            for n in v.out_neighbors():
                for e in n.all_edges():
                    self.graph.ep.weight[e] += adjust
                    
                # Also weight to everything 2 vertices away, which will have a compounding effect 
                # on the inbound edges leading toward the inspect since they were already adjusted above
                for n1 in n.out_neighbors():
                    for e1 in n1.all_edges():
                        self.graph.ep.weight[e1] += adjust


    def status(self):
        print()
        print("Crimes: ", self.crimes)
        print("Clues: ", self.clues)
        print("ipos: ", self.ipos)
        print("Coach cards: ", 2 - len(self.coach_cards))
        print("Alley cards: ", 2 - len(self.alley_cards))
        print("Boat cards:  ", 2 - len(self.boat_cards))
        print("Moves remaining: ", 16 - self.turn_count())
        if (self.godmode):
            print("Here is the path Jack took:", self.path_used)
            print("Targets: ", self.targets)
        print
        

    def set_water_weight(self, weight):
        for edge in self.graph.edges():
            if self.graph.ep.transport[edge] == WATER:
                self.graph.ep.weight[edge] = weight
    
    
    # Calculate the number of vertices away from the target - every vertex should have a weight of 1
    def hop_count(self, dest):
        #unweight the water paths if Jack still has a boat card
        if (len(self.boat_cards) < 2):
            self.set_water_weight(1)
        
        v = find_vertex(self.graph, self.graph.vp.ids, dest)[0]
        shortest = shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], v, 
                                                            weights=self.graph.ep.weight)

        #re-weight the water paths if Jack still has a boat card
        if (len(self.boat_cards) < 2):
            self.set_water_weight(10)
        
        return shortest
        
    
    # If Jack is running out of moves, reduce the weights of water if he has boat cards
    def consider_desperate_weights(self, enabled):
        # TODO: consider alley weights
        if (self.turn_count() > 7):
            if (enabled):
                weight = 1
                if (self.godmode):
                    print("Jack is desperate")
            else:
                weight = 10
            
            if (len(self.boat_cards) < 2):
                self.set_water_weight(weight)

    def turn_count(self):
        return len(self.path_used)
        

    def find_nearest_vertex(self, prior_location):
        # Jack is not allowed to move to a target destination using a coach
        # Need to figure out how to pick another vertex that is 1 space away and isn't where he was previously
        print("Sorry, I have not yet implemented this type of move for Jack.")
        print("Jack was surrounded by investigators and tried to use a coach, but his goal was 2 spaces away and according to the rules a coach cannot be used for going directly there.")
        print("Jack was at location " + prior_location + " and is currently at " + self.pos)
    

    def move(self):
        if (not self.game_in_progress):
            print("No game in progress, please \033[1mstart\033[0m a game before trying to move Jack.")
            return
        
        coach_move = False

        # Always consider what is the best target to try - do this before poisoning/weighting routes
        self.choose_closest_target()
        
        # Poison the position of the inspectors (i.e. add weights)
        # TODO: if getting close to the end of the round and still have coach cards, maybe don't poison inspector paths and if one is chosen, use a coach?
        self.poison(1000)
        deterrent = random.choice([0,1,1,1])
        self.discourage(deterrent)
        self.consider_desperate_weights(True)
        
        v1 = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        v2 = find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0]
        
        vlist, elist = shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
        if (self.godmode):
            print([self.graph.vp.ids[v] for v in vlist])

        # Detect when surrounded (i.e shortest path to the next vertex is > 1000) and 
        # determine if any move is possible or if Jack is trapped and loses.
        if shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], vlist[1], 
                                                            weights=self.graph.ep.weight) >= 1000:
            if (len(self.coach_cards) < 2 and self.turn_count() < 13):
                # do coach move
                coach_move = True
            # TODO: consider alleys
            else:
                print("Jack cannot move.  You win!")
                print("Jack's current position: ", self.pos)
                return

        # un-poison the ipos edges
        self.poison(-1000)
        self.discourage(-deterrent)
        self.consider_desperate_weights(False)
              
        # If a water path was selected, spend the card
        if ((self.pos in water) and (self.graph.vp.ids[vlist[1]] in water)):
            print("Jack took a boat on turn %d!" % len(self.path_used))
            self.boat_cards.append(self.turn_count())
            if (len(self.boat_cards)>= 2):
                # poison all the water paths - Jack has no boat cards left
                self.set_water_weight(1000)
        
        self.pos = self.find_next_location(vlist)
        self.path_used.append(self.pos)

        # Count how far away the goal is now that Jack moved
        shortest = self.hop_count(self.active_target)
        
        if (coach_move):
            print("Jack takes a coach!")
            self.coach_cards.append(self.turn_count()-1)
            if self.godmode:
                print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")
            if (shortest > 1):
                self.pos = self.find_second_location(vlist)
                self.path_used.append(self.pos)
            else:
                self.find_nearest_vertex(self.path_used[-2])
            # Count how far away the goal is now that Jack moved
            shortest = self.hop_count(self.active_target)

                
        if self.godmode:
            print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")

        if self.pos == self.active_target:
            print("Jack has committed a crime at ", self.pos)
            print("Here is the path he took:", self.path_used)
            self.crimes.append(self.pos)
            self.path_used = [self.pos]
            self.targets.remove(self.pos)

        if (len(self.targets) == 0):
            print("Game over!  Jack won!")
            print("    Crime locations: ", self.crimes)
        else:
            print("Jack has ", 16 - self.turn_count(), " moves remaining.")

            # If shortest path is longer than remaining turns
            if (16 - self.turn_count() < shortest):
                print("Jack LOSES!  He cannot reach his target with the number of moves left.")
                print("Here is the path he took:", self.path_used)
                return

    def clue_search(self, pos_list):
        #TODO: verify clue location is next to an ipos?  Or just have players enforce the rules themselves.
        print("\nSearching for clues at: ", pos_list)
        for loc in pos_list:
            if loc in self.path_used:
                print("Clue found at ", loc, "!!")
                self.clues.append(loc)
                break
            else:
                print(loc, ": no clue")

    def arrest(self, pos):
        #TODO: verify arrest location is next to an ipos?  Or just have players enforce the rules themselves.
        if pos == self.pos:
            print("Congratulations!  You arrested Jack at location ", pos, "!")
            print("Here is the path he took:", self.path_used)
        else:
            print("Jack is not at location ", pos)

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
        
        