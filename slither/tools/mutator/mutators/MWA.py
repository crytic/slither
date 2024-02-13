from typing import Dict
from slither.core.cfg.node import NodeType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator
from slither.core.expressions.unary_operation import UnaryOperationType, UnaryOperation


class MWA(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "MWA"
    HELP = '"while" construct around statement'

    def _mutate(self) -> Dict:
        result: Dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                if node.type == NodeType.IFLOOP:
                    # Get the string
                    start = node.source_mapping.start
                    stop = start + node.source_mapping.length
                    old_str = self.in_file_str[start:stop]
                    line_no = node.source_mapping.lines
                    if not line_no[0] in self.dont_mutate_line:
                        if not isinstance(node.expression, UnaryOperation):
                            new_str = str(UnaryOperationType.BANG) + "(" + old_str + ")"
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
