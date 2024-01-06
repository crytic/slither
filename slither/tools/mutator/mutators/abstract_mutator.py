import abc
import logging
from enum import Enum
from typing import Optional, Dict, Tuple, List

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.tools.doctor.utils import snip_section
from slither.formatters.utils.patches import apply_patch, create_diff
from slither.tools.mutator.utils.testing_generated_mutant import test_patch
logger = logging.getLogger("Slither-Mutate")


class IncorrectMutatorInitialization(Exception):
    pass


class FaultClass(Enum):
    Assignement = 0
    Checking = 1
    Interface = 2
    Algorithm = 3
    Undefined = 100


class FaultNature(Enum):
    Missing = 0
    Wrong = 1
    Extraneous = 2
    Undefined = 100


class AbstractMutator(metaclass=abc.ABCMeta):  # pylint: disable=too-few-public-methods
    NAME = ""
    HELP = ""
    FAULTCLASS = FaultClass.Undefined
    FAULTNATURE = FaultNature.Undefined
    VALID_MUTANTS_COUNT = 0
    INVALID_MUTANTS_COUNT = 0

    def __init__(
        self, compilation_unit: SlitherCompilationUnit, rate: int = 10, seed: Optional[int] = None
    ):
        self.compilation_unit = compilation_unit
        self.slither = compilation_unit.core
        self.seed = seed
        self.rate = rate

        if not self.NAME:
            raise IncorrectMutatorInitialization(
                f"NAME is not initialized {self.__class__.__name__}"
            )

        if not self.HELP:
            raise IncorrectMutatorInitialization(
                f"HELP is not initialized {self.__class__.__name__}"
            )

        if self.FAULTCLASS == FaultClass.Undefined:
            raise IncorrectMutatorInitialization(
                f"FAULTCLASS is not initialized {self.__class__.__name__}"
            )

        if self.FAULTNATURE == FaultNature.Undefined:
            raise IncorrectMutatorInitialization(
                f"FAULTNATURE is not initialized {self.__class__.__name__}"
            )

        if rate < 0 or rate > 100:
            raise IncorrectMutatorInitialization(
                f"rate must be between 0 and 100 {self.__class__.__name__}"
            )

    @abc.abstractmethod
    def _mutate(self, test_cmd: str, test_dir: str) -> Dict:
        """TODO Documentation"""
        return {}

    def mutate(self, testing_command: str, testing_directory: str, contract_name: str) -> Tuple[int, int]:
        # identify the main contract, ignore the imports
        for contract in self.slither.contracts:
            if contract_name == str(contract.name):
                self.contract = contract

        # call _mutate function from different mutators
        (all_patches) = self._mutate()

        if "patches" not in all_patches:
            logger.debug(f"No patches found by {self.NAME}")
            return (0,0)

        for file in all_patches["patches"]:
            original_txt = self.slither.source_code[file].encode("utf8")
            patched_txt = original_txt
            offset = 0
            patches = all_patches["patches"][file]
            patches.sort(key=lambda x: x["start"])
            # if not all(patches[i]["end"] <= patches[i + 1]["end"] for i in range(len(patches) - 1)):
            #     logger.error(f"Impossible to generate patch; patches collisions: {patches}")
            #     continue
            for patch in patches:
                # print(patch)
                # test the patch
                flag = test_patch(file, patch, testing_command, self.VALID_MUTANTS_COUNT, self.NAME)
                # count the valid and invalid mutants
                if not flag:
                    self.INVALID_MUTANTS_COUNT += 1
                    continue
                self.VALID_MUTANTS_COUNT += 1
            #     patched_txt, offset = apply_patch(patched_txt, patch, offset)
            # diff = create_diff(self.compilation_unit, original_txt, patched_txt, file)
            # if not diff:
            #     logger.info(f"Impossible to generate patch; empty {patches}")

            # print the differences
            # print(diff)
        
        return (self.VALID_MUTANTS_COUNT, self.INVALID_MUTANTS_COUNT)
    
    
    
    