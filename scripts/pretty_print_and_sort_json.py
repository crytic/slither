#!/usr/bin/python3

'''
the purpose of this file is to sort the json output from the detectors such that
the order is deterministic

- the keys of a json object are sorted
- json objects in a list will be sorted based on the values of their keys

'''

import sys
import json

raw_json_file = sys.argv[1]
pretty_json_file = sys.argv[2]

from collections import OrderedDict

def create_property_val_tuple(d, props_info):
    p_names = props_info[0]
    p_types = props_info[1]
    result = []
    for p in p_names:
        if not p in d: # not all objects have the same keys
            if p_types[p] is 'number':
                result.append(0) # to make sorting work
            if p_types[p] is 'string':
                result.append("") # to make sorting work
        else:
            result.append(d[p])
    return tuple(result)

def get_props_info(list_of_dicts):
    found_props = set()
    prop_types = dict()

    # gather all prop names
    for d in list_of_dicts:
        for p in d:
            found_props.add(p)

    # create a copy, since we are gonna possibly remove props
    shared_props = set(found_props)

    # for each object, loop through list of all found property names,
    # if the object contains that property, check that it's of type string or number
    # if it is, save it's type (used later on for sorting with objects that don't have that property)
    # if it's not of type string/number remove it from list of properties to check
    # since we cannot sort on non-string/number values
    for p in list(found_props):
        if p in shared_props: # short circuit
            for d in list_of_dicts:
                if p in shared_props: # less shorter short circuit
                    if p in d:
                        # we ae only gonna sort key values if they are of type string or number
                        if not isinstance(d[p], str) and not isinstance(d[p], int):
                            shared_props.remove(p)
                        # we need to store the type of the value because not each object
                        # in a list of output objects for 1 detector will have the same
                        # keys, so if we want to sort based on the values then if a certain object
                        # does not have a key which another object does have we are gonna
                        # put in 0 for number and "" for string for that key such that sorting on values
                        # still works
                        elif isinstance(d[p], str):
                            prop_types[p] = 'string'
                        elif isinstance(d[p], int):
                            prop_types[p] = 'number'
    return (list(shared_props), prop_types)

def order_by_prop_value(list_of_dicts):
    props_info = get_props_info(list_of_dicts)
    return sorted(list_of_dicts, key=lambda d: create_property_val_tuple(d, props_info))

def order_list(l):
    # TODO: sometimes slither detectors return a null value in the json output sourceMapping object array
    # get rid of those values, it will break sorting (some items are an object, some are null?!)
    l = list(filter(None, l))
    if not l:
        return []
    if isinstance(l[0], str): # it's a list of string
        return sorted(l)
    elif isinstance(l[0], int): # it's a list of numbers
        return sorted(l)
    elif isinstance(l[0], dict): # it's a list of objects
        ordered_by_key = [order_dict(v) for v in l]
        ordered_by_val = order_by_prop_value(ordered_by_key)
        return ordered_by_val

def order_dict(dictionary):
    result = OrderedDict() # such that we keep the order
    for k, v in sorted(dictionary.items()):
        if isinstance(v, dict):
            result[k] = order_dict(v)
        elif type(v) is list:
            result[k] = order_list(v)
        else: # string/number
            result[k] = v
    return result

with open(raw_json_file, 'r') as json_data:
    with open(pretty_json_file, 'w') as out_file:
        out_file.write(json.dumps(order_list(json.load(json_data)), sort_keys=False, indent=4, separators=(',',': ')))