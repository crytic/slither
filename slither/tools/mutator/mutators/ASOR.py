from typing import Dict
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.core.expressions.assignment_operation import (
    AssignmentOperationType,
    AssignmentOperation,
)

assignment_operators = [
    AssignmentOperationType.ASSIGN_ADDITION,
    AssignmentOperationType.ASSIGN_SUBTRACTION,
    AssignmentOperationType.ASSIGN,
    AssignmentOperationType.ASSIGN_OR,
    AssignmentOperationType.ASSIGN_CARET,
    AssignmentOperationType.ASSIGN_AND,
    AssignmentOperationType.ASSIGN_LEFT_SHIFT,
    AssignmentOperationType.ASSIGN_RIGHT_SHIFT,
    AssignmentOperationType.ASSIGN_MULTIPLICATION,
    AssignmentOperationType.ASSIGN_DIVISION,
    AssignmentOperationType.ASSIGN_MODULO,
]


class ASOR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "ASOR"
    HELP = "Assignment Operator Replacement"

    def _mutate(self) -> Dict:
        result: Dict = {}

        for (  # pylint: disable=too-many-nested-blocks
            function
        ) in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                for ir in node.irs:
                    if (
                        isinstance(ir.expression, AssignmentOperation)
                        and ir.expression.type in assignment_operators
                    ):
                        if ir.expression.type == AssignmentOperationType.ASSIGN:
                            continue
                        alternative_ops = assignment_operators[:]
                        try:
                            alternative_ops.remove(ir.expression.type)
                        except:  # pylint: disable=bare-except
                            continue
                        for op in alternative_ops:
                            if op != ir.expression:
                                start = node.source_mapping.start
                                stop = start + node.source_mapping.length
                                old_str = node.source_mapping.content
                                line_no = node.source_mapping.lines
                                # Replace the expression with true
                                new_str = f"{old_str.split(str(ir.expression.type))[0]}{op}{old_str.split(str(ir.expression.type))[1]}"
                                create_patch_with_line(
                                    result,
                                    self.in_file,
                                    start,
                                    stop,
                                    old_str,
                                    new_str,
                                    line_no[0],
                                )
        return result
