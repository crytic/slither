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
    VALID_RR_MUTANTS_COUNT = 0
    VALID_CR_MUTANTS_COUNT = 0
    # total revert/comment/tweak mutants that were generated and compiled
    total_mutant_counts = [0, 0, 0]
    # total valid revert/comment/tweak mutants
    valid_mutant_counts = [0, 0, 0]

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

    def mutate(self) -> Tuple[List[int], List[int], List[int]]:
        # call _mutate function from different mutators
        (all_patches) = self._mutate()
        if "patches" not in all_patches:
            logger.debug("No patches found by %s", self.NAME)
            return ([0, 0, 0], [0, 0, 0], self.dont_mutate_line)
        for file in all_patches["patches"]: # Note: This should only loop over a single file
            original_txt = self.slither.source_code[file].encode("utf8")
            patches = all_patches["patches"][file]
            patches.sort(key=lambda x: x["start"])
            logger.info(yellow(f"Mutating {file} with {self.NAME} \n"))
            for patch in patches:
                # test the patch

                patchIsValid = test_patch(
                    file,
                    patch,
                    self.test_command,
                    self.NAME,
                    self.timeout,
                    self.solc_remappings,
                    self.verbose,
                )

                # count the valid mutants, flag RR/CR mutants to skip further mutations
                if patchIsValid == 0:
                    if self.NAME == 'RR':
                        self.valid_mutant_counts[0] += 1
                        self.dont_mutate_line.append(patch['line_number'])
                    elif self.NAME == 'CR':
                        self.valid_mutant_counts[1] += 1
                        self.dont_mutate_line.append(patch['line_number'])
                    else:
                        self.valid_mutant_counts[2] += 1

                    patched_txt,_ = apply_patch(original_txt, patch, 0)
                    diff = create_diff(self.compilation_unit, original_txt, patched_txt, file)
                    if not diff:
                        logger.info(f"Impossible to generate patch; empty {patches}")

                    # add valid mutant patches to a output file
                    with open(
                        self.output_folder + "/patches_file.txt", "a", encoding="utf8"
                    ) as patches_file:
                        patches_file.write(diff + "\n")

                # count the total number of mutants that we were able to compile
                if patchIsValid != 2:
                    if self.NAME == 'RR':
                        self.total_mutant_counts[0] += 1
                    elif self.NAME == 'CR':
                        self.total_mutant_counts[1] += 1
                    else:
                        self.total_mutant_counts[2] += 1

                if self.verbose:
                    if self.NAME == "RR":
                        logger.info(f"Found {self.valid_mutant_counts[0]} uncaught revert mutants so far (out of {self.total_mutant_counts[0]} that compile)")
                    elif self.NAME == "CR":
                        logger.info(f"Found {self.valid_mutant_counts[1]} uncaught comment mutants so far (out of {self.total_mutant_counts[1]} that compile)")
                    else:
                        logger.info(f"Found {self.valid_mutant_counts[2]} uncaught tweak mutants so far (out of {self.total_mutant_counts[2]} that compile)")

            if self.verbose:
                logger.info(f"Done mutating file {file}")
                logger.info(f"Found {self.valid_mutant_counts[0]} uncaught revert mutants (out of {self.total_mutant_counts[0]} that compile)")
                logger.info(f"Found {self.valid_mutant_counts[1]} uncaught comment mutants (out of {self.total_mutant_counts[1]} that compile)")
                logger.info(f"Found {self.valid_mutant_counts[2]} uncaught tweak mutants (out of {self.total_mutant_counts[2]} that compile)")

        return (
            self.total_mutant_counts,
            self.valid_mutant_counts,
            self.dont_mutate_line
        )
