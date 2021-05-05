from itertools import count
from slither.tools.middle.framework.tokens import (
    Variable,
    Equals,
    Literal,
    Keyword,
    NewLine,
    CallSite,
    Indent,
)
from slither.core.cfg.node import Node, NodeType

from slither.slithir.operations import (
    Assignment,
    Binary,
    Return,
    Condition,
    Phi,
    InternalCall,
    NewContract,
    HighLevelCall,
    SolidityCall,
)


class OverlayNode:
    node: Node
    type: NodeType
    succ: set
    prev: set
    ir: list

    def __init__(self, node_type: NodeType, node=None):
        # Some nodes may be created and do not have a concrete counterpart
        self.type = node_type
        self.node = node
        self.succ = set()
        self.prev = set()
        counter = count()

        # If the ssa ir is available from the node then use it
        if node is not None:
            self.ir = node.irs_ssa
        else:
            self.ir = []

    def __str__(self):
        if self.node is not None:
            return str(self.node)
        return str(self.type)

    def __copy__(self):
        return OverlayNode(self.type, self.node)

    def get_internal_calls(self):
        return [x for x in self.ir if isinstance(x, InternalCall)]

    def get_all_non_calls(self):
        return [x for x in self.ir if not isinstance(x, InternalCall)]

    def to_tokens(self, func, indentation_level=0):
        token_list = []

        for ir in self.ir:
            if isinstance(ir, Assignment):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                token_list.append(Variable(ir.lvalue, ir, func))
                token_list.append(Equals(ir, func))
                token_list.append(Variable(ir.rvalue, ir, func))
                token_list.append(NewLine(ir, func))
            elif isinstance(ir, Binary):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                token_list.append(Variable(ir.lvalue, ir, func))
                token_list.append(Equals(ir, func))
                token_list.append(Variable(ir.variable_left, ir, func))
                token_list.append(Literal(ir.type_str, ir, func))
                token_list.append(Variable(ir.variable_right, ir, func))
                token_list.append(NewLine(ir, func))
            elif isinstance(ir, Return):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                token_list.append(Keyword("return", ir, func))
                for value in ir.values:
                    token_list.append(Variable(value, ir, func))
                token_list.append(NewLine(ir, func))
            elif isinstance(ir, InternalCall):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                if ir.lvalue is not None:
                    token_list.append(Variable(ir.lvalue, ir, func))
                    token_list.append(Equals(ir, func))
                token_list.append(Keyword("call", ir, func))
                token_list.append(CallSite(ir, func))
                token_list.append(NewLine(ir, func))
            elif isinstance(ir, NewContract):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                if ir.lvalue is not None:
                    token_list.append(Variable(ir.lvalue, ir, func))
                    token_list.append(Equals(ir, func))
                token_list.append(Keyword("new", ir, func))
                token_list.append(Literal(ir.contract_name, ir, func))
                token_list.append(NewLine(ir, func))
            elif isinstance(ir, HighLevelCall):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                if ir.lvalue is not None:
                    token_list.append(Variable(ir.lvalue, ir, func))
                    token_list.append(Equals(ir, func))
                token_list.append(Keyword("ext_call", ir, func))
                token_list.append(CallSite(ir, func))
                token_list.append(NewLine(ir, func))
            elif isinstance(ir, Condition):
                continue
            elif isinstance(ir, Phi):
                continue
            elif isinstance(ir, SolidityCall):
                token_list.extend([Indent(ir, func) for _ in range(indentation_level)])
                if ir.lvalue is not None:
                    token_list.append(Variable(ir.lvalue, ir, func))
                    token_list.append(Equals(ir, func))
                token_list.append(Keyword("sol_call", ir, func))
                token_list.append(CallSite(ir, func))
                token_list.append(NewLine(ir, func))
                continue
            else:
                print("Unhandled type in OverlayNode.to_tokens: {}".format(type(ir)))
        return token_list
