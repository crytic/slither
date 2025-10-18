from pathlib import Path
from slither import Slither
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.operations import HighLevelCall, NewStructure, Binary

# Assuming this path setup is correct for the test runner environment
# This path points to the directory containing array_instantiation_call.sol
TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" 


def _check_common_assertions(target_func: FunctionContract, expected_description: str):
    """Utility to check the base requirement: successful HighLevelCall generation."""
    assert target_func is not None, f"Target function for {expected_description} not found."
    
    slithir_ops = target_func.slithir_operations
    
    # 1. Check for the HighLevelCall (the external call to a.f)
    # The presence of this call proves the array and argument resolution completed without crashing.
    call_to_f = next(
        (op for op in slithir_ops if isinstance(op, HighLevelCall)), 
        None
    )
    assert call_to_f is not None, f"[{expected_description}]: HighLevelCall to 'a.f' should exist."
    assert len(slithir_ops) > 0, f"[{expected_description}]: No SlithIR operations found, indicating a crash or severe parsing failure."


def test_primitive_array_instantiation_fix(solc_binary_path) -> None:
    """
    Tests the fix for array instantiation of simple primitive types (e.g., a.f([0, num])).
    This case was previously bugged and must now successfully generate the HighLevelCall.
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "array_instantiation_call.sol").as_posix(), solc=solc_path)
    contract_c = slither.get_contract_from_name("C")[0]
    
    target_func: FunctionContract = contract_c.get_function_from_signature("test_primitive_array_instantiation(address,uint256)")
    
    _check_common_assertions(target_func, "Primitive Array Instantiation")
    


def test_struct_array_instantiation_fix(solc_binary_path) -> None:
    """
    Tests the fix for complex array instantiation involving structs and arithmetic 
    (e.g., a.f([B(num), B(num + 1)])). This was a more complex buggy case.
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "array_instantiation_call.sol").as_posix(), solc=solc_path)

    contract_c = slither.get_contract_from_name("C")[0]
    
    target_func: FunctionContract = contract_c.get_function_from_signature("test_struct_array_instantiation(address,uint256)")
    
    _check_common_assertions(target_func, "Struct Array Instantiation")
    
    slithir_ops = target_func.slithir_operations
    
    
    #Check for the NewStructure operation (for B(num) or B(num + 1))
    new_struct_op = next(
        (op for op in slithir_ops if isinstance(op, NewStructure)), 
        None
    )
    assert new_struct_op is not None, "[Struct Array Instantiation]: NewStructure operation must be generated for struct B creation."
