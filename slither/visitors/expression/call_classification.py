from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from slither.core.declarations import Contract
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.member_access import MemberAccess
from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.utils.using_for import USING_FOR

ExternalIdentifierPredicate = Callable[[Identifier], bool]


def _is_using_for_library_call(
    variable: Variable,
    member_name: str,
    using_for: USING_FOR,
) -> bool:
    """Return True when *member_name* resolves to a library function
    attached to *variable*'s type via a ``using … for`` directive.
    """
    from slither.core.solidity_types.user_defined_type import (
        UserDefinedType,
    )

    var_type = variable.type
    if var_type is None:
        return False

    # Collect candidate library entries for the variable's type.
    # Keys can be Type objects, the "*" wildcard, or string representations.
    candidates = []
    for key, items in using_for.items():
        if key == "*" or key == var_type or str(key) == str(var_type):
            candidates.extend(items)

    for item in candidates:
        # ``using LibContract for SomeType`` → item is UserDefinedType
        if isinstance(item, UserDefinedType):
            lib = item.type
            if isinstance(lib, Contract) and lib.is_library:
                if any(f.name == member_name for f in lib.functions):
                    return True
        # ``using {freeFunc} for SomeType`` → item is Function
        if hasattr(item, "name") and item.name == member_name:
            return True

    return False


def classify_calls(
    calls: list[CallExpression],
    is_external_identifier: ExternalIdentifierPredicate | None = None,
    using_for: USING_FOR | None = None,
) -> tuple[list[CallExpression], list[CallExpression]]:
    """
    Classify call expressions into internal and external calls.

    External calls are calls to external contracts (e.g., token.transfer()).
    Internal calls include:
    - Direct function calls (e.g., myFunc())
    - Solidity built-in calls (e.g., abi.encode(), abi.decode())
    - Library calls (e.g., SafeMath.add(), or addr.sendValue() via using-for)

    Args:
        calls: List of CallExpression to classify
        is_external_identifier: Optional predicate to mark Identifier calls
            as external
        using_for: Optional mapping from ``contract.using_for_complete``
            used to recognise ``using Library for Type`` calls as internal

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
                # Note: "this" is a SolidityVariable but this.foo() is
                # an external call
                if (
                    isinstance(base_value, SolidityVariable)
                    and base_value.name != "this"
                ):
                    internal_calls.append(call)
                # Library calls (e.g., SafeMath.add())
                elif isinstance(base_value, Contract) and base_value.is_library:
                    internal_calls.append(call)
                # using-for library calls (e.g., addr.sendValue())
                elif (
                    using_for
                    and isinstance(base_value, Variable)
                    and _is_using_for_library_call(
                        base_value, called.member_name, using_for
                    )
                ):
                    internal_calls.append(call)
                else:
                    external_calls.append(call)
            else:
                external_calls.append(call)
            continue

        # Other cases (e.g., complex expressions) — treat as external
        external_calls.append(call)

    return internal_calls, external_calls
