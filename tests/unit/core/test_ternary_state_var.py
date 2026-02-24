"""Test that ternary expressions in state variable initializers are handled correctly.

Regression test for https://github.com/crytic/slither/issues/2836
"""

from pathlib import Path

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "ternary_in_state_var"


def test_ternary_in_state_variable_initializer(solc_binary_path) -> None:
    """Ensure ternary expressions in state variable initializers don't crash.

    Before the fix, a ConditionalExpression in a state variable initializer
    would reach SlithIR conversion without being split, causing SlithIRError.
    """
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    for source_file in TEST_DATA_DIR.rglob("**/*.sol"):
        standard_json.add_source_file(Path(source_file).as_posix())
    compilation = CryticCompile(standard_json, solc=solc_path)
    sl = Slither(compilation)

    # Verify contract B was parsed successfully
    contract_b = next(c for c in sl.contracts if c.name == "B")
    result_var = next(v for v in contract_b.state_variables if v.name == "result")
    assert result_var is not None
    assert "uint32" in str(result_var.type)
