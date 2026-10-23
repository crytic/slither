from slither.core.expressions.unary_operation import UnaryOperation, UnaryOperationType
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.visitors.expression.expression import ExpressionVisitor


class RemoveNegationVisitor(ExpressionVisitor):
    def __init__(self, expression, mutator, result):
        self._mutator = mutator
        self._result = result

        # Traverse the expression AST
        super().__init__(expression)

    def _post_unary_operation(self, expression: UnaryOperation):
        # Mutate only logical negation (!)
        if expression.type != UnaryOperationType.BANG:
            return

        if not expression.source_mapping:
            return

        operand = expression.expression

        # Replace '!expr' with 'expr'
        create_patch_with_line(
            self._result,
            self._mutator.in_file,
            expression.source_mapping.start,
            expression.source_mapping.start + expression.source_mapping.length,
            expression.source_mapping.content,
            operand.source_mapping.content,
            expression.source_mapping.lines[0],
        )


class RNM(AbstractMutator):
    NAME = "RNM"
    HELP = "Remove Negation"

    def _mutate(self) -> dict:
        result = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue

            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue

                expression = getattr(node, "expression", None)
                if expression is None:
                    continue

                RemoveNegationVisitor(expression, self, result)

        return result
