from typing import Any, IO
from slither.rpc.servers.server_state import ServerState
from slither.rpc.io.jsonrpc_io import JsonRpcIo


class BaseServer:
    running = False
    server_state: ServerState = None
    io: JsonRpcIo = None

    def _main_loop(self, read_file_handle: IO, write_file_handle: IO):
        """
        The main entry point for the server, which begins accepting and processing commands on the given IO.
        :return: None
        """
        # Set our running state to True
        running = True

        # Reset server state and set our IO
        self.server_state = ServerState()
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
        self.io.write({"receivedMessage": message})

