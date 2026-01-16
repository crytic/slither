import abc
from logging import Logger

from typing import TYPE_CHECKING, Union, List, Optional, Dict

from slither.utils import output
from slither.utils.output import SupportedOutput

if TYPE_CHECKING:
    from slither import Slither


class IncorrectPrinterInitialization(Exception):
    pass


class AbstractPrinter(metaclass=abc.ABCMeta):
    ARGUMENT = ""  # run the printer with slither.py --ARGUMENT
    HELP = ""  # help information

    WIKI = ""

    def __init__(self, slither: "Slither", logger: Optional[Logger]) -> None:
        self.slither = slither
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectPrinterInitialization(
                f"HELP is not initialized {self.__class__.__name__}"
            )

        if not self.ARGUMENT:
            raise IncorrectPrinterInitialization(
                f"ARGUMENT is not initialized {self.__class__.__name__}"
            )

        if not self.WIKI:
            raise IncorrectPrinterInitialization(
                f"WIKI is not initialized {self.__class__.__name__}"
            )

    @property
    def contracts(self):
        """Direct accessor to the slither contracts.

        We prefer to delay as much as possible the direct access of contracts to leave the possibility
        for filtering to be applied.
        """
        return self.slither.contracts

    def info(self, info: str) -> None:
        if self.logger:
            self.logger.info(info)

    def generate_output(
        self,
        info: Union[str, List[Union[str, SupportedOutput]]],
        additional_fields: Optional[Dict] = None,
    ) -> output.Output:
        if additional_fields is None:
            additional_fields = {}
        printer_output = output.Output(info, additional_fields)
        printer_output.data["printer"] = self.ARGUMENT

        return printer_output

    @abc.abstractmethod
    def output(self, filename: str) -> output.Output:
        pass
