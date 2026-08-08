from pathlib import Path

from slither import Slither
from slither.analyses.data_dependency.data_dependency import is_dependent_ssa
from slither.slithir.variables import LocalIRVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_param_dependency(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.24")
    slither = Slither(
        Path(TEST_DATA_DIR, "parameter_dependency_ssa.sol").as_posix(), solc=solc_path
    )

    target_function = slither.contracts[0].get_function_from_signature(
        "onERC721Received(address,address,uint256,bytes)"
    )

    # Param is from (from_0 in SSA)
    # Local SSA variable is from_1

    param_var = None

    for param_ssa in target_function.parameters_ssa:
        if param_ssa.non_ssa_version.name == "from":
            param_var = param_ssa
            break

    assert param_var is not None, "Param variable not found in SSA"

    local_var = None
    for ir in target_function.slithir_ssa_operations:
        for v in ir.used:
            if isinstance(v, LocalIRVariable) and v.non_ssa_version.name == "from" and v.index == 1:
                local_var = v
                break

    assert local_var is not None, "Local variable not found in SSA"

    assert is_dependent_ssa(
        local_var, param_var, target_function
    ), "Param and local variable are not dependent"
