from typing import Any, Optional
from abc import ABC, abstractmethod
from slither import Slither
from slither.rpc.servers.server_state import ServerState

class AbstractCommand(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def command_id(self) -> str:
        """
        Represents a unique identifier for a JSON-RPC command.
        :return: Returns the unique identifier for the JSON-RPC command.
        """
        pass

    @property
    @abstractmethod
    def requires_prior_analysis(self) -> str:
        """
        Indicates whether the command requires a reference to a previous slither analysis.
        :return: Returns a value indicating whether a reference to a previous slither analysis is required.
        """
        pass

    @abstractmethod
    def execute(self, server_state: ServerState, slither: Optional[Slither], args: Optional[dict]) -> Any:
        """
        Executes a command given the provided arguments.
        :param server_state: The RPC server state object for the RPC server calling this command handler..
        :param slither: An optional analysis object which was tied to this command/request. It is ignored for this
        command.
        :param args: Command handler specific arguments provided within a dictionary.
        :return: Returns a command handler specific response, must be JSON serializable.
        """
        pass
