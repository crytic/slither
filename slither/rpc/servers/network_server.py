import socket
from slither.rpc.servers.base_server import BaseServer


class NetworkServer(BaseServer):
    """
    Provides a TCP network socket interface for JSON-RPC
    """
    def __init__(self, port: int):
        # Set our port and initialize our socket
        self.port = port
        super().__init__()

    def start(self):
        """
        Starts the server to begin accepting and processing commands on the given IO.
        :return: None
        """
        # Create a socket to accept our connections
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind our socket
        # TODO: For now we only allow one connection, determine if we should allow multiple in the future.
        server_socket.bind(('127.0.0.1', self.port))
        server_socket.listen(1)

        # Accept connections and process with the underlying IO handlers.
        while True:
            # Accept a new connection, create a file handle which we will use to process our main loop
            connection_socket, address = server_socket.accept()
            connection_file_handle = connection_socket.makefile(mode='rw', encoding='utf-8')

            # Enter the main loop, this will reset state, so each connection will reset state.
            self._main_loop(connection_file_handle, connection_file_handle)