from graph_tool.all import *
from graph_data import *
import random

WATER = 1

NORMAL_MOVE = 0
BOAT_MOVE = 1
COACH_MOVE = 2
ALLEY_MOVE = 3
DEFAULT_WATER_WEIGHT = 10
POISON = 1000

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
    def __init__(self, g, ipos):
        self.graph = g
        self.ipos = ipos
        self.godmode = False
        
        self.game_in_progress = False
        
        self.targets = []
        self.completed_targets = []
        self.crimes = []
        self.clues = []
        
        # For bookkeeping these get populated with the turn number they are used
        self.boat_cards = []
        self.alley_cards = []
        self.coach_cards = []
        
        self.path_used = []
        
        print("   Welcome!")
        print("   Type \033[1mhelp\033[0m at any time for a full list of commands.")
        print("   Use the \033[1mipos\033[0m command to specify the investigator starting locations.")
        print("   Then type \033[1mstart\033[0m to begin the game.")


    def make_pdf(self):
        # Recolor the graph from scratch - yes, it's inefficient, but easier to do than undo previous ipos coloring, etc.
        reset_graph_color_and_shape(self.graph)
        
        if (self.godmode):
            # show Jack on the map
            for loc in self.path_used:
                self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, loc)[0]] = "cyan"
            if hasattr(self, 'pos'):
                self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]] = "cyan"
                self.graph.vp.vshape[find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]] = "double_circle"
        
        for target in self.crimes:    
            self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, target)[0]] = "red"
    
        for clue in self.clues:
            self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, clue)[0]] = "yellow"
        
        for pos in self.ipos:
            self.graph.vp.vshape[find_vertex(self.graph, self.graph.vp.ids, pos)[0]] = "hexagon"
        
        self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, self.ipos[0])[0]] = "yellow"
        self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, self.ipos[1])[0]] = "blue"
        self.graph.vp.vcolor[find_vertex(self.graph, self.graph.vp.ids, self.ipos[2])[0]] = "red"
                
        # We don't want curved edges - define a common Bezier control so the lines are straight.
        # This will make the two edges overlap and look like a single edge with an arrow on each end.
        control = [0.3, 0, 0.7, 0]
    
        graph_draw(self.graph,  vertex_text=self.graph.vp.ids, vertex_fill_color=self.graph.vp.vcolor, 
                      vertex_shape=self.graph.vp.vshape, vertex_size=self.graph.vp.vsize,
                      vertex_font_size=self.graph.vp.vfsize,
                      pos=self.graph.vp.pos, output_size=(873,873), edge_pen_width=1, edge_color=self.graph.ep.ecolor,
                      edge_marker_size=4,
                      edge_control_points=control,
                      output="jack.pdf")


    def godmode_print(self, *msg):
        if (self.godmode):
            print(*msg)

    def reset(self):
        self.game_in_progress = True
        self.targets = []
        self.crimes = []
        self.clues = []
        self.path_used = []
        reset_graph_color_and_shape(self.graph)
        
        # Jack gets two of each - track use by length of the array as the array will hold the turn the card was used.
        self.boat_cards = []
        self.alley_cards = []
        self.coach_cards = []
        
        self.set_water_weight(DEFAULT_WATER_WEIGHT)
        
        for q in quads:
            self.targets.append(random.choice(q))
        
        self.godmode_print("Jack shall visit ", self.targets)
        
        # Determine starting position.  It will be and announced as part of Jack's first move
        self.choose_starting_target()
        self.pos = self.active_target
        
        self.godmode_print("Jack starts at " + self.pos + " and is " + 
                str(self.hop_count(self.pos, self.active_target)) + 
                " away.")
                
        # Perform Jack's first move of the game
        self.move()

    
    # Calculate the number of vertices away from the target - every vertex should have a weight of 1
    def hop_count(self, src, dest):
        #unweight the water paths if Jack still has a boat card
        if (len(self.boat_cards) < 2):
            self.set_water_weight(1)
        
        v1 = find_vertex(self.graph, self.graph.vp.ids, src)[0]
        v2 = find_vertex(self.graph, self.graph.vp.ids, dest)[0]
        shortest = shortest_distance(self.graph, v1, v2, weights=self.graph.ep.weight)

        #re-weight the water paths if Jack still has a boat card
        if (len(self.boat_cards) < 2):
            self.set_water_weight(DEFAULT_WATER_WEIGHT)
        
        return shortest

    # choose the optimal target based on current location and investigator positions
    def choose_closest_target(self):
        best_distance = 10000000
        best_option = 0
        
        for option in self.targets:
            d = self.hop_count(self.pos, option)
            if d < best_distance:
                best_option = option
                best_distance = d
                
        if best_option == 0:
            print("Woah! That's wrong!")
        
        self.active_target = best_option
        self.godmode_print("Best distance", best_distance)
        self.godmode_print("Jack chooses \033[1m", self.active_target, "\033[0m")


    def choose_starting_target(self):            
        candidates = []
        farthest_dist  = 0
        farthest_mean = 0
        
        '''   Temporarily disable target choosing
        # Built a list of targets that aren't aren't too close to the investigators
        for target in self.targets:
            closest_dist = 100
            closest_mean = 0
            
            self.godmode_print("Considering target: ", target)
            # Consider how close each investigator is
            for pos in self.ipos:
                dist = self.hop_count(target, pos)
                closest_mean += dist
                self.godmode_print("   ipos " + pos + " is " + str(dist) + " away.")
                if dist < closest_dist:
                    closest_dist = dist

            closest_mean = closest_mean / 3
            self.godmode_print("  Closest dist:", closest_dist)
            self.godmode_print("  Closest mean:", closest_mean)
            
            # If farthest away so far, save it for choice of last resort.
            # IF distances are equal, consider the average distance as a tie breaker
            if (closest_dist > farthest_dist) or (closest_dist == farthest_dist and closest_mean > farthest_mean):
                farthest_target = target
                farthest_dist = closest_dist
                farthest_mean = closest_mean
            
            # If Far enough away, add to the candidate list
            if closest_dist > 3:
                self.godmode_print("Adding " + target + " to the candidate list.")
                candidates.append(target)

        # If we have targets that are not too close, pick one randomly
        if len(candidates) > 0:
            self.active_target = random.choice(candidates)
        else:
            self.godmode_print("All the targets are close to an investigator. Choosing the farthest of all 4...")
            self.active_target = farthest_target
        '''
        
        self.active_target = random.choice(self.targets)
        self.godmode_print("Jack chooses ", self.active_target)
        
        
    def set_ipos(self, i):
        self.ipos = i
        print("ipos: ", self.ipos)
        self.make_pdf()

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
    def discourage(self, adjust):
        for num in range (0, 3):
            # Find the vertex belonging to the `num` inspector
            v = find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
            # follow paths up to 3 away and adjust them all
            self.discourage_recursion(v, adjust, 3)

    def discourage_recursion(self, v, adjust, depth):
        depth = depth - 1
        # Add a weight to all the edges one vertex away from v
        for n in v.out_neighbors():
            for e in n.all_edges():
                self.graph.ep.weight[e] += adjust
            if depth > 0:
                self.discourage_recursion(n, adjust, depth)

    def status(self):
        print()
        print("Crimes: ", self.crimes)
        print("Clues: ", self.clues)
        print("ipos: ", self.ipos)
        print("Coach cards: ", 2 - len(self.coach_cards))
        print("Alley cards: ", 2 - len(self.alley_cards))
        print("Boat cards:  ", 2 - len(self.boat_cards))
        print("Moves remaining: ", 16 - self.turn_count())
        self.godmode_print("Here is the path Jack took:", self.path_used)
        self.godmode_print("Targets: ", self.targets)
        print
        

    def set_water_weight(self, weight):
        for edge in self.graph.edges():
            if self.graph.ep.transport[edge] == WATER:
                self.graph.ep.weight[edge] = weight
            
    
    # If Jack is running out of moves,
    # or he is trying to reach the final target, 
    # then reduce the weights of water if he still has boat cards
    def consider_desperate_weights(self, enabled):
        # TODO: consider alley weights
        if (self.turn_count() > 7) or (len(self.targets) == 1):
            if (enabled):
                weight = 1
                self.godmode_print("Jack is desperate")
            else:
                weight = DEFAULT_WATER_WEIGHT
            
            if (len(self.boat_cards) < 2):
                self.set_water_weight(weight)

    def turn_count(self):
        return len(self.path_used)
        

    def find_adjacent_nongoal_vertex(self, prior_location):
        # Jack is not allowed to move to a target destination using a coach
        # Pick another vertex that is 1 space away and isn't where he was previously, since that is also against the rules
        cur_pos = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        # Find locations (i.e. not crossings) with a weighted distance of 1
        dist_map = list(shortest_distance(self.graph, cur_pos, max_dist=1, weights=self.graph.ep.weight))
        vertices_with_distance_one = [
            self.graph.vp.ids[v] for v in self.graph.iter_vertices() if (dist_map[v] == 1 and 'c' not in self.graph.vp.ids[v])
        ]
        if prior_location in vertices_with_distance_one:
            vertices_with_distance_one.remove(prior_location)
        self.godmode_print("These are all 1 away from ", self.pos)
        self.godmode_print(vertices_with_distance_one)
        if (len(vertices_with_distance_one) > 0):
            choice = random.choice(vertices_with_distance_one)
            self.godmode_print("Choosing:", choice)
        else:
            choice = "NULL"
        return choice

    
    def consider_coach_move(self):
        ret = NORMAL_MOVE
        if len(self.coach_cards) < 2:
            closest = 100
            average = 0
            
            # Find how far away each investigator is from Jack - don't use weights - we want to count edges
            for ipos in self.ipos:
                v = find_vertex(self.graph, self.graph.vp.ids, ipos)[0]
                dist = shortest_distance(self.graph, find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], v)
                self.godmode_print("ipos " + ipos + " is " + str(dist) + " away.")
                average += dist
                if dist < closest:
                    closest = dist
            average = average / 3
            self.godmode_print("Average = ", average)
            
            on_clue = (self.pos in self.clues) or (self.pos == self.crimes[-1])
            
            # If the investigator crossing is adjacent to Jack, or all the investigators on average are close, 
            # or Jack is searching for the final target on his list and the investigators are somewhat close,
            # it is "too close", so Jack should use a coach card.
            # TODO - add some random variability to the threshold?  
            #        or maybe if the number of clues found is over X _and_ the average is < Y
            #        or maybe if the running average is < X over Y turns?
            if ((closest < 2 and on_clue) or average < 2.5) or (len(self.targets) == 1 and average < 4):
                ret = COACH_MOVE
        return ret

    # Choose the path when Jack has decided he needs to use a coach
    def pick_a_coach_path(self):
        # compute shortest path without any poisoned paths since Jack can move through investigators using a coach
        # but... Jack cannot take a boat at the same time, so poison the water routes
        
        self.set_water_weight(POISON)
        
        # decide on a path
        deterrents = [2, 1, 0.5, 0.25, 0]
        for deterrent in deterrents:
            v1 = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
            v2 = find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0]

            self.discourage(deterrent)
            vlist = random_shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
            self.discourage(-deterrent)
            
            # Compute the cost of this chosen path.  Easiest to just count the entries that aren't crossing
            cost = sum(1 for entry in vlist if 'c' not in self.graph.vp.ids[entry]) - 1
            self.godmode_print("   Considering coach cost: ", cost)
            
            # TODO: Make sure Jack doesn't choose a path 2 away from the goal as that is against the rules
            # NOTE: we currently enforce this rule elsewhere in the code in move().
                
            if (cost <= (16 - self.turn_count())):
                self.godmode_print("   Jack finds this cost acceptable.")
                break;
        
        self.set_water_weight(DEFAULT_WATER_WEIGHT)
        return vlist
    
    
    def pick_a_path(self, deterrent):
        move_type = NORMAL_MOVE
        
        # Poison the position of the inspectors (i.e. add weights)
        # TODO: if getting close to the end of the round and still have coach cards, maybe don't poison inspector paths and if one is chosen, use a coach?
        self.poison(POISON)
        self.discourage(deterrent)
        self.consider_desperate_weights(True)
                
        v1 = find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        v2 = find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0]
        
        vlist = random_shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
        self.godmode_print([self.graph.vp.ids[v] for v in vlist])

        # Detect when surrounded (i.e shortest path to the next vertex is > 1000) and 
        # determine if any move is possible or if Jack is trapped and loses.
        if shortest_distance(self.graph, v1, vlist[1], weights=self.graph.ep.weight) >= POISON:
            if (len(self.coach_cards) < 2 and self.turn_count() < 13):
                # do coach move
                move_type = COACH_MOVE
            # TODO: consider alleys
            else:
                print("Jack cannot move.  You win!")
                print("Jack's current position: ", self.pos)
                self.game_in_progress = False

        # un-poison the ipos edges
        self.poison(-POISON)
        self.discourage(-deterrent)
        self.consider_desperate_weights(False)
        
        # Compute the cost of this chosen path.  Easiest to just count the entries that aren't crossing
        cost = sum(1 for entry in vlist if 'c' not in self.graph.vp.ids[entry]) - 1
        self.godmode_print("    Cost: ", cost)
        
        return [vlist, cost, move_type]
        
        
    def move(self):
        if (not self.game_in_progress):
            print("No game in progress, please \033[1mstart\033[0m a game before trying to move Jack.")
            return
        
        # Per the rules, Jack does not announce he has reached his target until AFTER the investigators take their turn.
        # For this reason, we perform this check here before his next move.
        if self.pos == self.active_target:
            print("A crime has been discovered at \033[1m" + self.pos + "\033[0m and Jack has moved on.")
            if (len(self.path_used) > 0):
                # TODO: this isn't really part of the rules, but might be helpful during play
                print("Here is the path he took:", self.path_used)
            self.crimes.append(self.pos)
            self.path_used = [self.pos]
            self.targets.remove(self.pos)
            self.clues = []

        if (len(self.targets) == 0):
            print("Game over!  Jack won!")
            print("    Crime locations: ", self.crimes)
            self.make_pdf()
            self.game_in_progress = False
            return
        
        # Each turn reconsider what is the best target to try
        # Do this before poisoning the routes
        self.choose_closest_target()
        
        # decide on a path
        deterrents = [2, 1, 0.5, 0.25, 0]
        for deterrent in deterrents:
            vlist, cost, move_type = self.pick_a_path(deterrent)
            if not self.game_in_progress:
                return
            if (cost <= (16 - self.turn_count())):
                self.godmode_print("   Jack finds this cost acceptable.")
                break;
        
        # If a water path was selected, spend the card - NOTE: this should never happen if a coach move was selected above so we do not check for move_type being set to COACH_MOVE
        if ((self.pos in water) and (self.graph.vp.ids[vlist[1]] in water)):
            print("Jack took a boat on turn %d!" % len(self.path_used))
            self.boat_cards.append(self.turn_count())
            move_type = BOAT_MOVE
            if (len(self.boat_cards)>= 2):
                # poison all the water paths - Jack has no boat cards left
                self.set_water_weight(POISON)
        
        # Have you consider the advantages to taking a COACH?
        if (move_type == NORMAL_MOVE):
            # If we are one space away from the goal, don't use a coach, otherwise, think about it.
            if (self.hop_count(self.pos, self.active_target) != 1):
                move_type = self.consider_coach_move()
                
        
        if (move_type == COACH_MOVE):
            vlist = self.pick_a_coach_path()
            self.godmode_print("\033[1mChoosing this for a coach path:\033[0m")
            self.godmode_print([self.graph.vp.ids[v] for v in vlist])
        
        self.pos = self.find_next_location(vlist)
        self.path_used.append(self.pos)

        # Count how far away the goal is now that Jack moved
        shortest = self.hop_count(self.pos, self.active_target)
        
        # If Jack is doing a coach move, he moves a second time.
        # Since we aready computed the shortest path above, just go to the next location in that path.
        if (move_type == COACH_MOVE):
            print("Jack takes a coach!")
            self.coach_cards.append(self.turn_count()-1)
            self.godmode_print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")
            
            if (shortest > 1):
                self.pos = self.find_second_location(vlist)
            else:
                # make sure we don't use a coach to get to the goal - pick another location 1 space away
                self.pos = self.find_adjacent_nongoal_vertex(self.path_used[-2])
                
                if self.pos == "NULL":
                    # I _think_ this case is impossible based on the map layout, but just in case....
                    print("Jack LOSES!")
                    print("Jack tried to use a coach, but his goal was 2 spaces away and according to the rules a coach cannot be used for going directly to his goal.")
                    print("Jak tried to find another location 1 space away, but there was no other legal place to move, so he is trapped.")
                    print("Jack was at location " + prior_location + " and is currently at " + self.pos)
                    print("Here is the full path he took:", self.path_used)
                    return
            self.path_used.append(self.pos)
            
            # Count how far away the goal is now that Jack moved
            shortest = self.hop_count(self.pos, self.active_target)
        
        self.godmode_print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")

        print("Jack has \033[1m", 16 - self.turn_count(), "\033[0m moves remaining.")

        # If shortest path is longer than remaining turns
        if (16 - self.turn_count() < shortest):
            print("Jack LOSES!  He cannot reach his target with the number of moves left.")
            print("Here is the path he took:", self.path_used)
            return
        self.make_pdf()

    def clue_search(self, pos_list):
        #TODO: verify clue location is next to an ipos?  Or just have players enforce the rules themselves.
        print("\nSearching for clues at: ", pos_list)
        for loc in pos_list:
            if loc in self.path_used:
                print("Clue found at ", loc, "!!")
                self.clues.append(loc)
                self.make_pdf()
                break
            else:
                print(loc, ": no clue")

    def arrest(self, pos):
        #TODO: verify arrest location is next to an ipos?  Or just have players enforce the rules themselves.
        if pos == self.pos:
            print("Congratulations!  You arrested Jack at location ", pos, "!")
            print("Here is the path he took:", self.path_used)
            self.game_in_progress = False
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
        
        