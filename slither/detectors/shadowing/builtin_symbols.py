"""
Module detecting reserved keyword shadowing
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class BuiltinSymbolShadowing(AbstractDetector):
    """
    Built-in symbol shadowing
    """

    ARGUMENT = "shadowing-builtin"
    HELP = "Built-in symbol shadowing"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#builtin-symbol-shadowing"

    WIKI_TITLE = "Builtin Symbol Shadowing"
    WIKI_DESCRIPTION = "Detection of shadowing built-in symbols using local variables, state variables, functions, modifiers, or events."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
pragma solidity ^0.4.24;

contract Bug {
    uint now; // Overshadows current time stamp.

    function assert(bool condition) public {
        // Overshadows built-in symbol for providing assertions.
    }

    function get_next_expiration(uint earlier_time) private returns (uint) {
        return now + 259200; // References overshadowed timestamp.
    }
}
```
`now` is defined as a state variable, and shadows with the built-in symbol `now`. The function `assert` overshadows the built-in `assert` function. Any use of either of these built-in symbols may lead to unexpected results."""

    WIKI_RECOMMENDATION = "Rename the local variables, state variables, functions, modifiers, and events that shadow a builtin symbol."

    SHADOWING_FUNCTION = "function"
    SHADOWING_MODIFIER = "modifier"
    SHADOWING_LOCAL_VARIABLE = "local variable"
    SHADOWING_STATE_VARIABLE = "state variable"
    SHADOWING_EVENT = "event"

    # Reserved keywords reference: https://solidity.readthedocs.io/en/v0.5.2/units-and-global-variables.html
    BUILTIN_SYMBOLS = [
        "assert",
        "require",
        "revert",
        "block",
        "blockhash",
        "gasleft",
        "msg",
        "now",
        "tx",
        "this",
        "addmod",
        "mulmod",
        "keccak256",
        "sha256",
        "sha3",
        "ripemd160",
        "ecrecover",
        "selfdestruct",
        "suicide",
        "abi",
        "fallback",
        "receive",
    ]

    # https://solidity.readthedocs.io/en/v0.5.2/miscellaneous.html#reserved-keywords
    RESERVED_KEYWORDS = [
        "abstract",
        "after",
        "alias",
        "apply",
        "auto",
        "case",
        "catch",
        "copyof",
        "default",
        "define",
        "final",
        "immutable",
        "implements",
        "in",
        "inline",
        "let",
        "macro",
        "match",
        "mutable",
        "null",
        "of",
        "override",
        "partial",
        "promise",
        "reference",
        "relocatable",
        "sealed",
        "sizeof",
        "static",
        "supports",
        "switch",
        "try",
        "type",
        "typedef",
        "typeof",
        "unchecked",
    ]

    def is_builtin_symbol(self, word):
        """Detects if a given word is a built-in symbol.

        Returns:
            boolean: True if the given word represents a built-in symbol."""

        return word in self.BUILTIN_SYMBOLS or word in self.RESERVED_KEYWORDS

    def detect_builtin_shadowing_locals(self, function_or_modifier):
        """Detects if local variables in a given function/modifier are named after built-in symbols.
            Any such items are returned in a list.

        Returns:
            list of tuple: (type, definition, local variable parent)"""

        results = []
        for local in function_or_modifier.variables:
            if self.is_builtin_symbol(local.name):
                results.append((self.SHADOWING_LOCAL_VARIABLE, local))
        return results

    def detect_builtin_shadowing_definitions(self, contract):
        """Detects if functions, access modifiers, events, state variables, or local variables are named after built-in
            symbols. Any such definitions are returned in a list.

        Returns:
            list of tuple: (type, definition, [local variable parent])"""

        result = []

        # Loop through all functions, modifiers, variables (state and local) to detect any built-in symbol keywords.
        for function in contract.functions_declared:
            if self.is_builtin_symbol(function.name):
                if function.is_fallback or function.is_receive:
                    continue
                result.append((self.SHADOWING_FUNCTION, function))
            result += self.detect_builtin_shadowing_locals(function)
        for modifier in contract.modifiers_declared:
            if self.is_builtin_symbol(modifier.name):
                result.append((self.SHADOWING_MODIFIER, modifier))
            result += self.detect_builtin_shadowing_locals(modifier)
        for variable in contract.state_variables_declared:
            if self.is_builtin_symbol(variable.name):
                result.append((self.SHADOWING_STATE_VARIABLE, variable))
        for event in contract.events_declared:
            if self.is_builtin_symbol(event.name):
                result.append((self.SHADOWING_EVENT, event))

        return result

    def _detect(self):
        """Detect shadowing of built-in symbols

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """

        results = []
        for contract in self.contracts:
            shadows = self.detect_builtin_shadowing_definitions(contract)
            if shadows:
                for shadow in shadows:
                    # Obtain components
                    shadow_type = shadow[0]
                    shadow_object = shadow[1]

                    info = [
                        shadow_object,
                        f' ({shadow_type}) shadows built-in symbol"\n',
                    ]

                    res = self.generate_result(info)
                    results.append(res)

        return results
