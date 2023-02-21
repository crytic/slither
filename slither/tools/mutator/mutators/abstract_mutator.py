import abc
import logging
from enum import Enum
from typing import Optional, Dict

from slither import Slither
from slither.formatters.utils.patches import apply_patch, create_diff

logger = logging.getLogger("Slither")


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

    def __init__(self, slither: Slither, rate: int = 10, seed: Optional[int] = None):
        self.slither = slither
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
    def _mutate(self) -> Dict:
        """TODO Documentation"""
        return {}

    def mutate(self) -> None:
        all_patches = self._mutate()

        if "patches" not in all_patches:
            logger.debug(f"No patches found by {self.NAME}")
            return

        for file in all_patches["patches"]:
            original_txt = self.slither.source_code[file].encode("utf8")
            patched_txt = original_txt
            offset = 0
            patches = all_patches["patches"][file]
            patches.sort(key=lambda x: x["start"])
            if not all(patches[i]["end"] <= patches[i + 1]["end"] for i in range(len(patches) - 1)):
                logger.info(f"Impossible to generate patch; patches collisions: {patches}")
                continue
            for patch in patches:
                patched_txt, offset = apply_patch(patched_txt, patch, offset)
            diff = create_diff(self.slither, original_txt, patched_txt, file)
            if not diff:
                logger.info(f"Impossible to generate patch; empty {patches}")
            print(diff)
