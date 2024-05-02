from slither.tools.demo.__main__ import main as demo_main
from slither.tools.doctor.__main__ import main as doctor_main
from slither.tools.codex.__main__ import codex_callback as codex_main
from slither.tools.erc_conformance.__main__ import main as erc_conformance_main
from slither.tools.flattening.__main__ import main as flattening_main
from slither.tools.interface.__main__ import main as interface_main
from slither.tools.kspec_coverage.__main__ import main as kspec_coverage_main
from slither.tools.mutator.__main__ import main as mutator_main
from slither.tools.possible_paths.__main__ import main as possible_paths_main
from slither.tools.properties.__main__ import main as properties_main
from slither.tools.read_storage.__main__ import main as read_storage_main

try:
    from slither.tools.similarity.__main__ import main as similarity_main
except ImportError:
    pass

from slither.tools.slither_format.__main__ import main as slither_format_main
from slither.tools.upgradeability.__main__ import main as upgradeability_main

__all__ = [
    "demo_main",
    "doctor_main",
    "codex_main",
    "erc_conformance_main",
    "flattening_main",
    "interface_main",
    "kspec_coverage_main",
    "mutator_main",
    "possible_paths_main",
    "properties_main",
    "read_storage_main",
    "slither_format_main",
    "upgradeability_main",
]
