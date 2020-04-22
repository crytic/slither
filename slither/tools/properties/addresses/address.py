from typing import Optional

# These are the default values in truffle
# https://www.trufflesuite.com/docs/truffle/getting-started/using-truffle-develop-and-the-console
OWNER_ADDRESS = "0x627306090abaB3A6e1400e9345bC60c78a8BEf57"
USER_ADDRESS = "0xf17f52151EbEF6C7334FAD080c5704D77216b732"
ATTACKER_ADDRESS = "0xC5fdf4076b8F3A5357c5E395ab970B5B54098Fef"


class Addresses:

    def __init__(self, owner: Optional[str] = None, user: Optional[str] = None, attacker: Optional[str] = None):
        self.owner = owner if owner else OWNER_ADDRESS
        self.user = user if user else USER_ADDRESS
        self.attacker = attacker if attacker else ATTACKER_ADDRESS
