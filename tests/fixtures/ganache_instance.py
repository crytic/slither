# pylint: disable=too-few-public-methods
class GanacheInstance:
    def __init__(self, provider: str, eth_address: str, eth_privkey: str):
        self.provider = provider
        self.eth_address = eth_address
        self.eth_privkey = eth_privkey
