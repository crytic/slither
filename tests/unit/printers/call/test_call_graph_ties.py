from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from slither import Slither
from slither.printers.call.call_graph import PrinterCallGraph


class OrderedSet(set):
    def __init__(self, values):
        super().__init__(values)
        self.order = values

    def __iter__(self):
        return iter(self.order)


def test_call_graph_same_canonical_name_selects_stable_source(
    tmp_path, solc_binary_path, monkeypatch
):
    # solc only reads sources below its working directory.
    monkeypatch.chdir(tmp_path)
    standard = SolcStandardJson()
    for name in ("A.sol", "B.sol"):
        path = tmp_path / name
        path.write_text(
            "pragma solidity ^0.8.19; contract C { function f(uint x) public pure returns(uint) { return x+1; } }\n"
        )
        standard.add_source_file(str(path))
    slither = Slither(CryticCompile(standard, solc=solc_binary_path("0.8.19")))
    unit = slither.compilation_units[0]
    functions = sorted(unit.functions, key=lambda f: f.source_mapping.filename.absolute)
    graphs = []
    for i, order in enumerate((functions, list(reversed(functions)))):
        unit._all_functions = OrderedSet(order)
        printer = PrinterCallGraph(unit, slither, None)
        printer.output(str(tmp_path / f"order{i}"))
        graphs.append((tmp_path / f"order{i}.all_contracts.call-graph.dot").read_text())
    assert graphs[0] == graphs[1]
