"""
Module detecting the incorrect use of unary expressions
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.visitors.expression.expression import ExpressionVisitor
from slither.core.expressions.unary_operation import UnaryOperationType, UnaryOperation


class InvalidUnaryExpressionDetector(ExpressionVisitor):
    def _post_assignement_operation(self, expression):
        if isinstance(expression.expression_right, UnaryOperation):
            if expression.expression_right.type == UnaryOperationType.PLUS_PRE:
                # This is defined in ExpressionVisitor but pylint
                # Seems to think its not
                # pylint: disable=attribute-defined-outside-init
                self._result = True


class InvalidUnaryStateVariableDetector(ExpressionVisitor):
    def _post_unary_operation(self, expression):
        if expression.type == UnaryOperationType.PLUS_PRE:
            # This is defined in ExpressionVisitor but pylint
            # Seems to think its not
            # pylint: disable=attribute-defined-outside-init
            self._result = True


class IncorrectUnaryExpressionDetection(AbstractDetector):
    """
    Incorrect Unary Expression detector
    """

    ARGUMENT = "incorrect-unary"
    HELP = "Dangerous unary expressions"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#dangerous-unary-expressions"
    )

    WIKI_TITLE = "Dangerous unary expressions"
    WIKI_DESCRIPTION = "Unary expressions such as `x=+1` probably typos."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```Solidity 
contract Bug{
    uint public counter;

    function increase() public returns(uint){
        counter=+1;
        return counter;
    }
}
```
`increase()` uses `=+` instead of `+=`, so `counter` will never exceed 1."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove the unary expression."

    def _detect(self):
        """
        Detect the incorrect use of unary expressions
        """
        results = []
        for c in self.contracts:
            for variable in c.state_variables:
                if (
                    variable.expression
                    and InvalidUnaryStateVariableDetector(variable.expression).result()
                ):
                    info = [variable, f" uses an dangerous unary operator: {variable.expression}\n"]
                    json = self.generate_result(info)
                    results.append(json)

            for f in c.functions_and_modifiers_declared:
                for node in f.nodes:
                    if node.expression and InvalidUnaryExpressionDetector(node.expression).result():
                        info = [node.function, " uses an dangerous unary operator: ", node, "\n"]
                        res = self.generate_result(info)
                        results.append(res)

        return results
