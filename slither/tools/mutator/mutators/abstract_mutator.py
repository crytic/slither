import abc
import logging
from typing import Optional, Dict, Tuple, List
from slither.core.compilation_unit import SlitherCompilationUnit
from slither.formatters.utils.patches import apply_patch, create_diff
from slither.tools.mutator.utils.testing_generated_mutant import test_patch
from slither.utils.colors import yellow
from slither.core.declarations import Contract

logger = logging.getLogger("Slither-Mutate")


class IncorrectMutatorInitialization(Exception):
    pass


class AbstractMutator(
    metaclass=abc.ABCMeta
):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    NAME = ""
    HELP = ""
    VALID_MUTANTS_COUNT = 0
    INVALID_MUTANTS_COUNT = 0

    def __init__(  # pylint: disable=too-many-arguments
        self,
        compilation_unit: SlitherCompilationUnit,
        timeout: int,
        testing_command: str,
        testing_directory: str,
        contract_instance: Contract,
        solc_remappings: str | None,
        verbose: bool,
        output_folder: str,
        dont_mutate_line: List[int],
        rate: int = 10,
        seed: Optional[int] = None,
    ) -> None:
        self.compilation_unit = compilation_unit
        self.slither = compilation_unit.core
        self.seed = seed
        self.rate = rate
        self.test_command = testing_command
        self.test_directory = testing_directory
        self.timeout = timeout
        self.solc_remappings = solc_remappings
        self.verbose = verbose
        self.output_folder = output_folder
        self.contract = contract_instance
        self.in_file = self.contract.source_mapping.filename.absolute
        self.in_file_str = self.contract.compilation_unit.core.source_code[self.in_file]
        self.dont_mutate_line = dont_mutate_line

        if not self.NAME:
            raise IncorrectMutatorInitialization(
                f"NAME is not initialized {self.__class__.__name__}"
            )

        if not self.HELP:
            raise IncorrectMutatorInitialization(
                f"HELP is not initialized {self.__class__.__name__}"
            )

        if rate < 0 or rate > 100:
            raise IncorrectMutatorInitialization(
                f"rate must be between 0 and 100 {self.__class__.__name__}"
            )

    @abc.abstractmethod
    def _mutate(self) -> Dict:
        """TODO Documentation"""
        return {}

    def mutate(self) -> Tuple[int, int, List[int]]:
        # call _mutate function from different mutators
        (all_patches) = self._mutate()
        if "patches" not in all_patches:
            logger.debug("No patches found by %s", self.NAME)
            return (0, 0, self.dont_mutate_line)

        for file in all_patches["patches"]:
            original_txt = self.slither.source_code[file].encode("utf8")
            patches = all_patches["patches"][file]
            patches.sort(key=lambda x: x["start"])
            logger.info(yellow(f"Mutating {file} with {self.NAME} \n"))
            for patch in patches:
                # test the patch
                flag = test_patch(
                    file,
                    patch,
                    self.test_command,
                    self.VALID_MUTANTS_COUNT,
                    self.NAME,
                    self.timeout,
                    self.solc_remappings,
                    self.verbose,
                )
                # if RR or CR and valid mutant, add line no.
                if self.NAME in ("RR", "CR") and flag:
                    self.dont_mutate_line.append(patch["line_number"])
                # count the valid and invalid mutants
                if not flag:
                    self.INVALID_MUTANTS_COUNT += 1
                    continue
                self.VALID_MUTANTS_COUNT += 1
                patched_txt, _ = apply_patch(original_txt, patch, 0)
                diff = create_diff(self.compilation_unit, original_txt, patched_txt, file)
                if not diff:
                    logger.info(f"Impossible to generate patch; empty {patches}")

                # add valid mutant patches to a output file
                with open(
                    self.output_folder + "/patches_file.txt", "a", encoding="utf8"
                ) as patches_file:
                    patches_file.write(diff + "\n")
        return (
            self.VALID_MUTANTS_COUNT,
            self.INVALID_MUTANTS_COUNT,
            self.dont_mutate_line,
        )
