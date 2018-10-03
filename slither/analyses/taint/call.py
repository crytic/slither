"""
    Compute taint on state call

    use taint on state_variable

    an call ir with a taint set to yes means tainted destination
"""
from slither.analyses.taint.state_variables import get_taint as get_taint_state
from slither.core.declarations.solidity_variables import \
    SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.index import Index
from slither.slithir.operations.low_level_call import LowLevelCall
from slither.slithir.operations.send import Send
from slither.slithir.operations.transfer import Transfer
from slither.slithir.variables.reference import ReferenceVariable

from slither.slithir.operations.member import Member
from slither.slithir.operations.lvalue import OperationWithLValue
KEY = 'TAINT_CALL_DESTINATION'

def _visit_node(node, visited, taints):
    if node in visited:
        return

    visited += [node]

    refs = {}
    for ir in node.irs:
        if isinstance(ir, (Index, Member)):
            refs[ir.lvalue] = ir.variable_left

        if isinstance(ir, Index):
            read = [ir.variable_left]
        else:
            read = ir.read
        if isinstance(ir, OperationWithLValue) and any(var_read in taints for var_read in read):
            taints += [ir.lvalue]
            lvalue = ir.lvalue
            while  isinstance(lvalue, ReferenceVariable):
                taints += [refs[lvalue]]
                lvalue = refs[lvalue]
        if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
            if ir.destination in taints:
                ir.context[KEY] = True

    for son in node.sons:
        _visit_node(son, visited, taints)

def _run_taint(slither, initial_taint):
    if KEY in slither.context:
        return
    for contract in slither.contracts:
        for function in contract.functions:
            if not function.is_implemented:
                continue
            _visit_node(function.entry_point, [], initial_taint + function.parameters)

def run_taint(slither):
    initial_taint = get_taint_state(slither)
    initial_taint += [SolidityVariableComposed('msg.sender')]

    if KEY not in slither.context:
        _run_taint(slither, initial_taint)

