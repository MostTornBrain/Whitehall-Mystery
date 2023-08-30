* Show special moves on the turn track
* Alley usage doesn't seem quite right - Jack uses it when a normal move would have gotten to the same location
* Randomly choose (50/50?) whether to use coach when investigator is adjacent to Jack and Jack is on a known clue? 
* Gomode mode output logged to a file when playing normally, for later debugging?
* Add difficuly mode - influences what positions Jack chooses, based average distance between targets?  The further apart the harder (from Jack's point of view)?  
* Enforce ipos, clues?
* Separate commands for each investigator?  I.e.  `y <pos>`,  `b <pos>`, `r <pos>`?
* Only poison paths if investigator is within X spaces of Jack?   Why block a path if Jack can't even reach it yet.
* Don't poison water paths based on nearby investigators
* When in "panic mode" (i.e investigators are too close) if there is a location that is not reachable by the investigators in one turn, move there?
