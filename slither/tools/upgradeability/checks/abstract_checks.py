import abc
from logging import Logger
from typing import Optional, List, Dict, Union, Callable

from slither.core.declarations import Contract
from slither.utils.colors import green, yellow, red
from slither.utils.comparable_enum import ComparableEnum
from slither.utils.output import Output, SupportedOutput


class IncorrectCheckInitialization(Exception):
    pass


class CheckClassification(ComparableEnum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    INFORMATIONAL = 3
    UNIMPLEMENTED = 999


classification_colors: Dict[CheckClassification, Callable[[str], str]] = {
    CheckClassification.INFORMATIONAL: green,
    CheckClassification.LOW: yellow,
    CheckClassification.MEDIUM: yellow,
    CheckClassification.HIGH: red,
}

classification_txt = {
    CheckClassification.INFORMATIONAL: "Informational",
    CheckClassification.LOW: "Low",
    CheckClassification.MEDIUM: "Medium",
    CheckClassification.HIGH: "High",
}

CHECK_INFO = List[Union[str, SupportedOutput]]


class AbstractCheck(metaclass=abc.ABCMeta):
    ARGUMENT = ""
    HELP = ""
    IMPACT: CheckClassification = CheckClassification.UNIMPLEMENTED

    WIKI = ""

    WIKI_TITLE = ""
    WIKI_DESCRIPTION = ""
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = ""

    REQUIRE_CONTRACT = False
    REQUIRE_PROXY = False
    REQUIRE_CONTRACT_V2 = False

    def __init__(
        self,
        logger: Logger,
        contract: Contract,
        proxy: Optional[Contract] = None,
        contract_v2: Optional[Contract] = None,
    ) -> None:
        self.logger = logger
        self.contract = contract
        self.proxy = proxy
        self.contract_v2 = contract_v2

        if not self.ARGUMENT:
            raise IncorrectCheckInitialization(f"NAME is not initialized {self.__class__.__name__}")

        if not self.HELP:
            raise IncorrectCheckInitialization(f"HELP is not initialized {self.__class__.__name__}")

        if not self.WIKI:
            raise IncorrectCheckInitialization(f"WIKI is not initialized {self.__class__.__name__}")

        if not self.WIKI_TITLE:
            raise IncorrectCheckInitialization(
                f"WIKI_TITLE is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_DESCRIPTION:
            raise IncorrectCheckInitialization(
                f"WIKI_DESCRIPTION is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_EXPLOIT_SCENARIO and self.IMPACT not in [
            CheckClassification.INFORMATIONAL
        ]:
            raise IncorrectCheckInitialization(
                f"WIKI_EXPLOIT_SCENARIO is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI_RECOMMENDATION:
            raise IncorrectCheckInitialization(
                f"WIKI_RECOMMENDATION is not initialized {self.__class__.__name__}"
            )

        if self.REQUIRE_PROXY and self.REQUIRE_CONTRACT_V2:
            # This is not a fundatemenal issues
            # But it requires to change __main__ to avoid running two times the detectors
            txt = f"REQUIRE_PROXY and REQUIRE_CONTRACT_V2 needs change in __main___ {self.__class__.__name__}"
            raise IncorrectCheckInitialization(txt)

        if self.IMPACT not in [
            CheckClassification.LOW,
            CheckClassification.MEDIUM,
            CheckClassification.HIGH,
            CheckClassification.INFORMATIONAL,
        ]:
            raise IncorrectCheckInitialization(
                f"IMPACT is not initialized {self.__class__.__name__}"
            )

        if self.REQUIRE_CONTRACT_V2 and contract_v2 is None:
            raise IncorrectCheckInitialization(
                f"ContractV2 is not initialized {self.__class__.__name__}"
            )

        if self.REQUIRE_PROXY and proxy is None:
            raise IncorrectCheckInitialization(
                f"Proxy is not initialized {self.__class__.__name__}"
            )

    @abc.abstractmethod
    def _check(self) -> List[Output]:
        """TODO Documentation"""
        return []

    def check(self) -> List[Dict]:
        all_outputs = self._check()
        # Keep only dictionaries
        all_results = [r.data for r in all_outputs]
        if all_results:
            if self.logger:
                info = "\n"
                for result in all_results:
                    info += result["description"]
                info += f"Reference: {self.WIKI}"
                self._log(info)
        return all_results

    def generate_result(
        self,
        info: CHECK_INFO,
        additional_fields: Optional[Dict] = None,
    ) -> Output:
        output = Output(
            info, additional_fields, markdown_root=self.contract.compilation_unit.core.markdown_root
        )

        output.data["check"] = self.ARGUMENT

        return output

    def _log(self, info: str) -> None:
        if self.logger:
            self.logger.info(self.color(info))

    @property
    def color(self) -> Callable[[str], str]:
        return classification_colors[self.IMPACT]
