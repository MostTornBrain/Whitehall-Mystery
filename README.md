# WhitehallMystery
Attempt at creating a computer player for Jack for the board game Whitehall Mystery

NOTE: This requires the python [graph-tool](https://graph-tool.skewed.de/static/doc/index.html) library.

Currently this is work-in-progress at the very early stages.  I am currently transcribing the map into a network graph form.

Right now, running `python graph.py` will simply create what exists of the map, render it as a pdf and save it to an external file (for proof-reading so I can hopefully spot issues with my manual process of creating it) and then calculate the shortest path from location 1 to 41 so I can confirm the map is functional.

The main goal is to allow human players to play against a computerized Jack, initially via text entry commands specifying move actions, looking for clues, and performing arrests. More distant goal is to perform moves via graphical interface.


