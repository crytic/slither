from typing import Dict, Tuple
from slither.core.cfg.node import NodeType
from slither.formatters.utils.patches import create_patch
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature, FaultClass
from slither.tools.mutator.utils.testing_generated_mutant import compile_generated_mutant, run_test_suite
from slither.tools.mutator.utils.replace_conditions import replace_string_in_source_file_specific_line
from slither.tools.mutator.utils.file_handling import create_mutant_file

class MIA(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "MIA"
    HELP = '"if" construct around statement'
    FAULTCLASS = FaultClass.Checking
    FAULTNATURE = FaultNature.Missing
    VALID_MUTANTS_COUNT = 0
    INVALID_MUTANTS_COUNT = 0

    def _mutate(self, test_cmd: str, test_dir: str, contract_name: str) -> Tuple[(Dict, int, int)]:

        result: Dict = {}
        
        for contract in self.slither.contracts:
            # if not contract.is_library:
            #     if not contract.is_interface:
            if contract_name == str(contract.name):
                for function in contract.functions_declared + list(contract.modifiers_declared):
                    for node in function.nodes:
                        if node.contains_if():
                            # print(node.expression)
                            # Retrieve the file
                            in_file = contract.source_mapping.filename.absolute
                            # Retrieve the source code
                            in_file_str = contract.compilation_unit.core.source_code[in_file]

                            # Get the string
                            start = node.source_mapping.start
                            stop = start + node.source_mapping.length
                            # old_str = in_file_str[start:stop]
                            old_str = str(node.expression)
                            line_no = node.source_mapping.lines
                            # Replace the expression with true
                            new_str = "true"
                            print(line_no[0])
                            replace_string_in_source_file_specific_line(in_file, old_str, new_str, line_no[0])
                            
                            # compile and run tests 
                            if compile_generated_mutant(in_file):
                                if run_test_suite(test_cmd, test_dir):
                                    # generate the mutant and patch
                                    create_mutant_file(in_file, self.VALID_MUTANTS_COUNT, self.NAME)
                                    create_patch(result, in_file, start, stop, old_str, new_str)
                                    self.VALID_MUTANTS_COUNT = self.VALID_MUTANTS_COUNT + 1
                                else:
                                    self.INVALID_MUTANTS_COUNT = self.INVALID_MUTANTS_COUNT + 1
                            else:
                                self.INVALID_MUTANTS_COUNT = self.INVALID_MUTANTS_COUNT + 1
        print(self.INVALID_MUTANTS_COUNT)
                                         
                                

        return (result, self.VALID_MUTANTS_COUNT, self.INVALID_MUTANTS_COUNT)

    

    
        
    