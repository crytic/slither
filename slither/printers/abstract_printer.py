import abc


class IncorrectPrinterInitialization(Exception):
    pass


class AbstractPrinter(metaclass=abc.ABCMeta):
    ARGUMENT = ''  # run the printer with slither.py --ARGUMENT
    HELP = ''  # help information

    WIKI = ''

    def __init__(self, slither, logger):
        self.slither = slither
        self.contracts = slither.contracts
        self.filename = slither.filename
        self.logger = logger

        if not self.HELP:
            raise IncorrectPrinterInitialization('HELP is not initialized {}'.format(self.__class__.__name__))

        if not self.ARGUMENT:
            raise IncorrectPrinterInitialization('ARGUMENT is not initialized {}'.format(self.__class__.__name__))

        if not self.WIKI:
            raise IncorrectPrinterInitialization('WIKI is not initialized {}'.format(self.__class__.__name__))

    def info(self, info):
        if self.logger:
            self.logger.info(info)

    @abc.abstractmethod
    def output(self, filename):
        """TODO Documentation"""
        return
