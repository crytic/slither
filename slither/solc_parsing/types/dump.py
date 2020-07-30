import json

from slither.solc_parsing.types.types import ASTNode


def dumps(node: ASTNode) -> str:
    def default(x):
        slots = x.__slots__
        if isinstance(slots, str):
            slots = [slots]
        res = {slot: getattr(x, slot, None) for slot in slots}
        res['nodeType'] = type(x).__name__
        return res

    return json.dumps(node, indent=2, default=default)
