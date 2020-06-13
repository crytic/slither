from typing import List


def unroll(list_to_unroll: List) -> List:
    ret = []
    for x in list_to_unroll:
        if not isinstance(x, list):
            ret += [x]
        else:
            ret += unroll(x)
    return ret
