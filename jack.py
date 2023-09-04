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
from graph_data import *
import random

# How many extra turns should Jack leave as "buffer" for completing his path
TURN_BUFFER = 3
DEFAULT_WATER_WEIGHT = 3
DEFAULT_ALLEY_WEIGHT = 13
DETERRENT_WEIGHTS = [6, 3, 1, 0]

# This difficulty rating is from JACK's point of view, not the players'
EASY_BUCKET = 0
HARD_BUCKET = 1

NORMAL_MOVE = 0
BOAT_MOVE = 1
ALLEY_MOVE = 2
COACH_MOVE = 3

POISON = 1000

TEXT_MSG=0
IMG_REFRESH=1
SPECIAL_TRAVEL_MSG=2
NEW_ROUND_MSG=3

JACK_MOVE_COLOR = "#e6988f"
WATER_COLOR = "#5eb2fb"
STARTING_CROSSINGS_COLOR = "#ece99c"
YELLOW_INVESTIGATOR_COLOR = "yellow"
BLUE_INVESTIGATOR_COLOR = "#2929d5"
RED_INVESTIGATOR_COLOR = "red"
CLUE_COLOR = "#f3f342"
CRIME_COLOR = "#dd1e1e"

def reset_graph_color_and_shape(ug, scale=1):
    # iterate over all the nodes
    for node in ug.vertices():
        ug.vp.vcolor[node] = "#000000"
    
        if 'c' in ug.vp.ids[node]:
            ug.vp.vshape[node] = "square"
            ug.vp.vsize[node] = 8*scale
            ug.vp.vfsize[node] = 8*scale
        else:
            ug.vp.vshape[node] = "circle"
            ug.vp.vsize[node] = 18*scale
            ug.vp.vfsize[node] = 10*scale

    # Color ispector starting positions yellow
    for node in starting_ipos:
        # TODO: maybe insert another unconnected node here and make it slightly bigger to get the yellow frame?
        v = gt.find_vertex(ug, ug.vp.ids, node)[0]
        ug.vp.vcolor[v] = STARTING_CROSSINGS_COLOR

    # Color all the destinations in the four quadrants white
    for q in quads:
        for num in q:
            v = gt.find_vertex(ug, ug.vp.ids, num)[0]    
            ug.vp.vcolor[v] = "#ffffff"

    # Make water destinations blue
    for num in water:
        v=gt.find_vertex(ug, ug.vp.ids, num)[0]    
        ug.vp.vcolor[v] = WATER_COLOR

class Jack:
    def __init__(self, g, ipos):
        self.file = open('whitehall.log', 'w')
        self.graph = g
        self.ipos = ipos
        self.godmode = False
        self.win = None
        self.pos = 0
        
        self.game_in_progress = False
        
        self.targets = []
        self.completed_targets = []
        self.crimes = []
        self.clues = []
        self.output_func = None
        
        # For bookkeeping these get populated with the turn number they are used
        self.boat_cards = []
        self.alley_cards = []
        self.coach_cards = []
        
        self.path_used = []
        
        # Rate all the potential target locations
        self.rate_quads()
        
        # Create a set of weights only used for the point of view of the investigators, 
        # so it omits alley and boat paths and it only weights entering crossings
        self.i_weight = self.graph.new_edge_property("float")
        self.i_weight.a = self.graph.ep.weight.a.copy()  # copy the underlying associative array
        for e in self.graph.edges():
            if self.graph.ep.transport[e] == NORMAL_MOVE:
                source = self.graph.vp.ids[e.source()]
                target = self.graph.vp.ids[e.target()]
                if "c" in source and "c" not in target:
                    self.i_weight[e] = 0
                else:
                    self.i_weight[e] = 1
            else:
                self.i_weight[e] = POISON    # Don't use Jack's special paths (boats and alleys)
            
            
    def rate_quads(self):
        self.rated_quads = []
        for q in quads:
            min = 1000
            max = 0
            total = 0 
            count = 0
            
            # First pass: compute the range and average of the group
            for t in q:
                rating = self.location_safety_rating(t)
                if rating < min:
                    min = rating
                if rating > max:
                    max = rating
                total += rating
                count += 1
            avg = total/count
            
            avg_span_low = round(avg - ((avg - min + 1)/3))
            avg_span_high = round(avg + ((max - avg + 1)/3))
            
            # Second pass: put each into the proper graded bucket
            quad_bucket = [[],[],[]]
            for t in q:
                rating = self.location_safety_rating(t)
                if rating >= avg:
                    quad_bucket[EASY_BUCKET].append(t)
                # For now, only using 2 difficulty levels as using 3 limited the choices for easy and hard for certain quads
                #elif rating > avg_span_low:
                #    quad_bucket[MEDIUM_BUCKET].append(t)
                else:
                    quad_bucket[HARD_BUCKET].append(t)
            
            self.rated_quads.append(quad_bucket)
            #print(quad_bucket)

    def register_output_reporter(self, func):
        self.output_func = func
        
    def log_to_file(self, *msg):
        print(*msg, file=self.file)
        
    def print(self, *msg):
        if (self.output_func == None):
            print(*msg)
        else:
            self.output_func(TEXT_MSG, *msg)
        self.log_to_file(*msg)
        
    def gui_refresh(self):
        if (self.output_func is not None):
            self.output_func(IMG_REFRESH)
            
    def notify_gui_of_special_travel(self, travel_type):
        if (self.output_func is not None):
            self.output_func(SPECIAL_TRAVEL_MSG, travel_type)
        
        
    def make_image(self, scale=2):
        # Recolor the graph from scratch - yes, it's inefficient, but easier to do than undo previous ipos coloring, etc.
        reset_graph_color_and_shape(self.graph, scale)
        
        if (self.godmode):
            # show Jack on the map
            for loc in self.path_used:
                self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, loc)[0]] = JACK_MOVE_COLOR
            if hasattr(self, 'pos'):
                self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]] = JACK_MOVE_COLOR
                self.graph.vp.vshape[gt.find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]] = "double_circle"
        
        for target in self.crimes:    
            self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, target)[0]] = CRIME_COLOR
    
        for clue in self.clues:
            self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, clue)[0]] = CLUE_COLOR
        
        for pos in self.ipos:
            self.graph.vp.vshape[gt.find_vertex(self.graph, self.graph.vp.ids, pos)[0]] = "hexagon"
        
        self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[0])[0]] = YELLOW_INVESTIGATOR_COLOR
        self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[1])[0]] = BLUE_INVESTIGATOR_COLOR
        self.graph.vp.vcolor[gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[2])[0]] = RED_INVESTIGATOR_COLOR
                
        # We don't want curved edges - define a common Bezier control so the lines are straight.
        # This will make the two edges overlap and look like a single edge with an arrow on each end.
        control = [0.3, 0, 0.7, 0]
    
        self.win = gt.graph_draw(self.graph,  vertex_text=self.graph.vp.ids, vertex_fill_color=self.graph.vp.vcolor, 
                      vertex_shape=self.graph.vp.vshape, vertex_size=self.graph.vp.vsize,
                      vertex_font_size=self.graph.vp.vfsize, bg_color="white",
                      pos=self.graph.vp.pos, output_size=(873*scale,873*scale), edge_pen_width=1*scale, edge_color=self.graph.ep.ecolor,
                      edge_marker_size=4*scale,
                      edge_control_points=control,
                      #window=self.win, return_window=True, main=False)
                      output="jack.png")
        
        # Trigger the map to refresh in the GUI
        self.gui_refresh()


    def godmode_print(self, *msg):
        if (self.godmode):
            self.print(*msg)
        self.log_to_file(*msg)

    def pick_the_targets(self, difficulty):
        # Choose the 4 targets for the game
        for q in self.rated_quads:
            self.targets.append(random.choice(q[difficulty]))

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
        
        self.set_travel_weight(BOAT_MOVE, DEFAULT_WATER_WEIGHT)
        self.set_travel_weight(ALLEY_MOVE, DEFAULT_ALLEY_WEIGHT)
        
        self.pick_the_targets(EASY_BUCKET)
        
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
    def hop_count(self, src, dest, boats_reduced=True):
        #unweight the water paths if Jack still has a boat card
        if (boats_reduced) and (len(self.boat_cards) < 2):
            self.set_travel_weight(BOAT_MOVE, 1)
        
        v1 = gt.find_vertex(self.graph, self.graph.vp.ids, src)[0]
        v2 = gt.find_vertex(self.graph, self.graph.vp.ids, dest)[0]
        shortest = gt.shortest_distance(self.graph, v1, v2, weights=self.graph.ep.weight)

        #re-weight the water paths if Jack still has a boat card
        if (boats_reduced) and (len(self.boat_cards) < 2):
            self.set_travel_weight(BOAT_MOVE, DEFAULT_WATER_WEIGHT)
        
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
            self.print("Woah! That's wrong!")
        
        self.active_target = best_option
        self.godmode_print("Best distance", best_distance)
        self.godmode_print("Jack chooses \033[1m", self.active_target, "\033[0m")


    def choose_starting_target(self):
        self.active_target = random.choice(self.targets)
        return
        
        # Built a list of targets that aren't aren't too close to the investigators
        farthest_dist = 0
        farthest_mean = 0
        candidates = []
        
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
        
        
    def set_ipos(self, i):
        self.ipos = i
        self.print("ipos: ", self.ipos)
        self.make_image()

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
    # NOTE: This assumes this called alternatively with a positive then a negative value
    #       It saves the list of poisoned locations, then the next call uses that list for the unpoisoning
    def poison_investigators(self, adjust):
        if not hasattr(self, "is_poison"):
            self.is_poison = []

        if len(self.is_poison) == 0:
            for num in range (0, 3):
                # Only poison if the investigator crossing can be reached by Jack in less than 2 moves
                if self.hop_count(self.ipos[num], self.pos) < 2:
                    self.is_poison.append(num)
                    self.godmode_print("Investigator #", num, "is poison.")
                    v = gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
        
                    for e in v.all_edges():
                        self.graph.ep.weight[e] += adjust
        else:
            for num in self.is_poison:
                v = gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
        
                for e in v.all_edges():
                    self.graph.ep.weight[e] += adjust
            self.is_poison = [] # Discard the entries so next time this is called, we start over

    def investigator_distance(self, num):
        # Find the vertex belonging to the `num` ivestigator
        v = gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
        distance = gt.shortest_distance(self.graph, v, gt.find_vertex(self.graph, self.graph.vp.ids, self.pos)[0], weights=self.i_weight)
        return distance
        
    # Discourage Jack from taking paths near investigators by increasing the weights
    def discourage_investigators2(self, adjust):
        for num in range (0, 3):
            v = gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
            distance = self.investigator_distance(num)
            if (adjust > 0):
                self.godmode_print("Investigator#", num, "at", self.ipos[num], "is", distance, "away.")
            if distance <= 3:
                # Follow paths up to 2 spaces away (from the ivestigator's point of view)
                v = gt.find_vertex(self.graph, self.graph.vp.ids, self.ipos[num])[0]
                dist_map, visited = list(gt.shortest_distance(self.graph, v, max_dist=2, weights=self.i_weight, return_reached=True))
                for v in visited:
                    # Only discourage edges directly connected to a location.  Otherwise adjacent crossings poison a path too much.  Jack doesn't care about how many crossings he crosses.
                    if "c" not in self.graph.vp.ids[self.graph.vertex(v)]:
                        for e in self.graph.vertex(v).in_edges():
                            self.graph.ep.weight[e] += adjust
                            #print("   Discourage Edge : ", self.graph.vp.ids[e.source()], self.graph.vp.ids[e.target()], self.graph.ep.weight[e])
    
    def status(self):
        self.print()
        self.print("Crimes: ", self.crimes)
        self.print("Clues: ", self.clues)
        self.print("ipos: ", self.ipos)
        self.print("Coach cards: ", 2 - len(self.coach_cards))
        self.print("Alley cards: ", 2 - len(self.alley_cards))
        self.print("Boat cards:  ", 2 - len(self.boat_cards))
        self.print("Moves remaining: ", 16 - self.turn_count())
        self.godmode_print("Here is the path Jack took:", self.path_used)
        self.godmode_print("Targets: ", self.targets)
        print
        

    def set_travel_weight(self, transport_type, weight):
        for edge in self.graph.edges():
            if self.graph.ep.transport[edge] == transport_type:
                self.graph.ep.weight[edge] = weight
            
    
    # If Jack is running out of moves,
    # or he is trying to reach the final target, 
    # then reduce the weights of water if he still has boat cards
    def consider_desperate_weights(self, enabled):
        # TODO: consider alley weights
        if (self.turn_count() > 9) or (len(self.targets) == 1):
            if (enabled):
                weight = 1
                self.godmode_print("Jack is desperate")
            else:
                weight = DEFAULT_WATER_WEIGHT
            
            if (len(self.boat_cards) < 2):
                self.set_travel_weight(BOAT_MOVE, weight)

    def turn_count(self):
        return len(self.path_used)
        

    def free_edge_count(self, pos):
        raw_pos = gt.find_vertex(self.graph, self.graph.vp.ids, pos)[0]
        #calculate the out-degree but don't count boat or alley paths or poisoned paths
        out_degree = 0
        for edge in raw_pos.out_edges():
            if (self.graph.ep.transport[edge] == NORMAL_MOVE) and (self.graph.ep.weight[edge] < POISON):
                out_degree += 1
        return out_degree
    
    # Compute the safety rating of a location - HIGHER is SAFER
    def location_safety_rating(self, pos):
        one_away = self.locations_one_away(pos)
        out_degree = self.free_edge_count(pos)
        return len(one_away) * out_degree

    # Return the LOCATIONS (not crossings) exactly 1 space away from `source` assuming Jack's movement
    def locations_one_away(self, source):
        pos = gt.find_vertex(self.graph, self.graph.vp.ids, source)[0]
        dist_map = list(gt.shortest_distance(self.graph, pos, max_dist=1, weights=self.graph.ep.weight))
        return [
            self.graph.vp.ids[v] for v in self.graph.iter_vertices() if (dist_map[v] == 1 and 'c' not in self.graph.vp.ids[v])
        ]
    
    
    def find_adjacent_nongoal_vertex(self, prior_location):
        # Jack is not allowed to move to a target destination using a coach
        # Pick another vertex that is 1 space away and isn't where he was previously, since that is also against the rules
        vertices_with_distance_one = self.locations_one_away(self.pos)

        self.godmode_print("   removing:", prior_location)
        if prior_location in vertices_with_distance_one:
            vertices_with_distance_one.remove(loc)
        self.godmode_print("These are all 1 away from ", self.pos)
        self.godmode_print(vertices_with_distance_one)
        if (len(vertices_with_distance_one) > 0):
            choice = random.choice(vertices_with_distance_one)
            self.godmode_print("Choosing:", choice)
        else:
            choice = "NULL"
        return choice

    
    def consider_coach_move(self):
        ret = False
        if len(self.coach_cards) < 2:
            closest = 100
            average = 0
            
            dist = [0, 0, 0]
            # Find how far away each investigator is from Jack 
            for num in range(0,3):
                dist[num] = self.investigator_distance(num)
                self.godmode_print("ipos " + self.ipos[num] + " is " + str(dist[num]) + " away.")
                average += dist[num]
                if dist[num] < closest:
                    closest = dist[num]
            average = average / 3
            self.godmode_print("Average = ", average)
            
            num_very_close = 0
            for num in dist:
                if num <= 1:
                    num_very_close += 1
            self.godmode_print(num_very_close, "are very close.")
            
            # Is Jack on the most recent clue?
            on_clue = len(self.clues) > 0 and (self.pos == self.clues[-1])
            
            # How many outbound edges are not blocked by investigators?
            self.poison_investigators(POISON)
            free_edge_count = self.free_edge_count(self.pos)
            self.poison_investigators(-POISON)
            
            # If the investigator crossing is adjacent to Jack, or all the investigators on average are close, 
            # or Jack is searching for the final target on his list and the investigators are somewhat close,
            # it is "too close", so Jack should use a coach card.
            # TODO - add some random variability to the threshold?  
            #        or maybe if the number of clues found is over X _and_ the average is < Y
            #        or maybe if the running average is < X over Y turns?
            if ((closest < 1 and on_clue) or average < 0.5) or (len(self.targets) == 1 and average < 1.5) or (num_very_close >= 2 and free_edge_count < num_very_close):
                ret = True
        return ret

    # Choose the path when Jack has decided he needs to use a coach
    def pick_a_coach_path(self):
        # compute shortest path without any poisoned paths since Jack can move through investigators using a coach
        # but... Jack cannot take a boat at the same time, so poison the water routes
        
        self.set_travel_weight(BOAT_MOVE, POISON)
        self.set_travel_weight(ALLEY_MOVE, POISON)
        
        # decide on a path
        deterrents = DETERRENT_WEIGHTS
        for deterrent in deterrents:
            v1 = gt.find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
            v2 = gt.find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0]

            self.discourage_investigators2(deterrent)
            vlist = gt.random_shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
            self.discourage_investigators2(-deterrent)
            
            # Compute the cost of this chosen path.  Easiest to just count the entries that aren't crossing
            cost = sum(1 for entry in vlist if 'c' not in self.graph.vp.ids[entry]) - 1
            self.godmode_print("   Considering coach cost: ", cost)
            
            # TODO: Make sure Jack doesn't choose a path 2 away from the goal as that is against the rules
            # NOTE: we currently enforce this rule elsewhere in the code in move().
                
            if (cost <= (16 - self.turn_count())):
                self.godmode_print("   Jack finds this coach cost acceptable.")
                break;
        
        # Restore the weights if Jack still has cards for the move type
        if (len(self.boat_cards) < 2):
            self.set_travel_weight(BOAT_MOVE, DEFAULT_WATER_WEIGHT)
        if (len(self.alley_cards) < 2):
            self.set_travel_weight(ALLEY_MOVE, DEFAULT_ALLEY_WEIGHT)
        return vlist

    def normal_move_possible(self, src, dest):
        ret = False
        self.poison_investigators(POISON)
        self.set_travel_weight(BOAT_MOVE, POISON)
        self.set_travel_weight(ALLEY_MOVE, POISON)
        
        v1 = gt.find_vertex(self.graph, self.graph.vp.ids, src)[0]
        v2 = gt.find_vertex(self.graph, self.graph.vp.ids, dest)[0]
        path_weight = gt.shortest_distance(self.graph, v1, v2, weights=self.graph.ep.weight)
        self.godmode_print("      Alley thoughts: count to get to ", dest, "is", path_weight)
        if (path_weight == 1):
            ret = True

        self.poison_investigators(-POISON)            
        # Restore the weights if Jack still has cards for the move type
        if (len(self.boat_cards) < 2):
            self.set_travel_weight(BOAT_MOVE, DEFAULT_WATER_WEIGHT)
        if (len(self.alley_cards) < 2):
            self.set_travel_weight(ALLEY_MOVE, DEFAULT_ALLEY_WEIGHT)
        
        return ret
        
    def pick_a_path_helper(self, deterrent):
        move_type = NORMAL_MOVE

        # Poison the position of the investigators (i.e. add weights)
        # TODO: if getting close to the end of the round and still have coach cards, maybe don't poison inspector paths and if one is chosen, use a coach?
        self.poison_investigators(POISON)
        self.discourage_investigators2(deterrent)
        self.consider_desperate_weights(True)

        v1 = gt.find_vertex(self.graph, self.graph.vp.ids, self.pos)[0]
        
        # Consider all the targets and return the easiest to reach
        shortest_path = 1000000
        for target in self.targets:
            v2 = gt.find_vertex(self.graph, self.graph.vp.ids, target)[0]
            path_weight = gt.shortest_distance(self.graph, v1, v2, weights=self.graph.ep.weight)
            self.godmode_print("   Weight to get to ", target, " is ", path_weight)
            if (path_weight < shortest_path):
                self.active_target = target
                shortest_path = path_weight
        
        v2 = gt.find_vertex(self.graph, self.graph.vp.ids, self.active_target)[0]
        vlist = gt.random_shortest_path(self.graph, v1, v2, weights=self.graph.ep.weight)
        self.godmode_print("Considering: ", [self.graph.vp.ids[v] for v in vlist])
        
        # Detect when surrounded (i.e shortest path to the next vertex is > 1000) and 
        # determine if any move is possible or if Jack is trapped and loses.
        next_dist = gt.shortest_distance(self.graph, v1, vlist[1], weights=self.graph.ep.weight)
        self.godmode_print("   Next dist is:", next_dist)
        if next_dist >= POISON:
            if (len(self.coach_cards) < 2 and self.turn_count() < 13):
                # do coach move
                self.godmode_print("Must use a coach!")
                move_type = COACH_MOVE
            else:
                self.print("Jack cannot move.  You win!")
                self.print("Jack's current position: ", self.pos)
                self.game_in_progress = False

        # un-poison the ipos edges
        self.poison_investigators(-POISON)
        self.discourage_investigators2(-deterrent)
        self.consider_desperate_weights(False)
    
        # Compute the cost of this chosen path.  Easiest to just count the entries that aren't crossing
        cost = sum(1 for entry in vlist if 'c' not in self.graph.vp.ids[entry]) - 1
        self.godmode_print("    Cost: ", cost)

        # If we didn't decide we have to take a coach, figure out if it was a boat or alley move, based on the next vertex in the path
        if move_type != COACH_MOVE:
            # Going from a water space to another water space - must be using a boat
            if ((self.pos in water) and (self.graph.vp.ids[vlist[1]] in water)):
                move_type = BOAT_MOVE
        
            # Jack didn't pass through any crossings - must be using an alley
            elif 'c' not in self.graph.vp.ids[vlist[1]]:
                # Confirm Jack couldn't have gotten there in 1 turn using a normal move.
                # If he could, don't waste an alley card
                if not self.normal_move_possible(self.pos, self.graph.vp.ids[vlist[1]]):
                    move_type = ALLEY_MOVE
                else:
                    self.godmode_print("Hmmm...   Jack thought to use an alley, but he can just walk there.")
                    self.godmode_print("   Randomly decide.")
                    # Randomly decide to use it so not totally predictable where he went when he uses an alley card.
                    if random.randint(1, 100) < 18:
                        move_type = ALLEY_MOVE
    
        return [vlist, cost, move_type]
        
    
    def pick_a_path(self, deterrent):        
        path_ok = False
        alleys_poison = False
        
        # Need to loop in case an alley was chosen for the final target.
        while(not path_ok):
            vlist, cost, move_type = self.pick_a_path_helper(deterrent)
            
            # Check to make sure we are using an alley to get to the target, as that isn't allow per the rules
            if (move_type == ALLEY_MOVE) and (self.graph.vp.ids[vlist[1]] == self.active_target):
                self.godmode_print("Oops! Jack tried to use an alley to get to the goal.  That is not allowed.")
                self.godmode_print("Recalculating...")
                
                # Make so Jack won't consider an alley
                self.set_travel_weight(ALLEY_MOVE, POISON)
                alleys_poison = True
            else: 
                path_ok = True
                if (alleys_poison):
                    if (len(self.alley_cards) < 2):
                        self.set_travel_weight(ALLEY_MOVE, DEFAULT_ALLEY_WEIGHT)
                    alleys_poison = False
        
        return [vlist, cost, move_type]
        
    def move(self):
        if (not self.game_in_progress):
            self.print("No game in progress, please \033[1mstart\033[0m a game before trying to move Jack.")
            return
        
        # Per the rules, Jack does not announce he has reached his target until AFTER the investigators take their turn.
        # For this reason, we perform this check here before his next move.
        if self.pos == self.active_target:
            self.print("A crime has been discovered at \033[1m" + self.pos + "\033[0m and Jack has moved on.")
            if (len(self.path_used) > 0):
                # TODO: this isn't really part of the rules, but might be helpful during play
                self.print("Here is the path he took:", self.path_used)
            self.crimes.append(self.pos)
            self.path_used = [self.pos]
            self.targets.remove(self.pos)
            self.clues = []
            if self.output_func != None:
                self.output_func(NEW_ROUND_MSG, None)

        if (len(self.targets) == 0):
            self.print("Game over!  Jack won!")
            self.print("    Crime locations: ", self.crimes)
            self.make_image()
            self.game_in_progress = False
            return
        
        # Each turn reconsider what is the best target to try
        # Do this before poisoning the routes
        # NOTE: pick_a_path() does this now (as an experimental test)
        #self.choose_closest_target()
        
        # decide on a path
        deterrents = DETERRENT_WEIGHTS
        for deterrent in deterrents:
            vlist, cost, move_type = self.pick_a_path(deterrent)
            if not self.game_in_progress:
                return
            if (cost <= ((16 - TURN_BUFFER) - self.turn_count())):
                self.godmode_print("   Jack finds this cost acceptable.")
                break;
        
        # Have you considered the advantages to taking a COACH?
        # Check if we are only moving 2 or less (either via normal move (which must be 1) or special card)
        if (move_type != COACH_MOVE) and (self.hop_count(self.pos, self.graph.vp.ids[vlist[1]], boats_reduced=False) <= 2):
            # If we are one space away from the goal, don't use a coach, otherwise, think about it.
            if (self.hop_count(self.pos, self.active_target) != 1):
                if self.consider_coach_move():
                    move_type = COACH_MOVE
        
        # If a water path was selected, spend the card
        if move_type == BOAT_MOVE:
            self.print("Jack took a boat on turn %d!" % len(self.path_used))
            self.boat_cards.append(self.turn_count())
            self.notify_gui_of_special_travel(BOAT_MOVE)
            
            if (len(self.boat_cards)>= 2):
                # poison all the water paths - Jack has no boat cards left
                self.set_travel_weight(BOAT_MOVE, POISON)

        # If a alley path was selected, spend the card
        elif move_type == ALLEY_MOVE:
            self.print("Jack snuck through an alley on turn %d!" % len(self.path_used))
            self.alley_cards.append(self.turn_count())
            self.notify_gui_of_special_travel(ALLEY_MOVE)
            
            if (len(self.alley_cards)>= 2):
                # poison all the alley paths - Jack has no alley cards left
                self.godmode_print("Poisoning alleys so they can no longer be used.")
                self.set_travel_weight(ALLEY_MOVE, POISON)
        
        # If we decide we should use a coach, revise the path since we can move through investigators
        if (move_type == COACH_MOVE):
            vlist = self.pick_a_coach_path()
            self.notify_gui_of_special_travel(COACH_MOVE)
            self.godmode_print("\033[1mChoosing this for a coach path:\033[0m")
            self.godmode_print([self.graph.vp.ids[v] for v in vlist])
        
        self.pos = self.find_next_location(vlist)
        self.path_used.append(self.pos)

        # Count how far away the goal is now that Jack moved
        shortest = self.hop_count(self.pos, self.active_target)
        
        # If Jack is doing a coach move, he moves a second time.
        # Since we aready computed the shortest path above, just go to the next location in that path, but make sure it isn't a goal.
        if (move_type == COACH_MOVE):
            self.print("Jack takes a coach!")
            self.coach_cards.append(self.turn_count()-1)
            self.godmode_print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")
            
            if (shortest > 1):
                self.pos = self.find_second_location(vlist)
            else:
                # make sure we don't use a coach to get to the goal - pick another location 1 space away
                self.pos = self.find_adjacent_nongoal_vertex(self.path_used[-2])
                
                if self.pos == "NULL":
                    # I _think_ this case is impossible based on the map layout, but just in case....
                    self.print("Jack \033[1mLOSES\033[0m!")
                    self.print("Jack tried to use a coach, but his goal was 2 spaces away and according to the rules a coach cannot be used for going directly to his goal.")
                    self.print("Jack tried to find another location 1 space away, but there was no other legal place to move, so he is trapped.")
                    self.print("Jack was at location " + prior_location + " and is currently at " + self.pos)
                    self.print("Here is the full path he took:", self.path_used)
                    return
            self.path_used.append(self.pos)
            
            # Count how far away the goal is now that Jack moved
            shortest = self.hop_count(self.pos, self.active_target)
        
        self.godmode_print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")

        self.print("Jack has \033[1m", 16 - self.turn_count(), "\033[0m moves remaining.")

        # If shortest path is longer than remaining turns
        if (16 - self.turn_count() < shortest):
            self.print("Jack LOSES!  He cannot reach his target with the number of moves left.")
            self.print("Here is the path he took:", self.path_used)
            return
        self.make_image()

    def clue_search(self, pos_list):
        #TODO: verify clue location is next to an ipos?  Or just have players enforce the rules themselves.
        self.print("\nSearching for clues at: ", pos_list)
        for loc in pos_list:
            if loc in self.path_used:
                self.print("Clue found at \033[1m", loc, "\033[0m!!")
                self.clues.append(loc)
                self.make_image()
                break
            else:
                self.print(loc, ": no clue")

    def arrest(self, pos):
        #TODO: verify arrest location is next to an ipos?  Or just have players enforce the rules themselves.
        if pos == self.pos:
            self.print("Congratulations!  You \033[1marrested\033[0m Jack at location ", pos, "!")
            self.print("Here is the path he took:", self.path_used)
            self.game_in_progress = False
        else:
            self.print("Jack is not at location ", pos)

'''
    def find_next_ilocation(self, vlist, id_list):
        index = 1
        while (index < len(vlist)-1) and 'c' not in id_list[vlist[index]]:
            index=index+1
    
        # Don't move the inspector onto a destination
        if 'c' not in id_list[vlist[index]]:
            index = 0

        return id_list[vlist[index]]

    # Let investigators always move towards Jack to test Jack's algorithm
    def move_investigators(g, ipos, jack_pos):
        for num in range (0, 3):
            v1 = gt.find_vertex(g, g.vp.ids, ipos[num])[0]
            v2 = gt.find_vertex(g, g.vp.ids, jack_pos)[0]
            vlist, elist = shortest_path(g, v1, v2)
            #print([g.vp.ids[v] for v in vlist])
        
            pos = find_next_ilocation(vlist, g.vp.ids)
            ipos[num]=pos
            print("Inspector #" + str(num) + " moved to " + pos +" and is now " + 
                str(gt.shortest_distance(g, gt.find_vertex(g, g.vp.ids, pos)[0], v2)) + " distance")
'''            
        
        