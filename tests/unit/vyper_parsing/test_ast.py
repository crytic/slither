from slither.vyper_parsing.ast.ast import parse
from slither.vyper_parsing.ast.types import Call, Name


def _name(node_id: int, value: str) -> dict:
    return {"ast_type": "Name", "id": value, "src": "0:1:0", "node_id": node_id}


def test_parse_call_without_keyword_field():
    raw = {
        "ast_type": "Call",
        "func": _name(1, "transfer"),
        "args": [_name(2, "amount")],
        "keywords": [],
        "src": "0:1:0",
        "node_id": 3,
    }

    parsed = parse(raw)

    assert isinstance(parsed, Call)
    assert parsed.keyword is None
    assert all(isinstance(arg, Name) for arg in parsed.args)
    assert [arg.id for arg in parsed.args if isinstance(arg, Name)] == ["amount"]


def test_parse_call_preserves_keyword_field():
    raw = {
        "ast_type": "Call",
        "func": _name(1, "transfer"),
        "args": [_name(2, "amount")],
        "keyword": _name(3, "recipient"),
        "keywords": [],
        "src": "0:1:0",
        "node_id": 4,
    }

    parsed = parse(raw)

    assert isinstance(parsed, Call)
    assert isinstance(parsed.keyword, Name)
    assert parsed.keyword.id == "recipient"
