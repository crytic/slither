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


class BOR(AbstractMutator):
    NAME = "BOR"
    HELP = "Bitwise Operator Replacement"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                for ir in node.irs:
                    if isinstance(ir, Binary) and ir.type in bitwise_operators:
                        alternative_ops = bitwise_operators[:]
                        alternative_ops.remove(ir.type)
                        for op in alternative_ops:
                            # Get the string
                            start = node.source_mapping.start
                            stop = start + node.source_mapping.length
                            old_str = node.source_mapping.content
                            line_no = node.source_mapping.lines
                            # Replace the expression with true
                            halves = old_str.split(ir.type.value)
                            if len(halves) != 2:
                                continue  # skip if assembly
                            new_str = f"{halves[0]}{op.value}{halves[1]}"
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
