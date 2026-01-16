from slither.core.cfg.node import NodeType
from slither.tools.mutator.utils.patch import create_patch_with_line
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator


class RR(AbstractMutator):
    NAME = "RR"
    HELP = "Revert Replacement"

    def _mutate(self) -> dict:
        result: dict = {}

        for function in self.contract.functions_and_modifiers_declared:
            if not self.should_mutate_function(function):
                continue
            for node in function.nodes:
                if not self.should_mutate_node(node):
                    continue
                if node.type not in (
                    NodeType.ENTRYPOINT,
                    NodeType.IF,
                    NodeType.ENDIF,
                    NodeType.ENDLOOP,
                    NodeType.PLACEHOLDER,
                ):
                    # Get the string
                    start = node.source_mapping.start
                    stop = start + node.source_mapping.length
                    old_str = node.source_mapping.content
                    line_no = node.source_mapping.lines[0]
                    if node.type == NodeType.RETURN and not old_str.lstrip().startswith("return"):
                        continue  # skip the return declarations in fn signatures
                    if not old_str.lstrip().startswith("revert"):
                        new_str = "revert()"
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
