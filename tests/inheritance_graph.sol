contract TestContractVar {

}

contract A {
    uint public public_var = 1;
    uint internal private_var = 1;
    TestContractVar public public_contract;
    TestContractVar internal private_contract;

    uint public shadowed_public_var = 1;
    uint internal shadowed_private_var = 1;
    TestContractVar public shadowed_public_contract;
    TestContractVar internal shadowed_private_contract;

    function getValue() public pure returns (uint) {
        // This function should be overshadowed directly by B, C, and indirectly by B (via 'Good')
        return 0;
    }
    function notRedefined() public returns (uint) {
        return getValue();
    }

    modifier testModifier {
        // This is redefined in E.
        assert(true);
        _;
    }
    function testFunction() testModifier public returns (uint) {
        return 0;
    }
}

contract B is A {
    // This function should not be marked as overshadowed (although C overshadows it, D further overshadows it, and D
    // derives from B, so it neutralizes any overshadowing for this contract).
    function getValue() public pure returns (uint) {
        return 1;
    }
}

contract Good is A, B {

}

contract C is A {
    TestContractVar public shadowed_public_contract;
    TestContractVar internal shadowed_private_contract;

    function getValue() public pure returns (uint) {
        // This function should be marked as overshadowed indirectly by D (via 'F')
        return super.getValue() + 1;
    }
}

contract D is B {
    // This should overshadow A's definitions.
    uint public shadowed_public_var = 2;
    uint internal shadowed_private_var = 2;

    // This contract should use B's getValue() to overshadow C's definition indirectly (via 'F').
}

contract E {
    // Variables cannot indirectly shadow, so this should not be counted.
    uint public public_var = 2;
    uint internal private_var = 2;
    TestContractVar public public_contract;
    TestContractVar internal private_contract;

    modifier testModifier {
        // This should indirectly shadow A's definition (via 'F')
        assert(false);
        _;
    }
}

contract F is B, C, D, E {
    // This should overshadow A's and D's definitions.
    uint public shadowed_public_var = 3;
    uint internal shadowed_private_var = 3;

    // This should overshadow A's and C's definitions.
    TestContractVar public shadowed_public_contract;

    // This contract's multiple inheritance chain should cause indirect shadowing (c3 linearization shadowing).
}
