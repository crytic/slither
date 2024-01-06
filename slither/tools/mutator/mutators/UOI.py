from typing import Dict
import re
from slither.core.expressions.unary_operation import UnaryOperationType
from slither.slithir.variables import Constant
from slither.core.variables.local_variable import LocalVariable
from slither.core.expressions.expression import Expression
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature, FaultClass
from slither.core.cfg.node import NodeType


unary_operators = [
    UnaryOperationType.PLUSPLUS_PRE,
    UnaryOperationType.MINUSMINUS_PRE,
    UnaryOperationType.PLUSPLUS_POST,
    UnaryOperationType.MINUSMINUS_POST,
    UnaryOperationType.MINUS_PRE,
]


class UOI(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "UOI"
    HELP = "Unary operator insertion"
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
                if (node.type == NodeType.EXPRESSION):
                    for op in unary_operators:
                        if str(op) in str(node.expression):
                            for i in node.variables_written:
                                print(i)
                            # Get the string
                            start = node.source_mapping.start
                            stop = start + node.source_mapping.length
                            old_str = in_file_str[start:stop]
                            # print(old_str)
                            # Replace the expression with true
                            # new_str = old_str.replace(str(operand), f"{str(op)}{operand}")
                            # new_str = re.sub(r'(\w+)\+\+', r'++\1', text)
                            # print(new_str)
                            # create_patch(result, in_file, start, stop, old_str, new_str)
        print(result)
        return result