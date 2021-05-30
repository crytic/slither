from abc import ABC, abstractmethod
from typing import Any, Union


class BaseCommandHandler(ABC):
    """
    Represents a handler for a command provided over the Language Server Protocol.
    """

    @staticmethod
    @abstractmethod
    def method_name():
        """
        The name of the method which this command handler handles. This should be unique per handler.
        Handlers which are custom or client/server-specific should be prefixed with '$/'
        :return: The name of the method which this command handler handles.
        """
        pass

    @staticmethod
    @abstractmethod
    def process(message_id: Union[int, str, None], params: Any):
        pass
