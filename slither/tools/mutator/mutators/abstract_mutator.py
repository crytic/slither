import abc
import logging
from enum import Enum
from typing import Optional, Dict, Tuple
from slither.core.compilation_unit import SlitherCompilationUnit
# from slither.tools.doctor.utils import snip_section
from slither.formatters.utils.patches import apply_patch, create_diff
from slither.tools.mutator.utils.testing_generated_mutant import test_patch
from slither.utils.colors import yellow

logger = logging.getLogger("Slither-Mutate")

class IncorrectMutatorInitialization(Exception):
    pass

class FaultNature(Enum):
    Missing = 0
    Wrong = 1
    Extraneous = 2
    Undefined = 100

    # not executed - can be detected by replacing with revert
    # has no effect - can be detected by removing a line / comment
    # can have valid mutant  
    # can't have valid mutant
    
class AbstractMutator(metaclass=abc.ABCMeta):  # pylint: disable=too-few-public-methods
    NAME = ""
    HELP = ""
    FAULTNATURE = FaultNature.Undefined
    VALID_MUTANTS_COUNT = 0
    INVALID_MUTANTS_COUNT = 0

    def __init__(
        self, compilation_unit: SlitherCompilationUnit, 
        timeout: int, 
        testing_command: str, 
        testing_directory: str, 
        contract_name: str, 
        solc_remappings: str | None, 
        verbose: bool,
        output_folder: str,
        rate: int = 10, 
        seed: Optional[int] = None
    ) -> None:
        self.compilation_unit = compilation_unit
        self.slither = compilation_unit.core
        self.seed = seed
        self.rate = rate
        self.test_command = testing_command
        self.test_directory = testing_directory
        self.timeout = timeout
        self.contract_exist = False
        self.solc_remappings = solc_remappings
        self.verbose = verbose
        self.output_folder = output_folder

        if not self.NAME:
            raise IncorrectMutatorInitialization(
                f"NAME is not initialized {self.__class__.__name__}"
            )

        if not self.HELP:
            raise IncorrectMutatorInitialization(
                f"HELP is not initialized {self.__class__.__name__}"
            )

        if self.FAULTNATURE == FaultNature.Undefined:
            raise IncorrectMutatorInitialization(
                f"FAULTNATURE is not initialized {self.__class__.__name__}"
            )

        if rate < 0 or rate > 100:
            raise IncorrectMutatorInitialization(
                f"rate must be between 0 and 100 {self.__class__.__name__}"
            )
        
        # identify the main contract, ignore the imports
        for contract in self.slither.contracts:
            # !limitation: what if the contract name is not same as file name
            # !limitation: multi contract
            if contract_name.lower() == str(contract.name).lower(): 
                # contract
                self.contract = contract
                # Retrieve the file
                self.in_file = self.contract.source_mapping.filename.absolute
                # Retrieve the source code
                self.in_file_str = self.contract.compilation_unit.core.source_code[self.in_file]
                # flag contract existence
                self.contract_exist = True

        if not self.contract_exist:
            self.contract_exist = False
            logger.error(f"Contract name is not matching with the File name ({contract_name}). Please refer 'https://docs.soliditylang.org/en/latest/style-guide.html#contract-and-library-names')")
                
    def get_exist_flag(self) -> bool:
        return self.contract_exist
    
    @abc.abstractmethod
    def _mutate(self) -> Dict:
        """TODO Documentation"""
        return {}

    def mutate(self) -> Tuple[int, int]:
        # call _mutate function from different mutators
        (all_patches) = self._mutate()

        if "patches" not in all_patches:
            logger.debug(f"No patches found by {self.NAME}")
            return (0,0)
        
        for file in all_patches["patches"]:
            original_txt = self.slither.source_code[file].encode("utf8")
            patches = all_patches["patches"][file]
            patches.sort(key=lambda x: x["start"])
            print(yellow(f"Mutating {file} with {self.NAME} \n"))
            for patch in patches:
                # test the patch
                flag = test_patch(file, patch, self.test_command, self.VALID_MUTANTS_COUNT, self.NAME, self.timeout, self.solc_remappings, self.verbose)
                # count the valid and invalid mutants
                if not flag:
                    self.INVALID_MUTANTS_COUNT += 1
                    continue
                self.VALID_MUTANTS_COUNT += 1
                patched_txt,_ = apply_patch(original_txt, patch, 0)
                diff = create_diff(self.compilation_unit, original_txt, patched_txt, file)
                if not diff:
                    logger.info(f"Impossible to generate patch; empty {patches}")

                # add valid mutant patches to a output file
                with open(self.output_folder + "/patches_file.txt", 'a') as patches_file:
                    patches_file.write(diff + '\n')
        
        return (self.VALID_MUTANTS_COUNT, self.INVALID_MUTANTS_COUNT)
    
    
    
    