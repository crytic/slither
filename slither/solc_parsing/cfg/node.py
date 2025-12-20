from typing import Union, List, Tuple, TYPE_CHECKING

from slither.core.cfg.node import Node
from slither.core.cfg.node import NodeType
from slither.core.declarations import Contract
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.expressions.assignment_operation import (
    AssignmentOperation,
    AssignmentOperationType,
)
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.member_access import MemberAccess
from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.visitors.expression.find_calls import FindCalls
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar

if TYPE_CHECKING:
    from slither.solc_parsing.declarations.function import FunctionSolc
    from slither.solc_parsing.declarations.modifier import ModifierSolc


def _classify_calls(
    calls: List[CallExpression],
) -> Tuple[List[CallExpression], List[CallExpression]]:
    """
    Classify call expressions into internal and external calls.

    External calls are calls to external contracts (e.g., token.transfer()).
    Internal calls include:
    - Direct function calls (e.g., myFunc())
    - Solidity built-in calls (e.g., abi.encode(), abi.decode())
    - Library calls (e.g., SafeMath.add())

    Args:
        calls: List of CallExpression to classify

    Returns:
        Tuple of (internal_calls, external_calls)
    """
    internal_calls: List[CallExpression] = []
    external_calls: List[CallExpression] = []

    for call in calls:
        called = call.called

        if isinstance(called, Identifier):
            # Direct function call like myFunc() or require()
            # These are internal calls (including Solidity built-ins accessed directly)
            internal_calls.append(call)

        elif isinstance(called, MemberAccess):
            # Member access like x.foo()
            # Need to determine if x is:
            # - A Solidity built-in (abi, msg, block, etc.) -> internal
            # - A library contract -> internal
            # - An external contract/address -> external
            base_expr = called.expression

            if isinstance(base_expr, Identifier):
                base_value = base_expr.value

                # Check if it's a Solidity built-in variable (abi, msg, block, tx, etc.)
                # Note: "this" is a SolidityVariable but this.foo() is an external call
                # (uses CALL opcode), so we exclude it from internal calls
                if isinstance(base_value, SolidityVariable) and base_value.name != "this":
                    internal_calls.append(call)
                # Check if it's a library contract
                elif isinstance(base_value, Contract) and base_value.is_library:
                    internal_calls.append(call)
                else:
                    # External contract call
                    external_calls.append(call)
            else:
                # Complex expression like getContract().foo() - treat as external
                external_calls.append(call)
        else:
            # Other cases (e.g., complex expressions) - treat as external to be safe
            external_calls.append(call)

    return internal_calls, external_calls


class NodeSolc:
    def __init__(self, node: Node) -> None:
        self._unparsed_expression: dict | None = None
        self._node = node

    @property
    def underlying_node(self) -> Node:
        return self._node

    def add_unparsed_expression(self, expression: dict) -> None:
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def analyze_expressions(self, caller_context: Union["FunctionSolc", "ModifierSolc"]) -> None:
        if self._node.type == NodeType.VARIABLE and not self._node.expression:
            self._node.add_expression(self._node.variable_declaration.expression)
        if self._unparsed_expression:
            expression = parse_expression(self._unparsed_expression, caller_context)
            self._node.add_expression(expression)
            # self._unparsed_expression = None

        if self._node.expression:
            if self._node.type == NodeType.VARIABLE:
                # Update the expression to be an assignement to the variable
                _expression = AssignmentOperation(
                    Identifier(self._node.variable_declaration),
                    self._node.expression,
                    AssignmentOperationType.ASSIGN,
                    self._node.variable_declaration.type,
                )
                _expression.set_offset(
                    self._node.expression.source_mapping, self._node.compilation_unit
                )
                self._node.add_expression(_expression, bypass_verif_empty=True)

            expression = self._node.expression
            read_var = ReadVar(expression)
            self._node.variables_read_as_expression = read_var.result()

            write_var = WriteVar(expression)
            self._node.variables_written_as_expression = write_var.result()

            find_call = FindCalls(expression)
            self._node.calls_as_expression = find_call.result()

            # Classify calls into internal and external
            # Internal: direct calls, Solidity built-ins (abi.encode, etc.), library calls
            # External: calls to external contracts
            internal, external = _classify_calls(self._node.calls_as_expression)
            self._node.internal_calls_as_expressions = internal
            self._node.external_calls_as_expressions = external
