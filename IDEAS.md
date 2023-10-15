* When computing a coach path, give a 50/50 chance to not apply deterrent?
* Provide logic to consider backtracking on existing clues?
* Decay the deterrent as it gets farther from the investigator
* Randomly choose (50/50?) whether to use coach when investigator is adjacent to Jack and Jack is on a known clue? 
* Gomode mode output logged to a file when playing normally, for later debugging?
* Add difficuly mode - influences what positions Jack chooses, based average distance between targets?  The further apart the harder (from Jack's point of view)?  Or how well conncected the targets are (or are not).
	* Could also implement the optional rules to help Jack:
		* Murderer at large: only show a special move was used, but not what type.
		* Newspaper Fabrications: Jack can reclaim 1 boat or alley card at the end of the round
* Enforce ipos, clues?
* When in "panic mode" (i.e investigators are too close) if there is a location that is not reachable by the investigators in one turn, move there?
* For the deterrent, only applying it if the investigator is within X moves of Jack causes a noticeable backtrack or oscillation in Jack's moves when an investigater suddenly comes within the deterrent range. Should this be addressed?
* Have a "hide mode" that Jack can be in for X turns where he just tries to get away from the investigators (i.e. try to move to the safest space) (Randomly enter this mode based on how close the investigators are?)
* Should paths along the edge of the map have a higher weight?   The can become a bottleneck for Jack as he has lesss options.
* Add a rule enforcement if not in godmode, then don't allow investigators to move if clue search or arrests have been attempted.  Reset this check after Jack moves.   This prevents players from forgetting to move Jack.
* Only use coach if surrounded or clue discovered in current pos and number of adjacent possible locations is < 3
* Use graph_tool's bfs_iterator() or all_paths() (with a cutoff value) for deterrent rather than wonky recursive method I implemented.  Or maybe use the concept from locations_one_away().
* If Jack is on an "unsafe" space, consider entering "hide mode"?
* Have an alternate set of weights based on the "safety" rating of the vertices
* Have a function to save the weights and to restore the weights rather than applying negative weights and restoring default boat and alley weights after?
* Have a "wild goose" mode Jack can enter if he has a large turn buffer available, we he heads in a random "safe" direction.
* Leave a ghost image of the imvestigator after moving so you know where you started. Have the ghost disappear once clues, arrest, or jack moves.


