import json
import sys
from abc import ABC
from slither.rpc.servers.base_server import BaseServer


class ConsoleServer(BaseServer):
    """
    Provides a console (stdin/stdout) interface for JSON-RPC
    """

    def __init__(self):
        # Use the common base constructor
        super().__init__()

    def main_loop(self):
        """
        The main entry point for the console server. Commands are read from stdin and responses are sent over stdout.
        :return: None
        """
        # Repetitively read commands and process them
        while True:
            # TODO: Disable stdout output from command processing, in case slither prints something.

            # Parse the supposed JSON-RPC command from stdin
            command = json.loads(sys.stdin.readline())
            sequence_number = command.get('sequence')
            if sequence_number is None:
                raise ValueError("Console RPC server requires a sequence number to respond to commands.")

            # Process our command and obtain the response
            response = super()._on_command_received(command)
            response['sequence'] = sequence_number

            # TODO: Re-enable stdout (read previous TODO)

            # Print the response
            sys.stdout.write(json.dumps(response))
            sys.stdout.flush()
