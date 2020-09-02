import abc
import re

from slither.utils.colors import green, yellow, red
from slither.formatters.exceptions import FormatImpossible
from slither.formatters.utils.patches import apply_patch, create_diff
from slither.utils.output import Output


class IncorrectDetectorInitialization(Exception):
    pass


class DetectorClassification:  # pylint: disable=too-few-public-methods
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    INFORMATIONAL = 3
    OPTIMIZATION = 4


classification_colors = {
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
    IMPACT = None
    CONFIDENCE = None

    WIKI = ""

    WIKI_TITLE = ""
    WIKI_DESCRIPTION = ""
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = ""

    STANDARD_JSON = True

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectDetectorInitialization(
                "HELP is not initialized {}".format(self.__class__.__name__)
            )

        if not self.ARGUMENT:
            raise IncorrectDetectorInitialization(
                "ARGUMENT is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI:
            raise IncorrectDetectorInitialization(
                "WIKI is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_TITLE:
            raise IncorrectDetectorInitialization(
                "WIKI_TITLE is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_DESCRIPTION:
            raise IncorrectDetectorInitialization(
                "WIKI_DESCRIPTION is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_EXPLOIT_SCENARIO and self.IMPACT not in [
            DetectorClassification.INFORMATIONAL,
            DetectorClassification.OPTIMIZATION,
        ]:
            raise IncorrectDetectorInitialization(
                "WIKI_EXPLOIT_SCENARIO is not initialized {}".format(
                    self.__class__.__name__
                )
            )

        if not self.WIKI_RECOMMENDATION:
            raise IncorrectDetectorInitialization(
                "WIKI_RECOMMENDATION is not initialized {}".format(
                    self.__class__.__name__
                )
            )

        if re.match("^[a-zA-Z0-9_-]*$", self.ARGUMENT) is None:
            raise IncorrectDetectorInitialization(
                "ARGUMENT has illegal character {}".format(self.__class__.__name__)
            )

        if self.IMPACT not in [
            DetectorClassification.LOW,
            DetectorClassification.MEDIUM,
            DetectorClassification.HIGH,
            DetectorClassification.INFORMATIONAL,
            DetectorClassification.OPTIMIZATION,
        ]:
            raise IncorrectDetectorInitialization(
                "IMPACT is not initialized {}".format(self.__class__.__name__)
            )

        if self.CONFIDENCE not in [
            DetectorClassification.LOW,
            DetectorClassification.MEDIUM,
            DetectorClassification.HIGH,
            DetectorClassification.INFORMATIONAL,
            DetectorClassification.OPTIMIZATION,
        ]:
            raise IncorrectDetectorInitialization(
                "CONFIDENCE is not initialized {}".format(self.__class__.__name__)
            )

    def _log(self, info):
        if self.logger:
            self.logger.info(self.color(info))

    @abc.abstractmethod
    def _detect(self):
        """TODO Documentation"""
        return []

    # pylint: disable=too-many-branches
    def detect(self):
        all_results = self._detect()
        # Keep only dictionaries
        all_results = [r.data for r in all_results]
        results = []
        # only keep valid result, and remove dupplicate
        # pylint: disable=expression-not-assigned
        [
            results.append(r)
            for r in all_results
            if self.slither.valid_result(r) and r not in results
        ]
        if results:
            if self.logger:
                info = "\n"
                for idx, result in enumerate(results):
                    if self.slither.triage_mode:
                        info += "{}: ".format(idx)
                    info += result["description"]
                info += "Reference: {}".format(self.WIKI)
                self._log(info)
        if self.slither.generate_patches:
            for result in results:
                try:
                    self._format(self.slither, result)
                    if not "patches" in result:
                        continue
                    result["patches_diff"] = dict()
                    for file in result["patches"]:
                        original_txt = self.slither.source_code[file].encode("utf8")
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
                            patched_txt, offset = apply_patch(
                                patched_txt, patch, offset
                            )
                        diff = create_diff(
                            self.slither, original_txt, patched_txt, file
                        )
                        if not diff:
                            self._log(f"Impossible to generate patch; empty {result}")
                        else:
                            result["patches_diff"][file] = diff

                except FormatImpossible as exception:
                    self._log(f'\nImpossible to patch:\n\t{result["description"]}\t{exception}')

        if results and self.slither.triage_mode:
            while True:
                indexes = input(
                    'Results to hide during next runs: "0,1,...,{}" or "All" (enter to not hide results): '.format(
                        len(results)
                    )
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
                    indexes = [int(i) for i in indexes.split(",")]
                    self.slither.save_results_to_hide(
                        [r for (idx, r) in enumerate(results) if idx in indexes]
                    )
                    return [r for (idx, r) in enumerate(results) if idx not in indexes]
                except ValueError:
                    self.logger.error(
                        yellow("Malformed input. Example of valid input: 0,1,2,3")
                    )
        return results

    @property
    def color(self):
        return classification_colors[self.IMPACT]

    def generate_result(self, info, additional_fields=None):
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
    def _format(_slither, _result):
        """Implement format"""
        return
