import logging

from slither.core.declarations import Function
from slither.slithir.operations import InternalCall
from slither.tools.upgradeability.checks.abstract_checks import (
    AbstractCheck,
    CheckClassification,
)
from slither.utils.colors import red

logger = logging.getLogger("Slither-check-upgradeability")


class MultipleInitTarget(Exception):
    pass


def _has_initiliaze_modifier(function: Function):
    if not function.modifiers:
        return False
    return any((m.name == "initializer") for m in function.modifiers)


def _get_initialize_functions(contract):
    return [
        f
        for f in contract.functions
        if (f.name == "initialize" or _has_initiliaze_modifier(f)) and f.is_implemented
    ]


def _get_all_internal_calls(function):
    all_ir = function.all_slithir_operations()
    return [
        i.function
        for i in all_ir
        if isinstance(i, InternalCall) and i.function_name == "initialize"
    ]


def _get_most_derived_init(contract):
    init_functions = [f for f in contract.functions if not f.is_shadowed and f.name == "initialize"]
    if len(init_functions) > 1:
        if len([f for f in init_functions if f.contract_declarer == contract]) == 1:
            return next((f for f in init_functions if f.contract_declarer == contract))
        raise MultipleInitTarget
    if init_functions:
        return init_functions[0]
    return None


class InitializablePresent(AbstractCheck):
    ARGUMENT = "init-missing"
    IMPACT = CheckClassification.INFORMATIONAL

    HELP = "Initializable is missing"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initializable-is-missing"
    WIKI_TITLE = "Initializable is missing"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect if a contract `Initializable` is present.
"""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Review manually the contract's initialization..
Consider using a `Initializable` contract to follow [standard practice](https://docs.openzeppelin.com/upgrades/2.7/writing-upgradeable).
"""
    # endregion wiki_recommendation

    def _check(self):
        initializable = self.contract.compilation_unit.get_contract_from_name("Initializable")
        if initializable is None:
            info = [
                "Initializable contract not found, the contract does not follow a standard initalization schema.\n"
            ]
            json = self.generate_result(info)
            return [json]
        return []


class InitializableInherited(AbstractCheck):
    ARGUMENT = "init-inherited"
    IMPACT = CheckClassification.INFORMATIONAL

    HELP = "Initializable is not inherited"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initializable-is-not-inherited"
    WIKI_TITLE = "Initializable is not inherited"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect if `Initializable` is inherited.
"""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Review manually the contract's initialization. Consider inheriting `Initializable`.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True

    def _check(self):
        initializable = self.contract.compilation_unit.get_contract_from_name("Initializable")
        # See InitializablePresent
        if initializable is None:
            return []
        if initializable not in self.contract.inheritance:
            info = [self.contract, " does not inherit from ", initializable, ".\n"]
            json = self.generate_result(info)
            return [json]
        return []


class InitializableInitializer(AbstractCheck):
    ARGUMENT = "initializer-missing"
    IMPACT = CheckClassification.INFORMATIONAL

    HELP = "initializer() is missing"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initializer-is-missing"
    WIKI_TITLE = "initializer() is missing"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect the lack of `Initializable.initializer()` modifier.
"""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Review manually the contract's initialization. Consider inheriting a `Initializable.initializer()` modifier.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True

    def _check(self):
        initializable = self.contract.compilation_unit.get_contract_from_name("Initializable")
        # See InitializablePresent
        if initializable is None:
            return []
        # See InitializableInherited
        if initializable not in self.contract.inheritance:
            return []

        initializer = self.contract.get_modifier_from_canonical_name("Initializable.initializer()")
        if initializer is None:
            info = ["Initializable.initializer() does not exist.\n"]
            json = self.generate_result(info)
            return [json]
        return []


class MissingInitializerModifier(AbstractCheck):
    ARGUMENT = "missing-init-modifier"
    IMPACT = CheckClassification.HIGH

    HELP = "initializer() is not called"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initializer-is-not-called"
    WIKI_TITLE = "initializer() is not called"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect if `Initializable.initializer()` is called.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Contract{
    function initialize() public{
        ///
    }
}

```
`initialize` should have the `initializer` modifier to prevent someone from initializing the contract multiple times.  
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Use `Initializable.initializer()`.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True

    def _check(self):
        initializable = self.contract.compilation_unit.get_contract_from_name("Initializable")
        # See InitializablePresent
        if initializable is None:
            return []
        # See InitializableInherited
        if initializable not in self.contract.inheritance:
            return []
        initializer = self.contract.get_modifier_from_canonical_name("Initializable.initializer()")
        # InitializableInitializer
        if initializer is None:
            return []

        results = []
        all_init_functions = _get_initialize_functions(self.contract)
        for f in all_init_functions:
            if initializer not in f.modifiers:
                info = [f, " does not call the initializer modifier.\n"]
                json = self.generate_result(info)
                results.append(json)
        return results


class MissingCalls(AbstractCheck):
    ARGUMENT = "missing-calls"
    IMPACT = CheckClassification.HIGH

    HELP = "Missing calls to init functions"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initialize-functions-are-not-called"
    WIKI_TITLE = "Initialize functions are not called"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect missing calls to initialize functions.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Base{
    function initialize() public{
        ///
    }
}
contract Derived is Base{
    function initialize() public{
        ///
    }
}

```
`Derived.initialize` does not call `Base.initialize` leading the contract to not be correctly initialized.  
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Ensure all the initialize functions are reached by the most derived initialize function.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True

    def _check(self):
        results = []

        # TODO: handle MultipleInitTarget
        try:
            most_derived_init = _get_most_derived_init(self.contract)
        except MultipleInitTarget:
            logger.error(red(f"Too many init targets in {self.contract}"))
            return []

        if most_derived_init is None:
            return []

        all_init_functions = _get_initialize_functions(self.contract)
        all_init_functions_called = _get_all_internal_calls(most_derived_init) + [most_derived_init]
        missing_calls = [f for f in all_init_functions if not f in all_init_functions_called]
        for f in missing_calls:
            info = ["Missing call to ", f, " in ", most_derived_init, ".\n"]
            json = self.generate_result(info)
            results.append(json)
        return results


class MultipleCalls(AbstractCheck):
    ARGUMENT = "multiple-calls"
    IMPACT = CheckClassification.HIGH

    HELP = "Init functions called multiple times"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initialize-functions-are-called-multiple-times"
    WIKI_TITLE = "Initialize functions are called multiple times"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detect multiple calls to a initialize function.
"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Base{
    function initialize(uint) public{
        ///
    }
}
contract Derived is Base{
    function initialize(uint a, uint b) public{
        initialize(a);
    }
}

contract DerivedDerived is Derived{
    function initialize() public{
        initialize(0);
        initialize(0, 1 );
    }
}

```
`Base.initialize(uint)` is called two times in `DerivedDerived.initiliaze` execution, leading to a potential corruption.
"""
    # endregion wiki_exploit_scenario

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Call only one time every initialize function.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True

    def _check(self):
        results = []

        # TODO: handle MultipleInitTarget
        try:
            most_derived_init = _get_most_derived_init(self.contract)
        except MultipleInitTarget:
            # Should be already reported by MissingCalls
            # logger.error(red(f'Too many init targets in {self.contract}'))
            return []

        if most_derived_init is None:
            return []

        all_init_functions_called = _get_all_internal_calls(most_derived_init) + [most_derived_init]
        double_calls = list(
            {f for f in all_init_functions_called if all_init_functions_called.count(f) > 1}
        )
        for f in double_calls:
            info = [f, " is called multiple times in ", most_derived_init, ".\n"]
            json = self.generate_result(info)
            results.append(json)

        return results


class InitializeTarget(AbstractCheck):
    ARGUMENT = "initialize-target"
    IMPACT = CheckClassification.INFORMATIONAL

    HELP = "Initialize function that must be called"
    WIKI = "https://github.com/crytic/slither/wiki/Upgradeability-Checks#initialize-function"
    WIKI_TITLE = "Initialize function"

    # region wiki_description
    WIKI_DESCRIPTION = """
Show the function that must be called at deployment. 

This finding does not have an immediate security impact and is informative.
"""
    # endregion wiki_description

    # region wiki_recommendation
    WIKI_RECOMMENDATION = """
Ensure that the function is called at deployment.
"""
    # endregion wiki_recommendation

    REQUIRE_CONTRACT = True

    def _check(self):

        # TODO: handle MultipleInitTarget
        try:
            most_derived_init = _get_most_derived_init(self.contract)
        except MultipleInitTarget:
            # Should be already reported by MissingCalls
            # logger.error(red(f'Too many init targets in {self.contract}'))
            return []

        if most_derived_init is None:
            return []

        info = [
            self.contract,
            " needs to be initialized by ",
            most_derived_init,
            ".\n",
        ]
        json = self.generate_result(info)
        return [json]
