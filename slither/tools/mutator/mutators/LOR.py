from typing import Dict
from slither.slithir.operations import Binary, BinaryType
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature, FaultClass

logical_operators = [
    BinaryType.OROR,
    BinaryType.ANDAND,
]

class LOR(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "LOR"
    HELP = "Logical operator replacement"
    FAULTCLASS = FaultClass.Checking
    FAULTNATURE = FaultNature.Missing

    def _mutate(self) -> Dict:

        result: Dict = {}

        contract = self.contract

        # Retrieve the file
        in_file = contract.source_mapping.filename.absolute
        # Retrieve the source code
        in_file_str = contract.compilation_unit.core.source_code[in_file]
        for function in contract.functions_and_modifiers_declared:

            for node in function.nodes:
                for ir in node.irs:
                    if isinstance(ir, Binary) and ir.type in logical_operators:
                        alternative_ops = logical_operators[:]
                        alternative_ops.remove(ir.type)

                        for op in alternative_ops:

                            # Get the string
                            start = node.source_mapping.start
                            stop = start + node.source_mapping.length
                            old_str = in_file_str[start:stop]
                            line_no = node.source_mapping.lines
                            # Replace the expression with true
                            # new_str = f"{ir.variable_left} {op.value} {ir.variable_right}"
                            new_str = f"{old_str.split(ir.type.value)[0]} {op.value} {old_str.split(ir.type.value)[1]}"

                            create_patch(result, in_file, start, stop, old_str, new_str, line_no[0])
        return result