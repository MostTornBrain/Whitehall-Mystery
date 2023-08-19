# Generate the water paths

import itertools

def print_combinations(numbers, static_data):
    combinations = list(itertools.permutations(numbers, 2))
    for combination in combinations:
        print("   (\"%s\", \"%s\", %d, %d), " % (combination[0], combination[1], static_data[0], static_data[1]))

numbers = ["111", "113", "95", "96", "80"]
static_data = (1, 1)
print_combinations(numbers, static_data)
