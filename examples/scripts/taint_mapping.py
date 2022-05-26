import sys

from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable
from slither.slither import Slither
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.index import Index
from slither.slithir.variables.reference import ReferenceVariable
from slither.slithir.variables.temporary import TemporaryVariable


def visit_node(node, visited):
    if node in visited:
        return

    visited += [node]
    taints = node.function.compilation_unit.context[KEY]

    refs = {}
    for ir in node.irs:
        if isinstance(ir, Index):
            refs[ir.lvalue] = ir.variable_left

        if isinstance(ir, Index):
            read = [ir.variable_left]
        else:
            read = ir.read
        print(ir)
        print(f"Refs {refs}")
        print(f"Read {[str(x) for x in ir.read]}")
        print(f"Before {[str(x) for x in taints]}")
        if any(var_read in taints for var_read in read):
            taints += [ir.lvalue]
            lvalue = ir.lvalue
            while isinstance(lvalue, ReferenceVariable):
                taints += [refs[lvalue]]
                lvalue = refs[lvalue]

        print(f"After {[str(x) for x in taints]}")
        print()

    taints = [v for v in taints if not isinstance(v, (TemporaryVariable, ReferenceVariable))]

    node.function.compilation_unit.context[KEY] = list(set(taints))

    for son in node.sons:
        visit_node(son, visited)


def check_call(func, taints):
    for node in func.nodes:
        for ir in node.irs:
            if isinstance(ir, HighLevelCall):
                if ir.destination in taints:
                    print(f"Call to tainted address found in {function.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("python taint_mapping.py taint.sol")
        sys.exit(-1)

    # Init slither
    slither = Slither(sys.argv[1])

    initial_taint = [SolidityVariableComposed("msg.sender")]
    initial_taint += [SolidityVariableComposed("msg.value")]

    KEY = "TAINT"

    prev_taints = []
    slither.context[KEY] = initial_taint
    while set(prev_taints) != set(slither.context[KEY]):
        prev_taints = slither.context[KEY]
        for contract in slither.contracts:
            for function in contract.functions:
                print(f"Function {function.name}")
                slither.context[KEY] = list(set(slither.context[KEY] + function.parameters))
                visit_node(function.entry_point, [])
                print(f"All variables tainted : {[str(v) for v in slither.context[KEY]]}")

            for function in contract.functions:
                check_call(function, slither.context[KEY])

    print(
        f"All state variables tainted : {[str(v) for v in prev_taints if isinstance(v, StateVariable)]}"
    )
