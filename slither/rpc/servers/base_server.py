import inspect
from typing import Any, IO, Optional, Type, Union
from slither.rpc.servers.server_context import ServerContext
from slither.rpc.io.jsonrpc_io import JsonRpcIo
from slither.rpc.commands.base_handler import BaseCommandHandler
from slither.rpc.commands import registered_handlers
from slither.rpc.errors.lsp_error_codes import LSPErrorCode

# Register all imported command handlers so we have a lookup of method name -> handler
COMMAND_HANDLERS = [getattr(registered_handlers, name) for name in dir(registered_handlers)]
COMMAND_HANDLERS = {ch.method_name: ch for ch in COMMAND_HANDLERS if inspect.isclass(ch) and ch != BaseCommandHandler and issubclass(ch, BaseCommandHandler)}


class BaseServer:
    running = False
    server_state: ServerContext = None
    io: JsonRpcIo = None

    def _main_loop(self, read_file_handle: IO, write_file_handle: IO):
        """
        The main entry point for the server, which begins accepting and processing commands on the given IO.
        :return: None
        """
        # Set our running state to True
        self.running = True

        # Reset server state and set our IO
        self.server_state = ServerContext()
        self.io = JsonRpcIo(read_file_handle, write_file_handle)

        # Continuously process messages.
        # TODO: This should use proper controls and not loop endlessly, potentially draining resources.
        while True:
            # Read a message, if there is none available, loop and wait for another.
            result = self.io.read()
            if result is None:
                continue

            # Process the underlying message
            (headers, message) = result
            self._on_message_received(message)

    def _on_message_received(self, message: Any) -> None:
        """
        The main dispatcher for a received message. It determines which command handler to call and unpacks arguments.
        :param message: The deserialized Language Server Protocol message received over JSON-RPC.
        :return: None
        """

        # TODO: Add appropriate error handling.
        # Verify the top level is a dictionary
        if not isinstance(message, dict):
            raise ValueError("The Language Server Protocol request message was not represented as a dictionary at the "
                             "top level.")

        # Try to fetch the method.
        message_id = message.get('id')
        method_name = message.get('method')
        if method_name is None:
            raise ValueError("Language Server Protocol request message did not contain a 'method' field.")
        elif not isinstance(method_name, str):
            raise ValueError("'method' field should be a string type.")

        # Fetch the relevant command handler and execute it if there is one.
        # If there is not, we simply ignore it.
        # TODO: Determine if there's an error code to send back for unsupported operation, etc.
        command_handler: Optional[Type[BaseCommandHandler]] = COMMAND_HANDLERS.get(method_name)
        if command_handler is not None:
            command_handler.process(message_id, message.get('params'))

    def send_response_message(self, message_id: Union[int, str, None], result: Any) -> None:
        """
        Sends a response back to the client in the event of a successful operation.
        :param message_id: The message id to respond to with this message.
        :param result: The resulting data to respond with in response to th
        :return: None
        """
        self.io.write({
            'jsonrpc': '2.0',
            'id': message_id,
            'result': result
        })

    def send_response_error(self, message_id: Union[int, str, None], error_code: LSPErrorCode, error_message: str,
                            error_data: Optional[Any]) -> None:
        """
        Sends an error response back to the client.
        :param message_id: The message id to respond to with this error.
        :param error_code: The error code to send across the wire.
        :param error_message: A short description of the error to be supplied to the client.
        :param error_data: Optional additional data which can be included with the error.
        :return: None
        """
        self.io.write({
            'jsonrpc': '2.0',
            'id': message_id,
            'error': {
                'code': error_code,
                'message': error_message,
                'data': error_data
            }
        })

    def send_notification_message(self, method_name: str, params: Optional[Any]) -> None:
        """
        Sends a notification to the client which targeting a specific method.
        :param method_name: The name of the method to invoke with this notification.
        :param params: The additional data provided to the underlying method.
        :return: None
        """
        self.io.write({
            'jsonrpc': '2.0',
            'method': method_name,
            'params': params
        })