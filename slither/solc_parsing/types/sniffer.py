from typing import Dict, Optional


def sniff(raw: Dict):
    result = sniff_internal(raw)
    if not result:
        result = DEFAULT_SNIFF_RESULT

    return HANDLERS[result]


def sniff_internal(raw: Dict) -> Optional[str]:
    for id, rule in SNIFFER_RULES.items():
        if rule(raw):
            return id

    for k, v in raw.items():
        if isinstance(v, dict):
            result = sniff_internal(v)
            if result:
                return result

    return None


def sniff_legacy_json(raw: Dict) -> bool:
    uses_legacy_nodetype_key = 'name' in raw
    uses_legacy_children = 'children' in raw and isinstance(raw['children'], list)

    return uses_legacy_nodetype_key and uses_legacy_children


DEFAULT_SNIFF_RESULT = 'sniffer_compact_json'

SNIFFER_RULES = {
    'sniffer_legacy_json': sniff_legacy_json,
}

from .legacy_json import parse as legacy_parser
from .compact_json import parse as compact_parser

HANDLERS = {
    'sniffer_legacy_json': legacy_parser,
    'sniffer_compact_json': compact_parser,
}
