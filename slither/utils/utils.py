def unroll(l):
    ret = []
    for x in l:
        if not isinstance(x, list):
            ret += [x]
        else:
            ret += unroll(x)
    return ret
