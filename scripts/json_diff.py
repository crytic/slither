import sys
import json
from deepdiff import DeepDiff  # pip install deepdiff
from pprint import pprint

if len(sys.argv) != 3:
    print("Usage: python json_diff.py 1.json 2.json")
    exit(-1)

with open(sys.argv[1], encoding="utf8") as f:
    d1 = json.load(f)

with open(sys.argv[2], encoding="utf8") as f:
    d2 = json.load(f)


# Remove description field to allow non deterministic print
for elem in d1:
    if "description" in elem:
        del elem["description"]
for elem in d2:
    if "description" in elem:
        del elem["description"]


def removes_lines(d):
    if isinstance(d, list):
        for sub in d:
            removes_lines(sub)
        return
    if not isinstance(d, dict):
        return
    if "lines" in d:
        del d["lines"]
    for key in d.keys():
        removes_lines(d[key])


results = DeepDiff(d1, d2, ignore_order=True, verbose_level=2)
removes_lines(results)
pprint(results)
