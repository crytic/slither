from slither.exceptions import SlitherError
from slither.tools.upgradeability.checks.abstract_checks import (
    AbstractCheck,
    CheckClassification,
)
from slither.utils.function import get_function_id


def get_signatures(c):
    functions = c.functions
    functions = [
        f.full_name
        for f in functions
        if f.visibility in ["public", "external"]
        and not f.is_constructor
        and not f.is_fallback
    ]

    variables = c.state_variables
    variables = [
        variable.name + "()"
        for variable in variables
        if variable.visibility in ["public"]
    ]
    return list(set(functions + variables))


def _get_function_or_variable(contract, signature):
    f = contract.get_function_from_signature(signature)

    if f:
        return f

    for variable in contract.state_variables:
        # Todo: can lead to incorrect variable in case of shadowing
        if variable.visibility in ["public"]:
            if variable.name + "()" == signature:
                return variable

    raise SlitherError(f"Function id checks: {signature} not found in {contract.name}")


class IDCollision(AbstractCheck):
    ARGUMENT = "function-id-collision"
    IMPACT = CheckClassification.HIGH

    HELP = "Functions ids collision"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#functions-ids-collisions"
    WIKI_TITLE = "Functions ids collisions"

    WIKI_DESCRIPTION = """
Detect function id collision between the contract and the proxy.
"""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    function gsf() public {
        // ...
    }
}

contract Proxy{
    function tgeo() public {
        // ...
    }
}
```
`Proxy.tgeo()` and `Contract.gsf()` have the same function id (0x67e43e43). 
As a result, `Proxy.tgeo()` will shadow Contract.gsf()`.  
"""

    WIKI_RECOMMENDATION = """
Rename the function. Avoid public functions in the proxy.
"""

    REQUIRE_CONTRACT = True
    REQUIRE_PROXY = True

    def _check(self):
        signatures_implem = get_signatures(self.contract)
        signatures_proxy = get_signatures(self.proxy)

        signatures_ids_implem = {get_function_id(s): s for s in signatures_implem}
        signatures_ids_proxy = {get_function_id(s): s for s in signatures_proxy}

        results = []

        for (k, _) in signatures_ids_implem.items():
            if k in signatures_ids_proxy:
                if signatures_ids_implem[k] != signatures_ids_proxy[k]:
                    implem_function = _get_function_or_variable(
                        self.contract, signatures_ids_implem[k]
                    )
                    proxy_function = _get_function_or_variable(
                        self.proxy, signatures_ids_proxy[k]
                    )

                    info = [
                        "Function id collision found: ",
                        implem_function,
                        " ",
                        proxy_function,
                        "\n",
                    ]
                    json = self.generate_result(info)
                    results.append(json)

        return results


class FunctionShadowing(AbstractCheck):
    ARGUMENT = "function-shadowing"
    IMPACT = CheckClassification.HIGH

    HELP = "Functions shadowing"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#functions-shadowing"
    WIKI_TITLE = "Functions shadowing"

    WIKI_DESCRIPTION = """
Detect function shadowing between the contract and the proxy.
"""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    function get() public {
        // ...
    }
}

contract Proxy{
    function get() public {
        // ...
    }
}
```
`Proxy.get` will shadow any call to `get()`. As a result `get()` is never executed in the logic contract and cannot be updated.
"""

    WIKI_RECOMMENDATION = """
Rename the function. Avoid public functions in the proxy.
"""

    REQUIRE_CONTRACT = True
    REQUIRE_PROXY = True

    def _check(self):
        signatures_implem = get_signatures(self.contract)
        signatures_proxy = get_signatures(self.proxy)

        signatures_ids_implem = {get_function_id(s): s for s in signatures_implem}
        signatures_ids_proxy = {get_function_id(s): s for s in signatures_proxy}

        results = []

        for (k, _) in signatures_ids_implem.items():
            if k in signatures_ids_proxy:
                if signatures_ids_implem[k] == signatures_ids_proxy[k]:
                    implem_function = _get_function_or_variable(
                        self.contract, signatures_ids_implem[k]
                    )
                    proxy_function = _get_function_or_variable(
                        self.proxy, signatures_ids_proxy[k]
                    )

                    info = [
                        "Function shadowing found: ",
                        implem_function,
                        " ",
                        proxy_function,
                        "\n",
                    ]
                    json = self.generate_result(info)
                    results.append(json)

        return results
