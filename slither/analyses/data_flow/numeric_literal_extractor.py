#!/usr/bin/env python3
"""
Numeric Literal Extractor for Slither
Extracts all numeric literals from Solidity contracts to create set B.
"""

from slither.core.expressions import *
from slither.slithir.operations import *
from typing import Set


class NumericLiteralExtractor:
    """Extracts all numeric literals from a Solidity program."""

    def __init__(self, slither):
        self.slither = slither
        self.numeric_literals: Set[int] = set()

    def extract_all_literals(self) -> Set[int]:
        """Extract all numeric literals and return set B."""
        for contract in self.slither.contracts:
            self._extract_from_contract(contract)
        return self.numeric_literals

    def _extract_from_contract(self, contract):
        """Extract literals from contract."""
        # State variables
        for state_var in contract.state_variables:
            if state_var.expression:
                self._extract_from_expression(state_var.expression)

        # All functions
        for function in contract.functions:
            self._extract_from_function(function)

    def _extract_from_function(self, function):
        """Extract literals from function."""
        # Function parameters with default values
        for param in function.parameters:
            if hasattr(param, "expression") and param.expression:
                self._extract_from_expression(param.expression)

        # Function body via SlithIR
        for node in function.nodes:
            for ir in node.irs:
                self._extract_from_ir(ir)

            # Also check expressions in the node
            if node.expression:
                self._extract_from_expression(node.expression)

    def _extract_from_ir(self, ir):
        """Extract literals from SlithIR operations."""
        if isinstance(ir, Assignment):
            if hasattr(ir.rvalue, "value") and isinstance(ir.rvalue.value, int):
                self.numeric_literals.add(ir.rvalue.value)

        elif isinstance(ir, Binary):
            for operand in [ir.variable_left, ir.variable_right]:
                if hasattr(operand, "value") and isinstance(operand.value, int):
                    self.numeric_literals.add(operand.value)

        elif isinstance(ir, Unary):
            if hasattr(ir.rvalue, "value") and isinstance(ir.rvalue.value, int):
                self.numeric_literals.add(ir.rvalue.value)

        elif isinstance(ir, Index):
            if hasattr(ir.variable_right, "value") and isinstance(ir.variable_right.value, int):
                self.numeric_literals.add(ir.variable_right.value)

        elif (
            isinstance(ir, InternalCall)
            or isinstance(ir, HighLevelCall)
            or isinstance(ir, LowLevelCall)
        ):
            for arg in ir.arguments:
                if hasattr(arg, "value") and isinstance(arg.value, int):
                    self.numeric_literals.add(arg.value)

        elif isinstance(ir, Return):
            for ret_val in ir.values:
                if hasattr(ret_val, "value") and isinstance(ret_val.value, int):
                    self.numeric_literals.add(ret_val.value)

        elif isinstance(ir, Condition):
            if hasattr(ir.value, "value") and isinstance(ir.value.value, int):
                self.numeric_literals.add(ir.value.value)

    def _extract_from_expression(self, expr):
        """Extract literals from AST expressions."""
        if isinstance(expr, Literal):
            if (
                expr.type.name in ["uint", "int"]
                or "uint" in str(expr.type)
                or "int" in str(expr.type)
            ):
                try:
                    value = int(expr.value)
                    self.numeric_literals.add(value)
                except ValueError:
                    pass

        elif isinstance(expr, BinaryOperation):
            self._extract_from_expression(expr.expression_left)
            self._extract_from_expression(expr.expression_right)

        elif isinstance(expr, UnaryOperation):
            self._extract_from_expression(expr.expression)

        elif isinstance(expr, IndexAccess):
            self._extract_from_expression(expr.expression_left)
            if expr.expression_right:
                self._extract_from_expression(expr.expression_right)

        elif isinstance(expr, CallExpression):
            for arg in expr.arguments:
                self._extract_from_expression(arg)

        elif isinstance(expr, ConditionalExpression):
            self._extract_from_expression(expr.condition)
            self._extract_from_expression(expr.then_expression)
            self._extract_from_expression(expr.else_expression)

        elif isinstance(expr, TupleExpression):
            for e in expr.expressions:
                if e:
                    self._extract_from_expression(e)

        elif isinstance(expr, AssignmentOperation):
            self._extract_from_expression(expr.expression_left)
            self._extract_from_expression(expr.expression_right)


def extract_numeric_literals_from_slither(slither):
    """Extract numeric literals from slither object."""
    extractor = NumericLiteralExtractor(slither)
    return extractor.extract_all_literals()


def extract_numeric_literals_with_summary(slither):
    """Extract numeric literals with summary."""
    extractor = NumericLiteralExtractor(slither)
    set_b = extractor.extract_all_literals()
    cardinality = len(set_b)
    print(f"\n=== Numeric Literal Extraction Summary ===")
    print(f"Total unique numeric literals found: {cardinality}")
    print(f"Set B contents: {sorted(set_b)}")
    print(f"==========================================\n")
    return set_b, cardinality
