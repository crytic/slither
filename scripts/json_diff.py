import sys
import json
from deepdiff import DeepDiff # pip install deepdiff
from pprint import pprint

if len(sys.argv) !=3:
    print('Usage: python json_diff.py 1.json 2.json')
    exit(-1)

with open(sys.argv[1]) as f:
    d1 = json.load(f)

with open(sys.argv[2]) as f:
    d2 = json.load(f)


pprint(DeepDiff(d1, d2, ignore_order=True, verbose_level=2))
