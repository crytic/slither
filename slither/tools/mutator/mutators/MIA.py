from slither.core.cfg.node import NodeType
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature, FaulClass


class MIA(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "MIA"
    HELP = '"if" construct around statement'
    FAULTCLASS = FaulClass.Checking
    FAULTNATURE = FaultNature.Missing

    def _mutate(self):

        result = {}

        for contract in self.slither.contracts:

            for function in contract.functions_declared + contract.modifiers_declared:

                for node in function.nodes:
                    if node.type == NodeType.IF:
                        # Retrieve the file
                        in_file = contract.source_mapping.filename.absolute
                        # Retrieve the source code
                        in_file_str = contract.compilation_unit.core.source_code[in_file]

                        # Get the string
                        start = node.source_mapping.start
                        stop = start + node.source_mapping.length
                        old_str = in_file_str[start:stop]

                        # Replace the expression with true
                        new_str = "true"

                        create_patch(result, in_file, start, stop, old_str, new_str)

        return result
