from slither.core.solidity_types import ArrayType, MappingType, UserDefinedType


def test_nested_types_keep_inherited_and_file_scope_bindings(slither_from_solidity_source):
    source = """
    pragma solidity ^0.8.19;
    type Amount is uint256;
    struct FileRecord { Amount amount; }
    contract A {
        enum Choice { Left, Right }
        struct Entry { Choice choice; FileRecord record; }
    }
    contract B is A {
        mapping(address => Entry[]) private records;
        uint256[3][] private numbers;
        function inspect(Entry memory e, FileRecord memory f, Amount amount)
            public pure returns (Choice, Amount) {
            return (e.choice, Amount.wrap(Amount.unwrap(f.amount) + Amount.unwrap(amount)));
        }
    }
    """
    with slither_from_solidity_source(source) as slither:
        contract = slither.get_contract_from_name("B")[0]
        records = contract.get_state_variable_from_name("records").type
        assert isinstance(records, MappingType)
        assert isinstance(records.type_to, ArrayType)
        entry = records.type_to.type
        assert isinstance(entry, UserDefinedType)
        assert entry.type.canonical_name == "A.Entry"
        function = next(f for f in contract.functions if f.name == "inspect")
        assert str(function.parameters[0].type) == "A.Entry"
        assert str(function.parameters[1].type) == "FileRecord"
        assert str(function.parameters[2].type) == "Amount"
        assert str(function.returns[0].type) == "A.Choice"
        assert str(contract.get_state_variable_from_name("numbers").type) == "uint256[3][]"
