from slither.slithir.variables.reference import ReferenceVariable
from slither.core.declarations import Function, SolidityVariableComposed
from slither.detectors.abstract_detector import AbstractDetector,DetectorClassification
from slither.slithir.operations import Binary, BinaryType, HighLevelCall, LowLevelCall, Send, Transfer
from slither.slithir.variables.constant import Constant


class TODTransfer(AbstractDetector):
    ARGUMENT = "tod-transfer"
    HELP = "Transaction ordering dependency"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#tod-transfer"

    WIKI_TITLE = "Transaction ordering dependency -- transfer"
    WIKI_DESCRIPTION = "If the result of the pre-order transaction will have an impact on the result of this transaction, the miner may gain benefits by controlling the order in which the transactions are packaged."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity

    function setReward() public payable {
        require (!claimed);

        require(msg.sender == owner;
        owner.transfer(reward);
        reward = msg.value;
    }

    function claimReward(uint256 submission) public {
        require (!claimed);
        require(submission < 10);

        msg.sender.transfer(reward);
        claimed = true;
    }
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "---To be added---"
    )

    def is_transfer(self, n):
        sender = []
        for ir in n.irs:
            if isinstance(ir, (HighLevelCall, LowLevelCall, Transfer, Send)):
                if isinstance(ir, (HighLevelCall)):
                    if isinstance(ir.function, Function):
                        if ir.function.full_name == "transferFrom(address,address,uint256)":
                            sender.append((ir.arguments[1], ir.arguments[2]))
                    continue

                if ir.call_value is None:
                    continue
                
                sender.append((ir.destination, ir.call_value))

        return sender


    # pylint: disable=too-many-nested-blocks,too-many-branches
    def detect_tod(self, c):
        state_var = {}
        tod = {}
        tod["null"] = []

        for f in c.functions_declared:
            if not f.nodes:
                continue

            if f.is_constructor:
                continue

            limit = False
            for n in f.nodes:
                sender = self.is_transfer(n)

                if limit and sender:
                    for (dest, var) in sender:
                        if var == SolidityVariableComposed("msg.value"):
                            continue
                        
                        while isinstance(var, ReferenceVariable):
                            var = var.points_to
                        
                        if f.is_protected():
                            if not isinstance(var, Constant) and var in n.state_variables_read:
                                if var not in state_var:
                                    state_var[var] = [f]
                                elif f not in state_var[var]:
                                    state_var[var] += [f]

                        elif dest == SolidityVariableComposed("msg.sender"):
                            if var in n.state_variables_read:
                                if (
                                    var in state_var 
                                    and f in state_var[var]
                                ):
                                    state_var[var].pop()
                                    continue

                                if var not in tod:
                                    tod[var] = [f]
                                elif f not in tod[var]:
                                    tod[var] += [f]

                            if isinstance(var, Constant) :
                                if f not in tod["null"]:
                                    tod["null"] += [[f]]

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

                for var in n.state_variables_written:
                    if var not in state_var:
                        state_var[var] = [f]
                    elif f not in state_var[var]:
                        state_var[var] += [f]

        res = tod["null"]
        for t in tod:
            if not tod[t]:
                continue
            
            if t in state_var and len(state_var[t]) != 0:
                res.append(tod[t]+state_var[t])

        return res
        

    def _detect(self):
        results = []
        for c in self.contracts:
            functions = self.detect_tod(c)

            if functions:
                for function in functions:
                    info = ["The following functions have TOD vulnerabilities :","\n",]

                    for f in function:
                        info += ["\t- ",f,"\n",]
                    
                    json = self.generate_result(info)
                    results.append(json)

        return results
