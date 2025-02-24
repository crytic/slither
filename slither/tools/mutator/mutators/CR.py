from typing import Dict
from slither.core.cfg.node import NodeType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator


class CR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "CR"
    HELP = "Comment Replacement"

    def _mutate(self) -> Dict:
        result: Dict = {}

        for (  # pylint: disable=too-many-nested-blocks
            function
        ) in self.contract.functions_and_modifiers_declared:
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                if node.type not in (
                    NodeType.ENTRYPOINT,
                    NodeType.ENDIF,
                    NodeType.ENDLOOP,
                ):
                    # Get the string
                    start = node.source_mapping.start
                    stop = start + node.source_mapping.length
                    old_str = node.source_mapping.content
                    line_no = node.source_mapping.lines
                    new_str = "//" + old_str
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
