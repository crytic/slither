from slither.core.expressions import AssignmentOperationType, BinaryOperationType
from slither.vyper_parsing.ast.ast import parse_aug_assign, parse_bin_op


def _base_node(node_id: int = 0) -> dict:
    return {"src": "0:0:0", "node_id": node_id}


def _int_node(value: int, node_id: int) -> dict:
    return {"ast_type": "Int", "value": value, **_base_node(node_id)}


def _name_node(name: str, node_id: int) -> dict:
    return {"ast_type": "Name", "id": name, **_base_node(node_id)}


def _binary_operation_type(vyper_ast_type: str) -> BinaryOperationType:
    expression = parse_bin_op(
        {
            "left": _int_node(1, 1),
            "op": {"ast_type": vyper_ast_type},
            "right": _int_node(2, 2),
            **_base_node(),
        }
    )
    return BinaryOperationType.get_type(expression.op)


def _assignment_operation_type(vyper_ast_type: str) -> AssignmentOperationType:
    expression = parse_aug_assign(
        {
            "target": _name_node("x", 1),
            "op": {"ast_type": vyper_ast_type},
            "value": _int_node(2, 2),
            **_base_node(),
        }
    )
    return AssignmentOperationType.get_type(expression.op)


def test_vyper_shift_binary_operator_mapping() -> None:
    assert _binary_operation_type("Shl") == BinaryOperationType.LEFT_SHIFT
    assert _binary_operation_type("Shr") == BinaryOperationType.RIGHT_SHIFT


def test_vyper_augmented_assignment_operator_mapping() -> None:
    assert _assignment_operation_type("Div") == AssignmentOperationType.ASSIGN_DIVISION
    assert _assignment_operation_type("Shl") == AssignmentOperationType.ASSIGN_LEFT_SHIFT
    assert _assignment_operation_type("Shr") == AssignmentOperationType.ASSIGN_RIGHT_SHIFT
