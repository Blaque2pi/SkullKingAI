import json, time
from collections import defaultdict


def complex_merge_to_dict(dicts):
    parsed_dicts = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # default to [score, count]
    dict_num = 0
    # Step through each dictionary in the list
    for d in dicts:
        dict_num += 1
        for key, val_dict in d.items():
            # Parse the JSON key to a Python dict
            parsed_key = json.dumps(json.loads(key), sort_keys=True)

            # Merge the dictionaries based on parsed_key
            for action, score in val_dict.items():
                existing_score, count = parsed_dicts[parsed_key][action]

                if score == 0 and existing_score != 0:
                    continue  # Skip if new score is zero and there is already a non-zero score
                elif existing_score == 0:
                    parsed_dicts[parsed_key][action] = [score, 1]  # Replace zero score
                else:
                    # Calculate the new average if both scores are non-zero
                    new_average = (existing_score * count + score) / (count + 1)
                    parsed_dicts[parsed_key][action] = [new_average, count + 1]
        print(f'Table {dict_num} incorporated')
    # Prepare the final single dictionary output
    final_dict = {key: {action: score[0] for action, score in val_dict.items()}
                  for key, val_dict in parsed_dicts.items()}

    return final_dict


dicts = []

# Load JSON data
for i in range(1, 21):
    print(f"Loading table {i}")
    table_name = f'table{i}'
    with open(f'{table_name}.json', 'r') as file:
        dicts.append(json.load(file))

print("Starting merge...")
start_time = time.perf_counter()
merged_dicts = complex_merge_to_dict(dicts)

# Save the merged dictionary
with open(f'combined.json', 'w') as file:
    json.dump(merged_dicts, file, indent=4)

end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Merge complete after {elapsed_time} seconds.")
