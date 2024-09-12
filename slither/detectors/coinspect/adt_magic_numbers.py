from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import Function
from slither.core.expressions import Literal
from slither.core.solidity_types import ElementaryType

class CoinspectMagicNumberDetector(AbstractDetector):
    """
    Detector to find magic numbers in smart contracts
    """

    ARGUMENT = "magic-numbers"
    HELP = "Usage of magic numbers"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#magic-numbers"
    WIKI_TITLE = "Magic Numbers"
    WIKI_DESCRIPTION = "This detector identifies magic numbers in the contract."
    WIKI_EXPLOIT_SCENARIO = "Using magic numbers can lead to errors and reduce code readability."
    WIKI_RECOMMENDATION = "Use named constants instead of magic numbers."
   
    def _is_integer_type(self, type_str):
        """
        Check if the given type string represents an integer type
        """
        return type_str.startswith('uint') or type_str.startswith('int')

    def _find_magic_numbers(self, expression):
        """
        Recursively search for magic numbers in an expression
        """
        magic_numbers = []

        if expression is None:
            return magic_numbers

        if isinstance(expression, Literal):
            if isinstance(expression.type, ElementaryType):
                if self._is_integer_type(expression.type.type):
                    # Exclude common numbers like 0, 1, 2 which are often used legitimately
                    if expression.value not in ['0', '1', '2']:
                        magic_numbers.append(expression)
        
        # Check if the expression has sub-expressions
        if hasattr(expression, 'expressions'):
            for sub_expr in expression.expressions:
                magic_numbers.extend(self._find_magic_numbers(sub_expr))
        
        return magic_numbers

    def _detect_magic_numbers(self, function: Function) -> list:
        """
        Detect magic numbers in a function
        """
        results = []
        
        for node in function.nodes: 
            if node.expression:
                magic_numbers = self._find_magic_numbers(node.expression)
                for magic_number in magic_numbers:
                    info = [

                        f"Magic number found in {function.canonical_name}",
                        f"\t- {magic_number} \n"
                    ]
                    results.append(info)
        return results

    def _detect(self) -> list:
        """
        Detect magic numbers in the contract
        """
        results = []
        for contract in self.contracts:
            for function in contract.functions_declared + contract.modifiers_declared:
                # Skip global declarations of state variables
                if (function.is_constructor_variables):
                    continue

                magic_numbers = self._detect_magic_numbers(function)
                for magic_number in magic_numbers:
                    results.append(self.generate_result(magic_number))
        return results