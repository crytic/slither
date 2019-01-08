"""
    Compute the data depenency between all the SSA variables
"""
from slither.slithir.operations import Index, Member, OperationWithLValue
from slither.slithir.variables import ReferenceVariable, Constant
from slither.slithir.variables import (Constant, LocalIRVariable, StateIRVariable,
                                       ReferenceVariable, TemporaryVariable,
                                       TupleVariable)

KEY = "DATA_DEPENDENCY_SSA"
KEY_NON_SSA = "DATA_DEPENDENCY"

def compute_dependency(slither):
    for contract in slither.contracts:
        compute_dependency_contract(contract)

def compute_dependency_contract(contract):
    if KEY in contract.context:
        return

    contract.context[KEY] = dict()
    for function in contract.all_functions_called:
        compute_dependency_function(function)
        data_depencencies = function.context[KEY]
 
        for (key, values) in data_depencencies.items():
            if not key in contract.context[KEY]:
                contract.context[KEY][key] = set(values)
            else:
                contract.context[KEY][key].union(values)

    # transitive closure
    changed = True
    while changed:
        changed = False
        # Need to create new set() as its changed during iteration
        data_depencencies = {k: set([v for v in values]) for k, values in  contract.context[KEY].items()}
        for key, items in data_depencencies.items():
            for item in items:
                if item in data_depencencies:
                    additional_items = contract.context[KEY][item]
                    for additional_item in additional_items:
                        if not additional_item in items and additional_item != key:
                            changed = True
                            contract.context[KEY][key].add(additional_item)


    contract.context[KEY_NON_SSA] = convert_to_non_ssa(contract.context[KEY])



def compute_dependency_function(function):
    if KEY in function.context:
        return function.context[KEY]

    function.context[KEY] = dict()
    for node in function.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, OperationWithLValue) and ir.lvalue:
                lvalue = ir.lvalue
               # if isinstance(ir.lvalue, ReferenceVariable):
               #     lvalue = lvalue.points_to_origin
               #     # TODO fix incorrect points_to for BALANCE
               #     if not lvalue:
               #         continue
                if not lvalue in function.context[KEY]:
                    function.context[KEY][lvalue] = set()
                if isinstance(ir, Index):
                    read = [ir.variable_left]
                else:
                    read = ir.read
                [function.context[KEY][lvalue].add(v) for v in read if not isinstance(v, Constant)]

    function.context[KEY_NON_SSA] = convert_to_non_ssa(function.context[KEY])

def valid_non_ssa(v):
    if isinstance(v, (TemporaryVariable,
                      ReferenceVariable,
                      TupleVariable)):
        return False
    return True

def convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable)):
        if isinstance(v, LocalIRVariable):
            function = v.function
            return function.get_local_variable_from_name(v.name)
        else:
            contract = v.contract
            return contract.get_state_variable_from_name(v.name)
    return v

def convert_to_non_ssa(data_depencies):
    # Need to create new set() as its changed during iteration
    ret = dict()
    for (k, values) in data_depencies.items():
        if not valid_non_ssa(k):
            continue
        var = convert_variable_to_non_ssa(k)
        if not var in ret:
            ret[var] = set()
        ret[var] = ret[var].union(set([convert_variable_to_non_ssa(v) for v in
                                       values if valid_non_ssa(v)]))

    return ret
