from __future__ import annotations

from collections.abc import Callable

from slither.core.declarations import Contract
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.member_access import MemberAccess

ExternalIdentifierPredicate = Callable[[Identifier], bool]


def classify_calls(
    calls: list[CallExpression],
    is_external_identifier: ExternalIdentifierPredicate | None = None,
) -> tuple[list[CallExpression], list[CallExpression]]:
    """
    Classify call expressions into internal and external calls.

    External calls are calls to external contracts (e.g., token.transfer()).
    Internal calls include:
    - Direct function calls (e.g., myFunc())
    - Solidity built-in calls (e.g., abi.encode(), abi.decode())
    - Library calls (e.g., SafeMath.add())

    Args:
        calls: List of CallExpression to classify
        is_external_identifier: Optional predicate to mark Identifier calls as external

    Returns:
        Tuple of (internal_calls, external_calls)
    """
    internal_calls: list[CallExpression] = []
    external_calls: list[CallExpression] = []

    for call in calls:
        called = call.called

        if isinstance(called, Identifier):
            if is_external_identifier and is_external_identifier(called):
                external_calls.append(call)
            else:
                internal_calls.append(call)
            continue

        if isinstance(called, MemberAccess):
            base_expr = called.expression

            if isinstance(base_expr, Identifier):
                base_value = base_expr.value

                # Solidity built-ins (abi, msg, block, tx, etc.)
                # Note: "this" is a SolidityVariable but this.foo() is an external call
                if isinstance(base_value, SolidityVariable) and base_value.name != "this":
                    internal_calls.append(call)
                # Library calls
                elif isinstance(base_value, Contract) and base_value.is_library:
                    internal_calls.append(call)
                else:
                    external_calls.append(call)
            else:
                external_calls.append(call)
            continue

        # Other cases (e.g., complex expressions) - treat as external to be safe
        external_calls.append(call)

    return internal_calls, external_calls
