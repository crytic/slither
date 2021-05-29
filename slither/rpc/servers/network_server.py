from abc import ABC
from slither.rpc.servers.base_server import BaseServer


class NetworkServer(BaseServer):
    """
    Provides a network socket interface for JSON-RPC
    """
    def __init__(self):
        pass

    def command_received(self, command_str):
        pass
