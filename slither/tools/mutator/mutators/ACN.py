from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.expressions.call_expression import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.tools.mutator.utils.patch import create_patch_with_line


class ACN(AbstractMutator):
    NAME = "ACN"
    HELP = "Assert Condition Negation"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue

            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue

                try:
                    expression = node.expression
                except AttributeError:
                    continue

                if not isinstance(expression, CallExpression):
                    continue

                if not isinstance(expression.called, Identifier):
                    continue

                called = expression.called.value
                if not isinstance(called, SolidityFunction):
                    continue

                if not called.name.startswith("assert("):
                    continue

                if not expression.arguments:
                    continue

                condition = expression.arguments[0]

                start = condition.source_mapping.start
                stop = start + condition.source_mapping.length
                old_str = condition.source_mapping.content
                line_no = condition.source_mapping.lines[0]
                new_str = f"!({old_str})"

                create_patch_with_line(
                    result,
                    self.in_file,
                    start,
                    stop,
                    old_str,
                    new_str,
                    line_no,
                )

        return result
