from pathlib import Path

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither
from slither.detectors.functions.dead_code import DeadCode


class OrderedFunctions(set):
    """Exercise either possible enumeration order of an identity-hashed set."""

    def __init__(self, functions):
        super().__init__(functions)
        self.order = functions

    def __iter__(self):
        return iter(self.order)


def test_dead_code_same_name_uses_stable_source_tie_breaker(
    tmp_path, solc_binary_path, monkeypatch
):
    # solc only reads sources below its working directory.
    monkeypatch.chdir(tmp_path)
    standard = SolcStandardJson()
    for name in ("A.sol", "B.sol"):
        path = tmp_path / name
        path.write_text("pragma solidity ^0.8.19; contract C { function unused() internal {} }\n")
        standard.add_source_file(str(path))
    compilation = CryticCompile(standard, solc=solc_binary_path("0.8.19"))
    slither = Slither(compilation)
    slither.register_detector(DeadCode)
    unit = slither.compilation_units[0]
    functions = sorted(unit.functions, key=lambda f: f.source_mapping.filename.absolute)
    raw = slither.detectors[0]._detect()
    # The existing ID conversion uses the canonical name, which collides here.
    # This regression does not change ID generation or deduplication.
    assert len(raw) == 2
    assert raw[0].data["id"] == raw[1].data["id"]
    outputs = []
    for order in (functions, list(reversed(functions))):
        unit._all_functions = OrderedFunctions(order)
        slither._currently_seen_resuts.clear()
        outputs.append(slither.run_detectors()[0])
    assert outputs[0] == outputs[1]
    assert len(outputs[0]) == 1
    source = outputs[0][0]["elements"][0]["source_mapping"]["filename_absolute"]
    assert Path(source).name == "A.sol"
