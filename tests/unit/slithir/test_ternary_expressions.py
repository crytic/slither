from pathlib import Path
from slither import Slither
from slither.core.cfg.node import NodeType
from slither.slithir.operations import Assignment, Unpack
from slither.core.expressions import (
    AssignmentOperation,
    TupleExpression,
    NewElementaryType,
    CallExpression,
)


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
# pylint: disable=too-many-nested-blocks
def test_ternary_conversions(solc_binary_path) -> None:
    """This tests that true and false sons define the same number of variables that the father node declares"""
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "ternary_expressions.sol").as_posix(), solc=solc_path)
    contract = next(c for c in slither.contracts if c.name == "C")
    for function in contract.functions:
        vars_declared = 0
        vars_assigned = 0
        for node in function.nodes:
            if node.type in [NodeType.IF, NodeType.IFLOOP]:

                # Iterate over true and false son
                for inner_node in node.sons:
                    # Count all variables declared
                    expression = inner_node.expression
                    if isinstance(
                        expression, (AssignmentOperation, NewElementaryType, CallExpression)
                    ):
                        var_expr = expression.expression_left
                        # Only tuples declare more than one var
                        if isinstance(var_expr, TupleExpression):
                            vars_declared += len(var_expr.expressions)
                        else:
                            vars_declared += 1

                    for ir in inner_node.irs:
                        # Count all variables defined
                        if isinstance(ir, (Assignment, Unpack)):
                            vars_assigned += 1
        assert vars_declared == vars_assigned and vars_assigned != 0


def test_ternary_tuple(solc_binary_path) -> None:
    """
    Test that in the ternary liftings of an assignment of the form `(z, ) = ...`,
    we obtain `z` from an unpack operation in both lifitings
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "ternary_expressions.sol").as_posix(), solc=solc_path)
    contract = next(c for c in slither.contracts if c.name == "D")
    fn = next(f for f in contract.functions if f.name == "a")

    if_nodes = [n for n in fn.nodes if n.type == NodeType.IF]
    assert len(if_nodes) == 1

    if_node = if_nodes[0]
    assert isinstance(if_node.son_true.expression, AssignmentOperation)
    assert (
        len([ir for ir in if_node.son_true.all_slithir_operations() if isinstance(ir, Unpack)]) == 1
    )
    assert (
        len([ir for ir in if_node.son_false.all_slithir_operations() if isinstance(ir, Unpack)])
        == 1
    )
