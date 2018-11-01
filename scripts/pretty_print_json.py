#!/usr/bin/python3

import sys
import json

raw_json_file = sys.argv[1]
pretty_json_file = sys.argv[2]

with open(raw_json_file, 'r') as json_data:
    with open(pretty_json_file, 'w') as out_file:
        out_file.write(json.dumps(json.load(json_data), sort_keys=True, indent=4))