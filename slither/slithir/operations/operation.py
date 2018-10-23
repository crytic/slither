import abc
from slither.core.context.context import Context

class AbstractOperation(abc.ABC):

    @property
    @abc.abstractmethod
    def read(self):
        """
            Return the list of variables READ
        """
        pass

    @property
    @abc.abstractmethod
    def used(self):
        """
            Return the list of variables used
        """
        pass

class Operation(Context, AbstractOperation):

    @property
    def used(self):
        """
            By default used is all the variables read
        """
        return self.read
