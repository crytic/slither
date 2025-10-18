from pathlib import Path
from slither import Slither
from slither.core.declarations.function_contract import FunctionContract
from slither.slithir.operations import HighLevelCall, NewArray

# Assuming this path setup is correct for the test runner environment
TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" 


def test_array_instantiation_with_call_fix(solc_binary_path) -> None:
    """
    Tests the fix for array instantiation that involves structs and function calls 
    within the array literal (e.g., a.f([B(num), B(num + 1)])).

    The previous bug manifested as a crash or incorrect SlithIR generation during 
    the processing of the array literal containing complex expressions/struct initializations.
    We assert that the necessary NewArray and HighLevelCall operations are correctly generated.
    """
    solc_path = solc_binary_path("0.8.0")
    # Load the minimal reproducible example contract
    slither = Slither(Path(TEST_DATA_DIR, "array_instantiation_call.sol").as_posix(), solc=solc_path)

    contract_c = slither.get_contract_from_name("C")[0]
    
    # Target the problematic function: e(A a, uint256 num) which has the struct array instantiation
    # Signature matching uses addresses for contract arguments
    target_func: FunctionContract = contract_c.get_function_from_signature("e(address,uint256)")
    
    assert target_func is not None, "Target function e(address,uint256) not found."
    
    # The fix is validated by ensuring the crucial SlithIR instructions exist, 
    # proving the parsing was successful and complete for the complex expression.
    
    # 1. Check for the HighLevelCall (the external call to a.f)
    call_to_f = next(
        (op for op in target_func.slithir_operations if isinstance(op, HighLevelCall)), 
        None
    )
    assert call_to_f is not None, "HighLevelCall to 'a.f' should exist."
    
    # 2. Check for the NewArray operation, which constructs the array literal
    new_array_op = next(
        (op for op in target_func.slithir_operations if isinstance(op, NewArray)), 
        None
    )
    assert new_array_op is not None, "NewArray operation must be generated for the array literal."
    
    # 3. Final structural check: ensure the function parsed fully without errors.
    assert len(target_func.slithir_operations) > 5, "SlithIR operations are too few, indicating incomplete parsing/generation."
