# WhitehallMystery
Attempt at creating a computer player for Jack for the board game Whitehall Mystery

NOTE: This requires the python [graph-tool](https://graph-tool.skewed.de/static/doc/index.html) library.

Currently this is work-in-progress at the very early stages.  I have transcribed the map into di-graph form and Jack is playable. However, Jack does not yet use Alley cards and the Coach card usage still needs to refinement.

A di-graph was needed so a weight can be assigned to ingress edges to a location, but not to outbound edges.  This allows path distance calculation to ignore the cost of crossings, since Jack goes from location to location.  However, it also will allow the graph to be updated with weights in crossings based on the players' positions so when a "best" path is chosen, players can be avoided.   Similarly, weights can be assigned to water crossings and alleys to influence how likely Jack will be to use them.

The main goal is to allow human players to play against a computerized Jack, initially via text entry commands specifying move actions, looking for clues, and performing arrests. More distant goal is to perform moves via graphical interface.

When the program runs, it will generate a PDF of the map.  This will need to be viewed to know the intersection/crossing IDs so they can be entered as the players take their turns.

Type `help` at the prompt to get a list of commands.
