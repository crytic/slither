"""
Module detecting voting amplification.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class VotingAmplification(AbstractDetector):
    """
    Detect voting-amplification
    """

    ARGUMENT = (
        "voting-amplification"  # slither will launch the detector with slither.py --mydetector
    )
    HELP = "There are flaws of on-chain governance implementation"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/trailofbits/slither/wiki/Detector-Documentation#voting-amplification"
    WIKI_TITLE = "VOTING_AMPLIFICATION"
    WIKI_DESCRIPTION = "VOTING_AMPLIFICATION"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
library SafeMath {
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a);
        uint256 c = a - b;

        return c;
    }

    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);

        return c;
    }
}

contract A {
    using SafeMath for uint;

    struct Checkpoint {
        uint32 fromBlock;
        uint256 votes;
    }
    mapping (address => uint256) _balances;
    mapping (address => mapping (address => uint256)) _allowed;
    mapping (address => address) public delegates;
    mapping (address => mapping (uint32 => Checkpoint)) checkpoints;
    mapping (address => uint32) numCheckpoints;
    // ...

    function _transfer(address from, address to, uint256 value) internal {
        require(to != address(0));
        _balances[from] = _balances[from].sub(value);
        _balances[to] = _balances[to].add(value);
    }

    function allowance(address owner, address spender) public view returns (uint256) {
        return _allowed[owner][spender];
    }

    function _approve(address owner, address spender, uint256 value) internal {
        require(spender != address(0));
        require(owner != address(0));

        _allowed[owner][spender] = value;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        _transfer(from, to, value);
        _approve(from, msg.sender, allowance(from, msg.sender).sub(value));
        _moveDelegates(delegates[msg.sender], delegates[to], value); // vulnerable point
        return true;
    }

    function _writeCheckpoint(address delegatee, uint32 nCheckpoints, uint256 oldVotes, uint256 newVotes) internal {
        uint32 blockNumber = safe32(block.number, "Xcn::_writeCheckpoint: block number exceeds 32 bits");

        if (nCheckpoints > 0 && checkpoints[delegatee][nCheckpoints - 1].fromBlock == blockNumber) {
            checkpoints[delegatee][nCheckpoints - 1].votes = newVotes;
        } else {
            checkpoints[delegatee][nCheckpoints] = Checkpoint(blockNumber, newVotes);
            numCheckpoints[delegatee] = nCheckpoints + 1;
        }   
    }

    function _moveDelegates(address srcRep, address dstRep, uint256 amount) internal {
        if (srcRep != dstRep && amount > 0) {
            if (srcRep != address(0)) {
                uint32 srcRepNum = numCheckpoints[srcRep];
                uint256 srcRepOld = srcRepNum > 0 ? checkpoints[srcRep][srcRepNum - 1].votes : 0;
                uint256 srcRepNew = srcRepOld.sub(amount);
                _writeCheckpoint(srcRep, srcRepNum, srcRepOld, srcRepNew);
            }

            if (dstRep != address(0)) {
                uint32 dstRepNum = numCheckpoints[dstRep];
                uint256 dstRepOld = dstRepNum > 0 ? checkpoints[dstRep][dstRepNum - 1].votes : 0;
                uint256 dstRepNew = dstRepOld.add(amount);
                _writeCheckpoint(dstRep, dstRepNum, dstRepOld, dstRepNew);
            }
        }
    }

    function safe32(uint n, string memory errorMessage) internal pure returns (uint32) {
        require(n < 2**32, errorMessage);
        return uint32(n);
    }
    // ...
}
```
https://etherscan.io/address/0xa2cd3d43c775978a96bdbf12d733d5a1ed94fb18#code#L533

When defi project just copy&paste code with vulnerability, the above pattern appears.
"""
    WIKI_RECOMMENDATION = "Do not copy&paste code with vulnerabilities."

    def detect_moving_exist(self, contracts):
        result = []
        delegates = "moveDelegate"

        for contract in contracts:
            for func in contract.functions:
                if any(delegates.lower() in callee.name.lower() for callee in func.internal_calls):

                    for node in func.nodes:
                        for _exp in node._internal_calls_as_expressions:
                            exp = str(_exp).lower()
                            if "moveDelegate".lower() in exp:
                                arg = exp[exp.find("(") : -1].split(",")
                                # 1. In calling moveDelegates(), improper position of from and to.
                                # 2. In burn(), moveDelegate(0, to) or moveDelegate(0, from).
                                # 3. In transferFrom(), moveDelegate(msg.sender, to).
                                if len(arg) == 3:
                                    if "to" in arg[0].lower() and "from" in arg[1].lower():
                                        result.append(func)

                                    if "burn" in func.name.lower() and (
                                        "to" in arg[1].lower() or "from" in arg[1].lower()
                                    ):
                                        result.append(func)

                                    if "transferFrom".lower() in func.name.lower():
                                        result.append(func)
        return result

    def _detect(self):

        results = []

        res = self.detect_moving_exist(self.contracts)
        for rep in res:
            info = [
                "Voting amplification found in ",
                rep,
                "\n",
            ]
            res = self.generate_result(info)
            results.append(res)
        return results
