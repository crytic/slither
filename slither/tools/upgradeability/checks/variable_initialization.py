from slither.tools.upgradeability.checks.abstract_checks import CheckClassification, AbstractCheck


class VariableWithInit(AbstractCheck):
    ARGUMENT = "variables-initialized"
    IMPACT = CheckClassification.HIGH

    HELP = "State variables with an initial value"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#state-variable-initialized"
    WIKI_TITLE = "State variable initialized"

    WIKI_DESCRIPTION = """
Detect state variables that are initialized.
"""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    uint variable = 10;
}
```
Using `Contract` will the delegatecall proxy pattern will lead `variable` to be 0 when called through the proxy.
"""

    WIKI_RECOMMENDATION = """
Using initialize functions to write initial values in state variables.
"""

    REQUIRE_CONTRACT = True

    def _check(self):
        results = []
        for s in self.contract.state_variables:
            if s.initialized and not s.is_constant:
                info = [s, " is a state variable with an initial value.\n"]
                json = self.generate_result(info)
                results.append(json)
        return results
