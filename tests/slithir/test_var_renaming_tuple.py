from typing import Set

from slither import Slither
from slither.slithir.operations import Unpack


# test if slither renames correctly local variables when they are initialised in tuple
def test_var_renaming_tuple() -> None:
    slither = Slither("./tests/slithir/var_renaming_tuple.sol")
    contract = slither.contracts[0]
    f2 = contract.functions[0] if contract.functions[0].name == "f2" else contract.functions[1]
    var_names: Set[str] = set()
    for op in f2.slithir_operations:
        if isinstance(op, Unpack):
            var_names.add(op.lvalue.name)
    # check if each variable has a different name
    assert len(var_names) == 4


if __name__ == "__main__":
    test_var_renaming_tuple()
