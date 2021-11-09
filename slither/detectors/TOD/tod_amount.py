from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations import SolidityVariableComposed
from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.TOD.tod_tranfer import TODTransfer
from slither.slithir.variables.constant import Constant


class TODAmount(TODTransfer):
    ARGUMENT = "tod-amount"
    HELP = "Transaction ordering dependency"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#tod-amount"

    WIKI_TITLE = "Transaction ordering dependency -- amount"
    WIKI_DESCRIPTION = "If the result of the pre-order transaction will have an impact on the result of this transaction, the miner may gain benefits by controlling the order in which the transactions are packaged."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity

    function setPrice(uint newPrice) public payable {
        require(msg.sender == owner);
        price = new_price;
    }

    function sellTokens() public {
        uint amount = balances[msg.sender];
        balances[msg.sender] = 0;
        msg.sender.transfer(amount * price);
    }
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "---To be added---"
    )

    # pylint: disable=too-many-nested-blocks,too-many-branches
    def detect_tod(self, c):
        state_var = {}
        tod = {}

        for f in c.functions_declared:
            if not f.nodes:
                continue

            if f.is_constructor:
                continue

            if f.is_protected():
                for var in f.all_state_variables_written():
                    if var not in state_var:
                        state_var[var] = [f]
                    elif f not in state_var[var]:
                        state_var[var] += [f]
                continue
           
            for n in f.nodes:
                sender = self.is_transfer(n)

                if sender:
                    for (dest, var) in sender:
                        if dest != SolidityVariableComposed("msg.sender"):
                            continue
                        
                        if isinstance(var, Constant):
                            continue

                        if is_dependent(var, SolidityVariableComposed("msg.value"), f,):
                            continue

                        if var in c.variables:
                            continue

                        for st_v in c.variables:
                            if is_dependent(var, st_v, f,):
                                if st_v in f.all_state_variables_written():
                                    continue
                                
                                if st_v not in tod:
                                    tod[st_v] = [f]

                                elif f not in tod[st_v]:
                                    tod[st_v]  += [f]

        res = []
        for t in tod:
            if t in state_var:
                res.append(state_var[t]+tod[t])

        return res
         
