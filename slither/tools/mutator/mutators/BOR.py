from typing import Dict
from slither.slithir.operations import Binary, BinaryType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator

bitwise_operators = [
    BinaryType.AND,
    BinaryType.OR,
    BinaryType.LEFT_SHIFT,
    BinaryType.RIGHT_SHIFT,
    BinaryType.CARET,
]


class BOR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "BOR"
    HELP = "Bitwise Operator Replacement"

    def _mutate(self) -> Dict:
        result: Dict = {}

        for (  # pylint: disable=too-many-nested-blocks
            function
        ) in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                for ir in node.irs:
                    if isinstance(ir, Binary) and ir.type in bitwise_operators:
                        alternative_ops = bitwise_operators[:]
                        alternative_ops.remove(ir.type)
                        for op in alternative_ops:
                            # Get the string
                            start = node.source_mapping.start
                            stop = start + node.source_mapping.length
                            old_str = self.in_file_str[start:stop]
                            line_no = node.source_mapping.lines
                            if not line_no[0] in self.dont_mutate_line:
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
