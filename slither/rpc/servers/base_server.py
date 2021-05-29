import inspect
import json
import traceback
from typing import Any, Optional, Union
from abc import ABC, abstractmethod
from slither.rpc.commands import all_commands
from slither.rpc.exceptions.api_exceptions import ApiError
from slither.rpc.commands.abstract_command import AbstractCommand
from slither.rpc.servers.server_state import ServerState
from enum import Enum

class JSONRPCError(Enum):
    # Defined by JSON RPC
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603

    # This is the start range of JSON RPC reserved error codes.
    # It doesn't denote a real error code. No LSP error codes should
    # be defined between the start and end range. For backwards
    # compatibility the `ServerNotInitialized` and the `UnknownErrorCode`
    # are left in the range.
    # @since 3.16.0
    jsonrpcReservedErrorRangeStart = -32099
    # @deprecated use jsonrpcReservedErrorRangeStart
    serverErrorStart = jsonrpcReservedErrorRangeStart;

    # Error code indicating that a server received a notification or
    # request before the server has received the `initialize` request.
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001


    # This is the start range of JSON RPC reserved error codes.
    # It doesn't denote a real error code.
    # @since 3.16.0
    jsonrpcReservedErrorRangeEnd = -32000
    # @deprecated use jsonrpcReservedErrorRangeEnd
    serverErrorEnd = jsonrpcReservedErrorRangeEnd

    # This is the start range of LSP reserved error codes.
    # It doesn't denote a real error code.
    # @since 3.16.0
    lspReservedErrorRangeStart = -32899

    ContentModified = -32801
    RequestCancelled = -32800

    # This is the end range of LSP reserved error codes.
    # It doesn't denote a real error code.
    # @since 3.16.0
    lspReservedErrorRangeEnd = -32800


class BaseServer(ABC):
    def __init__(self):
        self.server_state = ServerState()

    @abstractmethod
    def main_loop(self):
        """
        The main entry point for the server, which begins accepting and processing commands.
        :return: None
        """
        pass

    @staticmethod
    def _create_message(jsonrpc: str="2.0"):
        return {"jsonrpc": jsonrpc}

    @staticmethod
    def _create_request(id: int, method: str, params: Any):
        return {"id": id, "method": method, "params": params}

    @staticmethod
    def _create_success_response(id: Optional[str, int], result: Optional[Any]):
        return {"id": id, "result": result, "error": None}

    @staticmethod
    def _create_error_response(id: Optional[str, int], error_code: int, message: str, data: Optional[Any]):
        return {"id": id, "code": error_code, "message": message, "data": data}

    @staticmethod
    def _wrap_response(error: Optional[str], result: Any):
        # Verify the error provided is valid
        assert error is None or isinstance(error, str), f"Error must either be None or an error string."

        # Return our wrapped message, with no result if an error occurred.
        # TODO: Consider unifying this with JSON result wrapping in slither core in the future.
        return {
            'success': error is None,
            'error': error if error is not None else None,
            'result': result if error is None else None
        }

    def _on_command_received(self, command: dict) -> dict:
        """
        The main entry point for a received command. It determines which command handler to call and unpacks arguments.
        :param command_json_str: The JSON serialized RPC request string which represents a command to execute.
        :return: The JSON serialized RPC response to the provided JSON-RPC command.
        """

        try:
            # Obtain the command id from the request, as well as the associated command handler.
            command_id = command['command']
            command_args = command.get('args')
            # Enumerate all commands
            command_handlers = [getattr(all_commands, name) for name in dir(all_commands)]
            self._all_command_handlers = {ch.command_id: ch for ch in command_handlers if
                                          inspect.isclass(ch) and issubclass(ch, AbstractCommand)}
            command_handler = self._all_command_handlers.get(command_id)
            if command_handler is None:
                raise ApiError(f'The command \'{command_id}\' is not a valid RPC command.')

            # Determine if this command handler requires a previous analysis id.
            analysis_key = command.get('analysis')
            slither = None if analysis_key is None else self.server_state.get_analysis(analysis_key)
            if command_handler.requires_prior_analysis and slither is None:
                raise ApiError(f'The \'{command_id}\' command requires a previous analysis key/id to operate on, '
                               f'but one was not provided.')

            # Execute the command handler and obtain the response
            response = command_handler.execute(None, self.server_state, slither, command_args)

            # Return the JSON serialized response
            response = self._wrap_response(None, response)

        except Exception as err:
            # Any exceptions that are encountered will be returned in a JSON wrap.
            response = self._wrap_response(traceback.format_exc(), None)

        return response

