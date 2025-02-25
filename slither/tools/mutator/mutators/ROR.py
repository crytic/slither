from typing import Dict
from slither.slithir.operations import Binary, BinaryType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator

relational_operators = [
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
]


class ROR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "ROR"
    HELP = "Relational Operator Replacement"

    def _mutate(self) -> Dict:
        result: Dict = {}

        for (  # pylint: disable=too-many-nested-blocks
            function
        ) in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                for ir in node.irs:
                    if isinstance(ir, Binary) and ir.type in relational_operators:
                        if (
                            str(ir.variable_left.type) != "address"
                            and str(ir.variable_right) != "address"
                        ):
                            alternative_ops = relational_operators[:]
                            alternative_ops.remove(ir.type)
                            for op in alternative_ops:
                                # Get the string
                                start = ir.expression.source_mapping.start
                                stop = start + ir.expression.source_mapping.length
                                old_str = node.source_mapping.content
                                line_no = node.source_mapping.lines
                                # Replace the expression with true
                                new_str = f"{old_str.split(ir.type.value)[0]}{op.value}{old_str.split(ir.type.value)[1]}"
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
