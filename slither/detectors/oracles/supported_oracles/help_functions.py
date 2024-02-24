from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations import InternalCall
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.constant import Constant

# Helpfull functions

# Check if the node's sons contain a revert statement
def check_revert(node: Node) -> bool:
    for n in node.sons:
        if n.type == NodeType.EXPRESSION:
            for ir in n.irs:
                if isinstance(ir, SolidityCall):
                    if "revert" in ir.function.name:
                        return True
    return False


def is_boolean(ir) -> bool:
    for val in ir.values:
        if isinstance(val, Constant):
            if isinstance(val.value, bool):
                return True
    return False

# Check if the node's sons contain a return statement
def return_boolean(node: Node) -> bool:
    for n in node.sons:
        if n.type == NodeType.RETURN:
            for ir in n.irs:
                if isinstance(ir, Return):
                    return is_boolean(ir)
    return False


# Check if the node is an internal call
def is_internal_call(node) -> bool:
    for ir in node.irs:
        if isinstance(ir, InternalCall):
            return True
    return False
