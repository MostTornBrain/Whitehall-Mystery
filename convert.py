#!/Users/brianstormont/opt/anaconda3/bin/python
import re
import sys

# Script to aid in my data entry.  Takes a node to crossing outbound edge definition 
# and creates the corresponding ingress definition with a weight of 1.
# NOTE: this assumes well-formed data and does minium error checking.

# Take input like this:
#    ("68", "68c1", 0, 0), ("68", "68c2", 0, 0), ("68", "68c3", 0, 0),
# And output this:
#        ("68c1", "68", 1, 0), ("68c2", "68", 1, 0), ("68c3", "68", 1, 0), 

# Read the input string from stdin
input_string = sys.stdin.read()

# Remove leading and trailing whitespace
trimmed_input = input_string.strip()

# Use regular expression to find tuples within parentheses
tuples = re.findall(r'\(.*?\)', trimmed_input)

# Loop through each tuple and transform it
transformed_output = ""
for tuple_str in tuples:
    # Remove parentheses and whitespace
    trimmed_tuple = tuple_str.strip('()').strip()

    # Split the tuple into separate values
    values = trimmed_tuple.split(',')

    # Check if the number of values is valid
    if len(values) == 4:
        # Construct the transformed tuple
        transformed_tuple = f'({values[1].strip()}, {values[0].strip()}, 1, {values[2].strip()}), '
        # Append the transformed tuple to the output
        transformed_output += transformed_tuple
    else:
        print("ERROR - malformed edge definition")

# Print the transformed output
print("        " + transformed_output)
