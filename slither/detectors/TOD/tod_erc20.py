from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.TOD.tod_tranfer import TODTransfer
from slither.slithir.operations.binary import Binary, BinaryType


class TODERC20(TODTransfer):
    ARGUMENT = "tod-erc20"
    HELP = "Transaction ordering dependency"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#tod-erc20"

    WIKI_TITLE = "Transaction ordering dependency -- erc20"
    WIKI_DESCRIPTION = "If the result of the pre-order transaction will have an impact on the result of this transaction, the miner may gain benefits by controlling the order in which the transactions are packaged."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
function approve(address spender, uint256 value) public returns (bool) {
    require(spender != address(0));
    _allowed[msg.sender][spender] = value;  //problem
    emit Approval(msg.sender, spender, value);
    return true;
}

function transferFrom(address from, address to, uint256 value) public returns (bool) {
    require(value <= _balances[from]);
    require(value <= _allowed[from][msg.sender]);
    require(to != address(0));

    _balances[from] = _balances[from].sub(value);
    _balances[to] = _balances[to].add(value);
    _allowed[from][msg.sender] = _allowed[from][msg.sender].sub(value);  //problem
    emit Transfer(from, to, value);
    return true;
}

```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "---To be added---"
    )

    def incorrect_erc20_interface(self, signature):
        (name, parameters, returnVars) = signature

        if name == "transfer" and parameters == ["address", "uint256"] and returnVars != ["bool"]:
            return True

        if (
            name == "transferFrom"
            and parameters == ["address", "address", "uint256"]
            and returnVars != ["bool"]
        ):
            return True

        if name == "approve" and parameters == ["address", "uint256"] and returnVars != ["bool"]:
            return True

        if (
            name == "allowance"
            and parameters == ["address", "address"]
            and returnVars != ["uint256"]
        ):
            return True

        if name == "balanceOf" and parameters == ["address"] and returnVars != ["uint256"]:
            return True

        if name == "totalSupply" and parameters == [] and returnVars != ["uint256"]:
            return True

        return False


    def detect_tod(self, c):
        if not c.is_possible_erc20():
            return []

        res = []

        for f in c.functions_declared:
            if not f.nodes:
                continue

            if self.incorrect_erc20_interface(f.signature):
                return []

            if f.name == "transferFrom":
                res.append(f)
                print(f.name)

            if f.name == "approve":
                res.append(f)
                print(f.name)
                
                for n in  f.nodes:
                    if (
                        n.contains_if() 
                        or n.contains_require_or_assert()
                    ):
                        if SolidityVariableComposed("msg.sender") in n.variables_read:

                            for ir in n.irs:
                                if (
                                    isinstance(ir, Binary) 
                                    and ir.type in [BinaryType.EQUAL, BinaryType.NOT_EQUAL]
                                    and ir.variable_right.name == "0"
                                ):
                                    res.pop()
                                    break

                    if f not in res:
                        break
        
        if len(res) == 2: 
            return [res] 
        else:  
             return []
