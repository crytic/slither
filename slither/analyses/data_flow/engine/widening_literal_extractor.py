#!/usr/bin/env python3
"""
Numeric Literal Extractor for Slither
Extracts numeric literals specific to functions for widening operations.
"""

from slither.core.expressions import *
from slither.slithir.operations import *
from typing import Set


def extract_numeric_literals_for_function(function) -> tuple[Set[int], int]:
    """Extract numeric literals specific to a function and its accessible state."""
    numeric_literals: Set[int] = set()

    # Extract from function parameters
    for param in function.parameters:
        if hasattr(param, "expression") and param.expression:
            _extract_from_expression(param.expression, numeric_literals)

    # Extract from function body
    for node in function.nodes:
        for ir in node.irs:
            _extract_from_ir(ir, numeric_literals)

        # Also check expressions in the node
        if node.expression:
            _extract_from_expression(node.expression, numeric_literals)

    # Extract from accessible global state variables
    contract = function.contract_declarer
    if contract:
        for state_var in contract.state_variables:
            if state_var.expression:
                _extract_from_expression(state_var.expression, numeric_literals)

    return numeric_literals, len(numeric_literals)


def _extract_from_ir(ir, numeric_literals: Set[int]):
    """Extract literals from SlithIR operations."""
    if isinstance(ir, Assignment):
        if hasattr(ir.rvalue, "value") and isinstance(ir.rvalue.value, int):
            numeric_literals.add(ir.rvalue.value)

    elif isinstance(ir, Binary):
        for operand in [ir.variable_left, ir.variable_right]:
            if hasattr(operand, "value") and isinstance(operand.value, int):
                numeric_literals.add(operand.value)

    elif isinstance(ir, Unary):
        if hasattr(ir.rvalue, "value") and isinstance(ir.rvalue.value, int):
            numeric_literals.add(ir.rvalue.value)

    elif isinstance(ir, Index):
        if hasattr(ir.variable_right, "value") and isinstance(ir.variable_right.value, int):
            numeric_literals.add(ir.variable_right.value)

    elif (
        isinstance(ir, InternalCall)
        or isinstance(ir, HighLevelCall)
        or isinstance(ir, LowLevelCall)
    ):
        for arg in ir.arguments:
            if hasattr(arg, "value") and isinstance(arg.value, int):
                numeric_literals.add(arg.value)

    elif isinstance(ir, Return):
        for ret_val in ir.values:
            if hasattr(ret_val, "value") and isinstance(ret_val.value, int):
                numeric_literals.add(ret_val.value)

    elif isinstance(ir, Condition):
        if hasattr(ir.value, "value") and isinstance(ir.value.value, int):
            numeric_literals.add(ir.value.value)


def _extract_from_expression(expr, numeric_literals: Set[int]):
    """Extract literals from AST expressions recursively."""
    if isinstance(expr, Literal):
        if expr.type.name in ["uint", "int"] or "uint" in str(expr.type) or "int" in str(expr.type):
            try:
                value = int(expr.value)
                numeric_literals.add(value)
            except ValueError:
                pass

    elif isinstance(expr, BinaryOperation):
        _extract_from_expression(expr.expression_left, numeric_literals)
        _extract_from_expression(expr.expression_right, numeric_literals)

    elif isinstance(expr, UnaryOperation):
        _extract_from_expression(expr.expression, numeric_literals)

    elif isinstance(expr, IndexAccess):
        _extract_from_expression(expr.expression_left, numeric_literals)
        if expr.expression_right:
            _extract_from_expression(expr.expression_right, numeric_literals)

    elif isinstance(expr, CallExpression):
        for arg in expr.arguments:
            _extract_from_expression(arg, numeric_literals)

    elif isinstance(expr, ConditionalExpression):
        _extract_from_expression(expr.condition, numeric_literals)
        _extract_from_expression(expr.then_expression, numeric_literals)
        _extract_from_expression(expr.else_expression, numeric_literals)

    elif isinstance(expr, TupleExpression):
        for e in expr.expressions:
            if e:
                _extract_from_expression(e, numeric_literals)

    elif isinstance(expr, AssignmentOperation):
        _extract_from_expression(expr.expression_left, numeric_literals)
        _extract_from_expression(expr.expression_right, numeric_literals)

    elif hasattr(expr, "expressions"):
        for sub_expr in expr.expressions:
            _extract_from_expression(sub_expr, numeric_literals)
