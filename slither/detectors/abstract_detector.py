import abc
import re
from logging import Logger
from typing import Optional, List, TYPE_CHECKING, Dict, Union, Callable

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations import Contract
from slither.utils.colors import green, yellow, red
from slither.formatters.exceptions import FormatImpossible
from slither.formatters.utils.patches import apply_patch, create_diff
from slither.utils.comparable_enum import ComparableEnum
from slither.utils.output import Output, SupportedOutput

if TYPE_CHECKING:
    from slither import Slither


class IncorrectDetectorInitialization(Exception):
    pass


class DetectorClassification(ComparableEnum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    INFORMATIONAL = 3
    OPTIMIZATION = 4

    UNIMPLEMENTED = 999


classification_colors: Dict[DetectorClassification, Callable[[str], str]] = {
    DetectorClassification.INFORMATIONAL: green,
    DetectorClassification.OPTIMIZATION: green,
    DetectorClassification.LOW: green,
    DetectorClassification.MEDIUM: yellow,
    DetectorClassification.HIGH: red,
}

classification_txt = {
    DetectorClassification.INFORMATIONAL: "Informational",
    DetectorClassification.OPTIMIZATION: "Optimization",
    DetectorClassification.LOW: "Low",
    DetectorClassification.MEDIUM: "Medium",
    DetectorClassification.HIGH: "High",
}


class AbstractDetector(metaclass=abc.ABCMeta):
    ARGUMENT = ""  # run the detector with slither.py --ARGUMENT
    HELP = ""  # help information
    IMPACT: DetectorClassification = DetectorClassification.UNIMPLEMENTED
    CONFIDENCE: DetectorClassification = DetectorClassification.UNIMPLEMENTED

    WIKI = ""

    WIKI_TITLE = ""
    WIKI_DESCRIPTION = ""
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = ""

    STANDARD_JSON = True

    def __init__(
        self, compilation_unit: SlitherCompilationUnit, slither: "Slither", logger: Logger
    ):
        self.compilation_unit: SlitherCompilationUnit = compilation_unit
        self.contracts: List[Contract] = compilation_unit.contracts
        self.slither: "Slither" = slither
        # self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectDetectorInitialization(
                f"HELP is not initialized {self.__class__.__name__}"
            )

        if not self.ARGUMENT:
            raise IncorrectDetectorInitialization(
                f"ARGUMENT is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI:
            raise IncorrectDetectorInitialization(
                f"WIKI is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_TITLE:
            raise IncorrectDetectorInitialization(
                f"WIKI_TITLE is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_DESCRIPTION:
            raise IncorrectDetectorInitialization(
                f"WIKI_DESCRIPTION is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_EXPLOIT_SCENARIO and self.IMPACT not in [
            DetectorClassification.INFORMATIONAL,
            DetectorClassification.OPTIMIZATION,
        ]:
            raise IncorrectDetectorInitialization(
                f"WIKI_EXPLOIT_SCENARIO is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_RECOMMENDATION:
            raise IncorrectDetectorInitialization(
                f"WIKI_RECOMMENDATION is not initialized {self.__class__.__name__}"
            )

        if re.match("^[a-zA-Z0-9_-]*$", self.ARGUMENT) is None:
            raise IncorrectDetectorInitialization(
                f"ARGUMENT has illegal character {self.__class__.__name__}"
            )

        if self.IMPACT not in [
            DetectorClassification.LOW,
            DetectorClassification.MEDIUM,
            DetectorClassification.HIGH,
            DetectorClassification.INFORMATIONAL,
            DetectorClassification.OPTIMIZATION,
        ]:
            raise IncorrectDetectorInitialization(
                f"IMPACT is not initialized {self.__class__.__name__}"
            )

        if self.CONFIDENCE not in [
            DetectorClassification.LOW,
            DetectorClassification.MEDIUM,
            DetectorClassification.HIGH,
            DetectorClassification.INFORMATIONAL,
            DetectorClassification.OPTIMIZATION,
        ]:
            raise IncorrectDetectorInitialization(
                f"CONFIDENCE is not initialized {self.__class__.__name__}"
            )

    def _log(self, info: str) -> None:
        if self.logger:
            self.logger.info(self.color(info))

    @abc.abstractmethod
    def _detect(self) -> List[Output]:
        """TODO Documentation"""
        return []

    # pylint: disable=too-many-branches
    def detect(self) -> List[Dict]:
        results: List[Dict] = []
        # only keep valid result, and remove duplicate
        # Keep only dictionaries
        for r in [output.data for output in self._detect()]:
            if self.compilation_unit.core.valid_result(r) and r not in results:
                results.append(r)
        if results and self.logger:
            self._log_result(results)
        if self.compilation_unit.core.generate_patches:
            for result in results:
                try:
                    self._format(self.compilation_unit, result)
                    if not "patches" in result:
                        continue
                    result["patches_diff"] = {}
                    for file in result["patches"]:
                        original_txt = self.compilation_unit.core.source_code[file].encode("utf8")
                        patched_txt = original_txt
                        offset = 0
                        patches = result["patches"][file]
                        patches.sort(key=lambda x: x["start"])
                        if not all(
                            patches[i]["end"] <= patches[i + 1]["end"]
                            for i in range(len(patches) - 1)
                        ):
                            self._log(
                                f"Impossible to generate patch; patches collisions: {patches}"
                            )
                            continue
                        for patch in patches:
                            patched_txt, offset = apply_patch(patched_txt, patch, offset)
                        diff = create_diff(self.compilation_unit, original_txt, patched_txt, file)
                        if not diff:
                            self._log(f"Impossible to generate patch; empty {result}")
                        else:
                            result["patches_diff"][file] = diff

                except FormatImpossible as exception:
                    self._log(f'\nImpossible to patch:\n\t{result["description"]}\t{exception}')

        if results and self.slither.triage_mode:
            while True:
                indexes = input(
                    f'Results to hide during next runs: "0,1,...,{len(results)}" or "All" (enter to not hide results): '
                )
                if indexes == "All":
                    self.slither.save_results_to_hide(results)
                    return []
                if indexes == "":
                    return results
                if indexes.startswith("["):
                    indexes = indexes[1:]
                if indexes.endswith("]"):
                    indexes = indexes[:-1]
                try:
                    indexes_converted = [int(i) for i in indexes.split(",")]
                    self.slither.save_results_to_hide(
                        [r for (idx, r) in enumerate(results) if idx in indexes_converted]
                    )
                    return [r for (idx, r) in enumerate(results) if idx not in indexes_converted]
                except ValueError:
                    self.logger.error(yellow("Malformed input. Example of valid input: 0,1,2,3"))
        results = sorted(results, key=lambda x: x["id"])

        return results

    @property
    def color(self) -> Callable[[str], str]:
        return classification_colors[self.IMPACT]

    def generate_result(
        self,
        info: Union[str, List[Union[str, SupportedOutput]]],
        additional_fields: Optional[Dict] = None,
    ) -> Output:
        output = Output(
            info,
            additional_fields,
            standard_format=self.STANDARD_JSON,
            markdown_root=self.slither.markdown_root,
        )

        output.data["check"] = self.ARGUMENT
        output.data["impact"] = classification_txt[self.IMPACT]
        output.data["confidence"] = classification_txt[self.CONFIDENCE]

        return output

    @staticmethod
    def _format(_compilation_unit: SlitherCompilationUnit, _result: Dict) -> None:
        """Implement format"""
        return

    def _log_result(self, results: List[Dict]) -> None:
        info = "\n"
        for idx, result in enumerate(results):
            if self.slither.triage_mode:
                info += f"{idx}: "
            info += result["description"]
        info += f"Reference: {self.WIKI}"
        self._log(info)
