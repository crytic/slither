import abc

from slither.utils.colors import green, yellow, red
from slither.utils.output import Output


class IncorrectCheckInitialization(Exception):
    pass


class CheckClassification:
    HIGH = 0
    MEDIUM = 1
    LOW = 2
    INFORMATIONAL = 3


classification_colors = {
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


class AbstractCheck(metaclass=abc.ABCMeta):
    ARGUMENT = ""
    HELP = ""
    IMPACT = None

    WIKI = ""

    WIKI_TITLE = ""
    WIKI_DESCRIPTION = ""
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = ""

    REQUIRE_CONTRACT = False
    REQUIRE_PROXY = False
    REQUIRE_CONTRACT_V2 = False

    def __init__(self, logger, contract, proxy=None, contract_v2=None):
        self.logger = logger
        self.contract = contract
        self.proxy = proxy
        self.contract_v2 = contract_v2

        if not self.ARGUMENT:
            raise IncorrectCheckInitialization(
                "NAME is not initialized {}".format(self.__class__.__name__)
            )

        if not self.HELP:
            raise IncorrectCheckInitialization(
                "HELP is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI:
            raise IncorrectCheckInitialization(
                "WIKI is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_TITLE:
            raise IncorrectCheckInitialization(
                "WIKI_TITLE is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_DESCRIPTION:
            raise IncorrectCheckInitialization(
                "WIKI_DESCRIPTION is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_EXPLOIT_SCENARIO and self.IMPACT not in [
            CheckClassification.INFORMATIONAL
        ]:
            raise IncorrectCheckInitialization(
                "WIKI_EXPLOIT_SCENARIO is not initialized {}".format(self.__class__.__name__)
            )

        if not self.WIKI_RECOMMENDATION:
            raise IncorrectCheckInitialization(
                "WIKI_RECOMMENDATION is not initialized {}".format(self.__class__.__name__)
            )

        if self.REQUIRE_PROXY and self.REQUIRE_CONTRACT_V2:
            # This is not a fundatemenal issues
            # But it requires to change __main__ to avoid running two times the detectors
            txt = "REQUIRE_PROXY and REQUIRE_CONTRACT_V2 needs change in __main___ {}".format(
                self.__class__.__name__
            )
            raise IncorrectCheckInitialization(txt)

        if self.IMPACT not in [
            CheckClassification.LOW,
            CheckClassification.MEDIUM,
            CheckClassification.HIGH,
            CheckClassification.INFORMATIONAL,
        ]:
            raise IncorrectCheckInitialization(
                "IMPACT is not initialized {}".format(self.__class__.__name__)
            )

        if self.REQUIRE_CONTRACT_V2 and contract_v2 is None:
            raise IncorrectCheckInitialization(
                "ContractV2 is not initialized {}".format(self.__class__.__name__)
            )

        if self.REQUIRE_PROXY and proxy is None:
            raise IncorrectCheckInitialization(
                "Proxy is not initialized {}".format(self.__class__.__name__)
            )

    @abc.abstractmethod
    def _check(self):
        """TODO Documentation"""
        return []

    def check(self):
        all_results = self._check()
        # Keep only dictionaries
        all_results = [r.data for r in all_results]
        if all_results:
            if self.logger:
                info = "\n"
                for idx, result in enumerate(all_results):
                    info += result["description"]
                info += "Reference: {}".format(self.WIKI)
                self._log(info)
        return all_results

    def generate_result(self, info, additional_fields=None):
        output = Output(info, additional_fields, markdown_root=self.contract.slither.markdown_root)

        output.data["check"] = self.ARGUMENT

        return output

    def _log(self, info):
        if self.logger:
            self.logger.info(self.color(info))

    @property
    def color(self):
        return classification_colors[self.IMPACT]
