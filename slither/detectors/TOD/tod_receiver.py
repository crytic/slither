from slither.core.declarations.solidity_variables  import SolidityVariableComposed
from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.TOD.tod_tranfer import TODTransfer
from slither.slithir.operations import Assignment, Binary, BinaryType
from slither.slithir.variables import ReferenceVariable


class TODReciver(TODTransfer):
    ARGUMENT = "tod-receiver"
    HELP = "Transaction ordering dependency"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#tod-receiver"

    WIKI_TITLE = "Transaction ordering dependency -- receiver"
    WIKI_DESCRIPTION = "If the result of the pre-order transaction will have an impact on the result of this transaction, the miner may gain benefits by controlling the order in which the transactions are packaged."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity

    function play(bytes32 guess) public{
       if (keccak256(abi.encode(guess)) == keccak256(abi.encode('hello'))) {
            winner = msg.sender;
        }
    }

    function getReward() payable public{
       winner.transfer(msg.value);
    }

```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "---To be added---"
    )


    # pylint: disable=too-many-nested-blocks,too-many-branches
    def detect_tod(self, c):
        state_var_check = {}
        tod = {}

        for f in c.functions_declared:

            if not f.nodes:
                continue

            if f.is_constructor:
                continue

            limit = False
            for n in f.nodes:
                sender = self.is_transfer(n)
                if sender:
                    for (dest, var) in sender:
                        while isinstance(dest, ReferenceVariable):
                            dest = dest.points_to

                        if dest not in n.state_variables_read:
                            continue
                        
                        if var == SolidityVariableComposed("msg.value") or f.is_protected():
                            if (
                                dest in state_var_check
                                and f in state_var_check[dest]
                            ):
                                state_var_check[dest].pop()
                                continue

                            if dest not in tod:
                                tod[dest] = [f]

                            elif f not in tod[dest]:
                                tod[dest] +=  [f]

                if n.contains_if() or n.contains_require_or_assert():
                    limit = True

                    """ don't report msg.sender/msg.value """
                    if n.solidity_variables_read:
                        limit = False

                    """ don't report +,-,*,/ """
                    if n.local_variables_read:
                        for ir in n.irs:
                            if isinstance(ir, Binary):
                                if not BinaryType.return_bool(ir.type):
                                    limit = False
                                    break

                """before winner=msg.sender must have condition node"""
                if not limit:
                    continue

                if not n.state_variables_written:
                    continue

                for ir in n.irs:
                    if not isinstance(ir, Assignment):
                        continue

                    if ir.rvalue != SolidityVariableComposed("msg.sender"):
                        continue
                    
                    left = ir.lvalue
                    while isinstance(left, ReferenceVariable):
                        left = left.points_to

                    if left not in n.state_variables_written:
                        continue
                    
                    if left not in state_var_check:
                        state_var_check[left] = [f]
                    elif f not in state_var_check[left]:
                        state_var_check[left] += [f]

        res = []
        for t in tod:
            if not tod[t]:
                continue
            if t in state_var_check and len(state_var_check[t]) != 0:
                res.append(tod[t]+state_var_check[t])

        return res
