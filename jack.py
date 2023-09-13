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
from graph_data import *
import random

# How many extra turns should Jack leave as "buffer" for completing his path
TURN_BUFFER = 3
DEFAULT_WATER_WEIGHT = 1  # Experimental: Using safety weights, treat water like any other path as it will have a high weight due to there only being 1 exit at each end.
DEFAULT_ALLEY_WEIGHT = 13
DETERRENT_WEIGHTS = [6, 3, 1, 0]

# This difficulty rating is from JACK's point of view, not the players'
EASY_BUCKET = 0
HARD_BUCKET = 1

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
    for node in ug.nodes():
        ug.nodes[node]['color'] = "#000000"
    
        if 'c' in node:
            ug.nodes[node]['shape'] = "square"
            ug.nodes[node]['size'] = 12*scale
            ug.nodes[node]['fsize'] = 0*scale   # Don't want crossing labels
        else:
            ug.nodes[node]['shape'] = "circle"
            ug.nodes[node]['size'] = 18*scale
            ug.nodes[node]['fsize'] = 10*scale

    # Color ispector starting positions yellow
    for node in starting_ipos:
        # TODO: maybe insert another unconnected node here and make it slightly bigger to get the yellow frame?
        ug.nodes[node]['color'] = STARTING_CROSSINGS_COLOR

    # Color all the destinations in the four quadrants white
    for q in quads:
        for num in q:
            ug.nodes[num]['color'] = "#ffffff"

    # Make water destinations blue
    for num in water:
        ug.nodes[num]['color'] = WATER_COLOR

class Jack:
    def __init__(self, g, ipos):
        self.file = open('whitehall.log', 'w')
        self.graph = g
        self.ipos = ipos
        self.godmode = False
        self.win = None
        self.pos = 0
        self.it_is_jacks_turn = False
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
        self.rate_nodes()
        self.rate_quads()
        
        # Experimental - use weighted paths based on how "safe" the location is
        self.weight_for_safety()
        
        # Create a set of weights only used for the point of view of the investigators, 
        # so it omits alley and boat paths and it only weights entering crossings
        
        for u, v in self.graph.edges():
            self.graph.edges[u, v]['i_weight'] = self.graph.edges[u, v]['weight']
            
        for u, v in self.graph.edges():
            if self.graph.edges[u, v]['transport'] == NORMAL_MOVE:
                source = u
                target = v
                if "c" in source and "c" not in target:
                    self.graph.edges[u, v]['i_weight'] = 0
                else:
                    self.graph.edges[u, v]['i_weight'] = 1
            else:
                self.graph.edges[u, v]['i_weight'] = POISON    # Don't use Jack's special paths (boats and alleys)
            
    def node_safety_weight(self, loc):
        weight_adjust = 0
        if loc in self.node_safety:
            safety = self.node_safety[loc]
            weight_adjust = (self.max_safety - safety)/10
        return weight_adjust
        
    def rate_nodes(self):
        self.node_safety = {}
        self.max_safety = 0 
        for loc, (x, y) in positions:
            if 'c' not in loc:
                self.node_safety[loc] = self.location_safety_rating(loc)
                if self.node_safety[loc] > self.max_safety:
                    self.max_safety = self.node_safety[loc]

    def weight_for_safety(self):
        self.set_travel_weight(BOAT_MOVE, DEFAULT_WATER_WEIGHT)
        self.set_travel_weight(ALLEY_MOVE, DEFAULT_ALLEY_WEIGHT)
        
        for u, v in self.graph.edges():
            weight_adjust = self.node_safety_weight(v)
            self.graph.edges[u, v]['safety_weight'] =  weight_adjust + self.graph.edges[u, v]['weight']
            #print ("weighting", u, v, self.graph.edges[u, v]['safety_weight'], " was:", self.graph.edges[u, v]['weight'])

    
    def rate_quads(self):
        self.rated_quads = []

        for q in quads:
            min = 1000
            max = 0
            total = 0 
            count = 0
            
            # First pass: compute the range and average of the quad group
            for t in q:
                rating = self.node_safety[t]
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
                rating = self.node_safety[t]
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
        print(*msg, file=self.file, flush=True)
        
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
        # Trigger the map to refresh in the GUI
        self.gui_refresh()

    def godmode_print(self, *msg):
        if (self.godmode):
            self.print(*msg)
        else:
            self.log_to_file(*msg)

    def pick_the_targets(self, difficulty):
        # Choose the 4 targets for the game
        for q in self.rated_quads:
            self.targets.append(random.choice(q[difficulty]))

    def reset(self):
        self.it_is_jacks_turn = False
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
        
        shortest = nx.shortest_path_length(self.graph, source=src, target=dest, weight='weight')

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
        while 'c' in vlist[index]:
            index=index+1
        return vlist[index]

    # Find the second vertex in the vlist
    def find_second_location(self, vlist):
        index = 1
        while 'c' in vlist[index]:
            index=index+1
        index = index+1   # Skip over the first vertex
        
        if index < len(vlist):
            while 'c' in vlist[index]:
                index=index+1
            ret = vlist[index]
        else:
            # No item left in list, so pick a random neighbor, but it can't be where Jack started nor his goal
            choices = self.locations_one_away(self.pos)
            if self.active_target in choices:
                choices.remove(self.active_target)
            if vlist[0] in choices:
                choices.remove(vlist[0])
            ret = random.choice(choices)
            
        return ret

    def poison_location(self, loc, adjust):
        self.godmode_print("Poisoning: ", loc, adjust)
        for u, v in self.graph.in_edges(loc):
            self.graph.edges[u,v]['safety_weight'] += adjust
            self.graph.edges[u,v]['weight'] += adjust
            
    # Poison all the paths (i.e. edges) that go through an inspector (i.e. ipos) as Jack isn't allowed to use those
    # NOTE: This assumes this called alternatively with a positive then a negative value
    #       It saves the list of poisoned locations, then the next call uses that list for the unpoisoning
    def poison_investigators(self, adjust):
        if not hasattr(self, "is_poison"):
            self.is_poison = []

        if len(self.is_poison) == 0:
            for num in range (0, 3):
                # Only poison if the investigator crossing can be reached by Jack in less than 3 moves
                if self.hop_count(self.ipos[num], self.pos) <= 2:
                    self.is_poison.append(num)
                    self.godmode_print("Investigator #", num, "is poison.")
                    self.poison_location(self.ipos[num], adjust)
                    
            self.godmode_print("Poisoned investigators...", self.is_poison, adjust)
        else:
            self.godmode_print("Unpoisoning investigators...", self.is_poison, adjust)
            for num in self.is_poison:
                self.poison_location(self.ipos[num], adjust)
            self.is_poison = [] # Discard the entries so next time this is called, we start over

    def investigator_distance(self, num):
        # Find the vertex belonging to the `num` ivestigator
        v = self.ipos[num]
        distance = nx.shortest_path_length(self.graph, source=v, target=self.pos, weight='i_weight')
        return distance
    
    # returns a list of crossings <= 2 spaces away
    def investigator_crossing_options(self, num):
        v = self.ipos[num]
        shortest_paths = nx.single_source_dijkstra_path_length(self.graph, v, cutoff=2, weight='i_weight')
        # List nodes within the maximum weighted distance
        return [node for node in shortest_paths.keys() if 'c' in node]
    
    # Discourage Jack from taking paths near investigators by increasing the weights
    def discourage_investigators2(self, adjust):
        for num in range (0, 3):
            distance = self.investigator_distance(num)
            if (adjust > 0):
                self.godmode_print("Investigator#", num, "at", self.ipos[num], "is", distance, "away.")
            if distance <= 4:
                v = self.ipos[num]
                # Follow paths up to 2 spaces away (from the investigator's point of view)
                shortest_paths = nx.single_source_dijkstra_path_length(self.graph, v, cutoff=2, weight='i_weight')
                for v in shortest_paths.keys():
                    # Only discourage edges directly connected to a location.  Otherwise adjacent crossings poison a path too much.  Jack doesn't care about how many crossings he crosses.
                    if "c" not in v:
                        for u, v in self.graph.in_edges(v):
                            self.graph.edges[u,v]['safety_weight'] += adjust
    
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
        #print
        

    def set_travel_weight(self, transport_type, weight):
        #self.godmode_print("set_travel_weight:", transport_type, weight)
        for u, v in self.graph.out_edges():
            if self.graph.edges[u, v]['transport'] == transport_type:
                self.graph.edges[u, v]['weight'] = weight
                self.graph.edges[u, v]['safety_weight'] = weight + self.node_safety_weight(v)
    
    # If Jack is running out of moves,
    # then reduce the weights of alley moves if he still has alley cards
    def consider_desperate_weights(self, enabled):
        return

    def turn_count(self):
        return len(self.path_used)
        

    def free_edge_count(self, pos):
        #calculate the out-degree but don't count boat or alley paths or poisoned paths
        out_degree = 0
        for u, v in self.graph.out_edges(pos):
            if (self.graph.edges[u, v]['transport'] == NORMAL_MOVE) and (self.graph.edges[u, v]['weight'] < POISON):
                out_degree += 1
        return out_degree
    
    # Compute the safety rating of a location - HIGHER is SAFER
    def location_safety_rating(self, pos):
        one_away = len(self.locations_one_away(pos))
        out_degree = self.free_edge_count(pos)
        return one_away * out_degree

    # Return the LOCATIONS (not crossings) exactly 1 space away from `source` assuming Jack's movement
    def locations_one_away(self, source):
        shortest_paths = nx.single_source_dijkstra_path_length(self.graph, source, cutoff=1, weight='weight')
        # List nodes within the maximum weighted distance
        locs = [node for node in shortest_paths.keys() if 'c' not in node]
        locs.remove(source)
        return locs
    
    def find_adjacent_nongoal_vertex(self):
        # Jack is not allowed to move to a target destination using a coach
        # Pick another vertex that is 1 space away and isn't where he was previously, since that is also against the rules
        vertices_with_distance_one = self.locations_one_away(self.active_target)

        self.godmode_print("   removing:", self.pos)
        if self.pos in vertices_with_distance_one:
            vertices_with_distance_one.remove(self.pos)
        self.godmode_print("These are all 1 away from ", self.active_target)
        self.godmode_print(vertices_with_distance_one)
        if (len(vertices_with_distance_one) > 0):
            choice = random.choice(vertices_with_distance_one)
            self.godmode_print("Choosing:", choice)
        else:
            choice = None
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

    def random_shortest_path(self, source, target):
        # Generate all shortest paths between the source and target
        shortest_paths = list(nx.all_shortest_paths(self.graph, source, target, weight='safety_weight'))

        if not shortest_paths:
            return None

        # Choose a random shortest path
        random_path = random.choice(shortest_paths)

        return random_path

    
    # Choose the path when Jack has decided he needs to use a coach
    def pick_a_coach_path(self):
        # compute shortest path without any poisoned paths since Jack can move through investigators using a coach
        # but... Jack cannot take a boat at the same time, so poison the water routes
        
        self.set_travel_weight(BOAT_MOVE, POISON)
        self.set_travel_weight(ALLEY_MOVE, POISON)
        
        # decide on a path
        deterrents = DETERRENT_WEIGHTS
        for deterrent in deterrents:
            v1 = self.pos
            
            # Can't go to the active_target, so pick a random location 1 away from it
            # and poison the active_target so Jack does not travel through it. 
            # (It's not 100% clear in the rules if he could not travel through it as the 
            # intermediate move, but I'll not allow it to be safe.)
            v2 = self.find_adjacent_nongoal_vertex()
            self.poison_location(self.active_target, POISON)

            self.discourage_investigators2(deterrent)
            vlist = self.random_shortest_path(v1, v2)
            self.discourage_investigators2(-deterrent)
            self.poison_location(self.active_target, -POISON)
            
            # Compute the cost of this chosen path.  Easiest to just count the entries that aren't crossing
            cost = sum(1 for entry in vlist if 'c' not in entry) - 1
            self.godmode_print("   Considering coach cost: ", cost)
                            
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
        
        v1 = src
        v2 = dest
        path_weight = nx.shortest_path_length(self.graph, source=v1, target=v2, weight='safety_weight')
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

        v1 = self.pos
        
        # Consider all the targets and return the easiest to reach
        shortest_path = 1000000
        for target in self.targets:
            v2 = target
            try:
                path_weight = nx.shortest_path_length(self.graph, source=v1, target=v2, weight='safety_weight')
            except ValueError as e:
                print("Noooo!")
                for u, v in self.graph.edges():
                    print(u, v, self.graph.edges[u, v]['safety_weight'])
                exit(0)
            self.godmode_print("   Weight to get to ", target, " is ", path_weight)
            if path_weight < 0:
                print("Noooo!")
                for u, v in self.graph.edges():
                    print(u, v, self.graph.edges[u, v]['safety_weight'])
                exit(0)
            if (path_weight < shortest_path):
                self.active_target = target
                shortest_path = path_weight
        
        v2 = self.active_target
        vlist = self.random_shortest_path(v1, v2)
        self.godmode_print("Considering: ", [v for v in vlist])
        
        # Detect when surrounded (i.e shortest path to the next vertex is > 1000) and 
        # determine if any move is possible or if Jack is trapped and loses.
        next_loc = self.find_next_location(vlist)
        next_dist = nx.shortest_path_length(self.graph, source=v1, target=next_loc, weight='safety_weight')
        self.godmode_print("   Next dist is:", next_dist)
        if next_dist >= POISON:
            # If getting to the next location goes through a blocked path, 
            # Jack is either surrounded (and must take a coach) or the goal is 1 away and is blocked, 
            # so he must pick a different place to go
            if next_loc != self.active_target:
                if (len(self.coach_cards) < 2 and self.turn_count() < 13):
                    # do coach move
                    self.godmode_print("Must use a coach!")
                    move_type = COACH_MOVE
                else:
                    self.print("Jack cannot move.  You win!")
                    self.print("Jack's current position: ", self.pos)
                    self.game_in_progress = False
            else:
                try_count = 0
                while (next_dist >= POISON):
                    self.godmode_print("   Ouch! Goal is blocked!")
                    # Trying to reach goal.  Must pick a different spot as the goal is surrounded.
                    candidates = locations_one_away(self.pos)
                    if self.active_target in candidates:
                        candidates.remove(self.active_target)
                    new_loc = random.choice(candidates)
                    self.godmode_print(f"    Let's visit {new_loc} instead.")
                    vlist = self.random_shortest_path(v1, new_loc)
                    next_dist = nx.shortest_path_length(self.graph, source=v1, target=new_loc, weight='safety_weight')
                    self.godmode_print("   Next dist is:", next_dist)
                    try_count += 1
                    
                    # safety valve - I don't think we should ever have this happen....
                    if try_count > 5:
                        self.print("Jack cannot move.  You win!")
                        self.print("Jack's current position: ", self.pos)
                        self.game_in_progress = False
                        break;

        # un-poison the ipos edges
        self.poison_investigators(-POISON)
        self.discourage_investigators2(-deterrent)
    
        # Compute the cost of this chosen path.  Easiest to just count the entries that aren't crossing
        cost = sum(1 for entry in vlist if 'c' not in entry) - 1
        self.godmode_print("    Cost: ", cost)

        # If we didn't decide we have to take a coach, figure out if it was a boat or alley move, based on the next vertex in the path
        if move_type != COACH_MOVE:
            # Going from a water space to another water space - must be using a boat
            if ((self.pos in water) and (vlist[1] in water)):
                move_type = BOAT_MOVE
        
            # Jack didn't pass through any crossings - must be using an alley
            elif 'c' not in vlist[1]:
                # Confirm Jack couldn't have gotten there in 1 turn using a normal move.
                # If he could, don't waste an alley card
                if not self.normal_move_possible(self.pos, vlist[1]):
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
        alley_dest = []
        
        # Need to loop in case an alley was chosen for the final target.
        while(not path_ok):
            vlist, cost, move_type = self.pick_a_path_helper(deterrent)
            # Check to make sure we are not using an alley to get to the target, as that isn't allow per the rules
            if (move_type == ALLEY_MOVE) and (vlist[1] == self.active_target):
                self.godmode_print("Oops! Jack tried to use an alley to get to the goal.  That is not allowed.")
                self.godmode_print("Recalculating...")
                
                # Make so Jack won't consider that specific alley
                self.graph.edges[self.pos, self.active_target]['safety_weight'] = POISON + self.node_safety_weight(self.active_target)
                self.graph.edges[self.pos, self.active_target]['weight'] = POISON
                alleys_poison = True
                # We can potentially get a new target from `pick_a_path_helper()` so we need to save the current poisoned one
                # for later unpoisoning
                alley_dest.append(self.active_target)
            else: 
                path_ok = True
                if (alleys_poison):
                    if (len(self.alley_cards) < 2):
                        for dest in alley_dest:
                            self.graph.edges[self.pos, dest]['safety_weight'] = DEFAULT_ALLEY_WEIGHT + self.node_safety_weight(self.active_target)
                            self.graph.edges[self.pos, dest]['weight'] = POISON
                            self.godmode_print("Unoopsie poisoning", self.graph.edges[self.pos, dest]['safety_weight'])
                    alleys_poison = False
        
        return [vlist, cost, move_type]
        
    def move(self):
        # Jack is taking his turn, so it is no longer his turn. ;-P
        self.it_is_jacks_turn = False
        
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
        if (move_type != COACH_MOVE) and (self.hop_count(self.pos, vlist[1], boats_reduced=False) <= 2):
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
            self.godmode_print([v for v in vlist])
        
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
            
            self.pos = self.find_second_location(vlist)
            self.path_used.append(self.pos)
            
            # Count how far away the goal is now that Jack moved
            shortest = self.hop_count(self.pos, self.active_target)
        
        self.godmode_print("\nJack moves to -> " + self.pos + " and is " + str(shortest) + " away.")

        self.print("Jack has \033[1m", 16 - self.turn_count(), "\033[0m moves remaining.")

        # If shortest path is longer than remaining turns
        if (16 - self.turn_count() < shortest):
            self.print("Jack LOSES!  He cannot reach his target with the number of moves left.")
            self.print("Here is the path he took:", self.path_used)
            self.print("His remaining target goals were:")
            self.print(self.targets)
            return
        self.make_image()

    def is_loc_adjacent(self, loc):
        loc_good = False
        for num in range(0,3):
            if nx.shortest_path_length(self.graph, source=self.ipos[num], target=loc, weight='i_weight') == 0:
                loc_good = True
                break;
        if not loc_good:
            self.print("\033[1m", loc, "\033[0m is not adjacent to any investigator.")
            self.print("Please enter a valid location list.")
        return loc_good
            
    def clue_search(self, pos_list):
        # Set flag to prevent players from moving after they started searching for clues
        self.it_is_jacks_turn = True
        
        for loc in pos_list:
            if loc in self.crimes:
                self.print("\033[1m", loc, "\033[0m is a crime location.  Please enter a valid location list.")
                return;

            # verify clue location is next to an ipos
            if not self.godmode and not self.is_loc_adjacent(loc):
                return
                
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
        # Set flag to prevent players from moving after they performed an arrest
        self.it_is_jacks_turn = True
        
        #verify arrest location is next to an ipos
        if not self.godmode and not self.is_loc_adjacent(pos):
            return
            
        if pos == self.pos:
            self.print("Congratulations!  You \033[1marrested\033[0m Jack at location ", pos, "!")
            self.print("Here is the path he took:", self.path_used)
            self.print("His remaining target goals were:")
            self.print(self.targets)
            self.game_in_progress = False
        else:
            self.print("Jack is not at location ", pos)
        
        