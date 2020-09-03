from slither.tools.upgradeability.checks.abstract_checks import (
    AbstractCheck,
    CheckClassification,
)


class WereConstant(AbstractCheck):
    ARGUMENT = "were-constant"
    IMPACT = CheckClassification.HIGH

    HELP = "Variables that should be constant"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#variables-that-should-be-constant"
    WIKI_TITLE = "Variables that should be constant"
    WIKI_DESCRIPTION = """
Detect state variables that should be `constant̀`.
"""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    uint variable1;
    uint constant variable2;
    uint variable3;
}

contract ContractV2{
    uint variable1;
    uint variable2;
    uint variable3;
}
```
Because `variable2` is not anymore a `constant`, the storage location of `variable3` will be different.
As a result, `ContractV2` will have a corrupted storage layout.
"""

    WIKI_RECOMMENDATION = """
Do not remove `constant` from a state variables during an update.
"""

    REQUIRE_CONTRACT = True
    REQUIRE_CONTRACT_V2 = True

    def _check(self):
        contract_v1 = self.contract
        contract_v2 = self.contract_v2

        state_variables_v1 = contract_v1.state_variables
        state_variables_v2 = contract_v2.state_variables

        v2_additional_variables = len(state_variables_v2) - len(state_variables_v1)
        if v2_additional_variables < 0:
            v2_additional_variables = 0

        # We keep two index, because we need to have them out of sync if v2
        # has additional non constant variables
        idx_v1 = 0
        idx_v2 = 0

        results = []
        while idx_v1 < len(state_variables_v1):

            state_v1 = contract_v1.state_variables[idx_v1]
            if len(state_variables_v2) <= idx_v2:
                break

            state_v2 = contract_v2.state_variables[idx_v2]

            if state_v2:
                if state_v1.is_constant:
                    if not state_v2.is_constant:
                        # If v2 has additional non constant variables, we need to skip them
                        if (
                            state_v1.name != state_v2.name or state_v1.type != state_v2.type
                        ) and v2_additional_variables > 0:
                            v2_additional_variables -= 1
                            idx_v2 += 1
                            continue
                        info = [state_v1, " was constant, but ", state_v2, "is not.\n"]
                        json = self.generate_result(info)
                        results.append(json)

            idx_v1 += 1
            idx_v2 += 1

        return results


class BecameConstant(AbstractCheck):
    ARGUMENT = "became-constant"
    IMPACT = CheckClassification.HIGH

    HELP = "Variables that should not be constant"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#variables-that-should-not-be-constant"
    WIKI_TITLE = "Variables that should not be constant"

    WIKI_DESCRIPTION = """
Detect state variables that should not be `constant̀`.
"""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    uint variable1;
    uint variable2;
    uint variable3;
}

contract ContractV2{
    uint variable1;
    uint constant variable2;
    uint variable3;
}
```
Because `variable2` is now a `constant`, the storage location of `variable3` will be different.
As a result, `ContractV2` will have a corrupted storage layout.
"""

    WIKI_RECOMMENDATION = """
Do not make an existing state variable `constant`.
"""

    REQUIRE_CONTRACT = True
    REQUIRE_CONTRACT_V2 = True

    def _check(self):
        contract_v1 = self.contract
        contract_v2 = self.contract_v2

        state_variables_v1 = contract_v1.state_variables
        state_variables_v2 = contract_v2.state_variables

        v2_additional_variables = len(state_variables_v2) - len(state_variables_v1)
        if v2_additional_variables < 0:
            v2_additional_variables = 0

        # We keep two index, because we need to have them out of sync if v2
        # has additional non constant variables
        idx_v1 = 0
        idx_v2 = 0

        results = []
        while idx_v1 < len(state_variables_v1):

            state_v1 = contract_v1.state_variables[idx_v1]
            if len(state_variables_v2) <= idx_v2:
                break

            state_v2 = contract_v2.state_variables[idx_v2]

            if state_v2:
                if state_v1.is_constant:
                    if not state_v2.is_constant:
                        # If v2 has additional non constant variables, we need to skip them
                        if (
                            state_v1.name != state_v2.name or state_v1.type != state_v2.type
                        ) and v2_additional_variables > 0:
                            v2_additional_variables -= 1
                            idx_v2 += 1
                            continue
                elif state_v2.is_constant:
                    info = [state_v1, " was not constant but ", state_v2, " is.\n"]
                    json = self.generate_result(info)
                    results.append(json)

            idx_v1 += 1
            idx_v2 += 1

        return results
