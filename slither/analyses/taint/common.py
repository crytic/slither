from slither.slithir.operations import (Index, Member)

def iterate_over_irs(irs, transfer_func, taints):
    refs = {}
    for ir in irs:
        if isinstance(ir, (Index, Member)):
            refs[ir.lvalue] = ir.variable_left

        if isinstance(ir, Index):
            read = [ir.variable_left]
        else:
            read = ir.read
        taints = transfer_func(ir, read, refs, taints)
    return taints

