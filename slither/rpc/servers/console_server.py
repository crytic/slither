import sys
from slither.rpc.servers.base_server import BaseServer


class ConsoleServer(BaseServer):
    """
    Provides a console (stdin/stdout) interface for JSON-RPC
    """

    def start(self):
        """
        Starts the server to begin accepting and processing commands on the given IO.
        :return: None
        """
        # Start our server using stdio for the provided IO handles.
        self._main_loop(sys.stdin, sys.stdout)