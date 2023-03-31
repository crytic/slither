from typing import List

from slither.core.declarations import Contract
from slither.tools.upgradeability.checks.abstract_checks import (
    CheckClassification,
    AbstractCheck,
    CHECK_INFO,
)
from slither.utils.upgradeability import get_missing_vars
from slither.utils.output import Output


class MissingVariable(AbstractCheck):
    ARGUMENT = "missing-variables"
    IMPACT = CheckClassification.MEDIUM

    HELP = "Variable missing in the v2"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#missing-variables"
    WIKI_TITLE = "Missing variables"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect variables that were present in the original contracts but are not in the updated one.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract V1{
    uint variable1;
    uint variable2;
}

contract V2{
    uint variable1;
}
```
The new version, `V2` does not contain `variable1`. 
If a new variable is added in an update of `V2`, this variable will hold the latest value of `variable2` and
will be corrupted.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Do not change the order of the state variables in the updated contract.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True
    REQUIRE_CONTRACT_V2 = True

    def _check(self) -> List[Output]:
        contract1 = self.contract
        contract2 = self.contract_v2

        assert contract2
        missing = get_missing_vars(contract1, contract2)

        results = []
        for variable1 in missing:
            info: CHECK_INFO = ["Variable missing in ", contract2, ": ", variable1, "\n"]
            json = self.generate_result(info)
            results.append(json)

        return results


class DifferentVariableContractProxy(AbstractCheck):
    ARGUMENT = "order-vars-proxy"
    IMPACT = CheckClassification.HIGH

    HELP = "Incorrect vars order with the proxy"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#incorrect-variables-with-the-proxy"
    WIKI_TITLE = "Incorrect variables with the proxy"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect variables that are different between the contract and the proxy.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    uint variable1;
}

contract Proxy{
    address variable1;
}
```
`Contract` and `Proxy` do not have the same storage layout. As a result the storage of both contracts can be corrupted.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Avoid variables in the proxy. If a variable is in the proxy, ensure it has the same layout than in the contract.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True
    REQUIRE_PROXY = True

    def _contract1(self) -> Contract:
        return self.contract

    def _contract2(self) -> Contract:
        assert self.proxy
        return self.proxy

    def _check(self) -> List[Output]:
        contract1 = self._contract1()
        contract2 = self._contract2()
        order1 = [
            variable
            for variable in contract1.state_variables_ordered
            if not (variable.is_constant or variable.is_immutable)
        ]
        order2 = [
            variable
            for variable in contract2.state_variables_ordered
            if not (variable.is_constant or variable.is_immutable)
        ]

        results: List[Output] = []
        for idx, _ in enumerate(order1):
            if len(order2) <= idx:
                # Handle by MissingVariable
                return results

            variable1 = order1[idx]
            variable2 = order2[idx]
            if (variable1.name != variable2.name) or (variable1.type != variable2.type):
                info: CHECK_INFO = [
                    "Different variables between ",
                    contract1,
                    " and ",
                    contract2,
                    "\n",
                ]
                info += ["\t ", variable1, "\n"]
                info += ["\t ", variable2, "\n"]
                json = self.generate_result(info)
                results.append(json)

        return results


class DifferentVariableContractNewContract(DifferentVariableContractProxy):
    ARGUMENT = "order-vars-contracts"

    HELP = "Incorrect vars order with the v2"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#incorrect-variables-with-the-v2"
    WIKI_TITLE = "Incorrect variables with the v2"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect variables that are different between the original contract and the updated one.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    uint variable1;
}

contract ContractV2{
    address variable1;
}
```
`Contract` and `ContractV2` do not have the same storage layout. As a result the storage of both contracts can be corrupted.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Respect the variable order of the original contract in the updated contract.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True
    REQUIRE_PROXY = False
    REQUIRE_CONTRACT_V2 = True

    def _contract2(self) -> Contract:
        assert self.contract_v2
        return self.contract_v2


class ExtraVariablesProxy(AbstractCheck):
    ARGUMENT = "extra-vars-proxy"
    IMPACT = CheckClassification.MEDIUM

    HELP = "Extra vars in the proxy"
    WIKI = (
        "https://github.com/crytic/slither/wiki/Upgradeability-Checks#extra-variables-in-the-proxy"
    )
    WIKI_TITLE = "Extra variables in the proxy"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect variables that are in the proxy and not in the contract.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    uint variable1;
}

contract Proxy{
    uint variable1;
    uint variable2;
}
```
`Proxy` contains additional variables. A future update of `Contract` is likely to corrupt the proxy.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Avoid variables in the proxy. If a variable is in the proxy, ensure it has the same layout than in the contract.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True
    REQUIRE_PROXY = True

    def _contract1(self) -> Contract:
        return self.contract

    def _contract2(self) -> Contract:
        assert self.proxy
        return self.proxy

    def _check(self) -> List[Output]:
        contract1 = self._contract1()
        contract2 = self._contract2()
        order1 = [
            variable
            for variable in contract1.state_variables_ordered
            if not (variable.is_constant or variable.is_immutable)
        ]
        order2 = [
            variable
            for variable in contract2.state_variables_ordered
            if not (variable.is_constant or variable.is_immutable)
        ]

        results = []

        if len(order2) <= len(order1):
            return []

        idx = len(order1)

        while idx < len(order2):
            variable2 = order2[idx]
            info: CHECK_INFO = ["Extra variables in ", contract2, ": ", variable2, "\n"]
            json = self.generate_result(info)
            results.append(json)
            idx = idx + 1

        return results


class ExtraVariablesNewContract(ExtraVariablesProxy):
    ARGUMENT = "extra-vars-v2"

    HELP = "Extra vars in the v2"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#extra-variables-in-the-v2"
    WIKI_TITLE = "Extra variables in the v2"

    # region wiki_description
    WIKI_DESCRIPTION = """
Show new variables in the updated contract. 

This finding does not have an immediate security impact and is informative.
"""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Ensure that all the new variables are expected.
"""
    # endregion wiki_recommendation

    IMPACT = CheckClassification.INFORMATIONAL

    REQUIRE_CONTRACT = True
    REQUIRE_PROXY = False
    REQUIRE_CONTRACT_V2 = True

    def _contract2(self) -> Contract:
        assert self.contract_v2
        return self.contract_v2
