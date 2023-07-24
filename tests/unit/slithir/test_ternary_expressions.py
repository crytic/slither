from pathlib import Path
from slither import Slither
from slither.core.cfg.node import NodeType
from slither.slithir.operations import Assignment
from slither.core.expressions import AssignmentOperation, TupleExpression


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
# pylint: disable=too-many-nested-blocks
def test_ternary_conversions(solc_binary_path) -> None:
    """This tests that true and false sons define the same number of variables that the father node declares"""
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "ternary_expressions.sol").as_posix(), solc=solc_path)
    for contract in slither.contracts:
        for function in contract.functions:
            vars_declared = 0
            vars_assigned = 0
            for node in function.nodes:
                if node.type in [NodeType.IF, NodeType.IFLOOP]:

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
