from enum import Enum
from slither.detectors.oracles.supported_oracles.oracle import Oracle

CHAINLINK_ORACLE_CALLS = ["latestRoundData","getRoundData",] 

class ChainlinkVars(Enum):
    ROUNDID = 0
    ANSWER = 1
    STARTEDAT = 2
    UPDATEDAT = 3
    ANSWEREDINROUND = 4


class ChainlinkOracle(Oracle):
    def __init__(self):
        super().__init__(CHAINLINK_ORACLE_CALLS)
        self.oracle_type = "Chainlink"
