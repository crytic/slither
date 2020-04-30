from typing import List


def unroll(l: List):
    ret = []
    for x in l:
        if not isinstance(x, list):
            ret += [x]
        else:
            ret += unroll(x)
    return ret
