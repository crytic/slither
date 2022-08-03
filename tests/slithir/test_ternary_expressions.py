from slither import Slither
from slither.core.cfg.node import NodeType
from slither.slithir.operations import Assignment
from slither.core.expressions import AssignmentOperation, TupleExpression

# pylint: disable=too-many-nested-blocks
def test_ternary_conversions() -> None:
    """This tests that true and false sons define the same number of variables that the father node declares"""
    slither = Slither("./tests/slithir/ternary_expressions.sol")
    for contract in slither.contracts:
        for function in contract.functions:
            for node in function.nodes:
                if node.type in [NodeType.IF, NodeType.IFLOOP]:
                    vars_declared = 0
                    vars_assigned = 0

                    # Iterate over true and false son
                    for inner_node in node.sons:
                        # Count all variables declared
                        expression = inner_node.expression
                        if isinstance(expression, AssignmentOperation):
                            var_expr = expression.expression_left
                            # Only tuples declare more than one var
                            if isinstance(var_expr, TupleExpression):
                                vars_declared += len(var_expr.expressions)
                            else:
                                vars_declared += 1

                        for ir in inner_node.irs:
                            # Count all variables defined
                            if isinstance(ir, Assignment):
                                vars_assigned += 1

                    assert vars_declared == vars_assigned


if __name__ == "__main__":
    test_ternary_conversions()
