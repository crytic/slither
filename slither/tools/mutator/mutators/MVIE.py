from typing import Dict, Tuple

from slither.core.expressions import Literal
from slither.core.variables.variable import Variable
from slither.tools.mutator.mutators.abstract_mutator import AbstractMutator, FaultNature, FaultClass
from slither.tools.mutator.utils.generic_patching import remove_assignement
from slither.tools.mutator.utils.file_handling import create_mutant_file

class MVIE(AbstractMutator):  # pylint: disable=too-few-public-methods
    NAME = "MVIE"
    HELP = "variable initialization using an expression"
    FAULTCLASS = FaultClass.Assignement
    FAULTNATURE = FaultNature.Missing
    VALID_MUTANTS_COUNT = 0
    INVALID_MUTANTS_COUNT = 0

    def _mutate(self, test_cmd: str, test_dir: str, contract_name: str) -> Tuple[(Dict, int, int)]:

        result: Dict = {}
        variable: Variable
        for contract in self.slither.contracts:
            # if not contract.is_library:
            #     if not contract.is_interface:
            if contract_name == str(contract.name):
                # Create fault for state variables declaration
                for variable in contract.state_variables_declared:
                    if variable.initialized:
                        # Cannot remove the initialization of constant variables
                        if variable.is_constant:
                            continue

                        if not isinstance(variable.expression, Literal):
                            if(remove_assignement(variable, contract, result, test_cmd, test_dir)):
                                create_mutant_file(contract.source_mapping.filename.absolute, self.VALID_MUTANTS_COUNT, self.NAME)
                            
                for function in contract.functions_declared + list(contract.modifiers_declared):
                    for variable in function.local_variables:
                        if variable.initialized and not isinstance(variable.expression, Literal):
                            if(remove_assignement(variable, contract, result, test_cmd, test_dir)):
                                create_mutant_file(contract.source_mapping.filename.absolute, self.VALID_MUTANTS_COUNT, self.NAME)
                    

        return (result, self.VALID_MUTANTS_COUNT, self.INVALID_MUTANTS_COUNT)
