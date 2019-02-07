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
        return 0;
    }
    function notRedefined() public returns (uint) {
        return getValue();
    }

    modifier testModifier {
        assert(true);
        _;
    }
    function testFunction() testModifier public returns (uint) {
        return 0;
    }
}

contract B is A {
    // This function overshadows A directly, and overshadows C indirectly (via 'G'->'D')
    function getValue() public pure returns (uint) {
        return 1;
    }
}

contract Good is A, B {

}

contract C is A {

    // This function overshadows A directly, and overshadows B indirectly (via 'G')
    function getValue() public pure returns (uint) {
        return super.getValue() + 1;
    }
}

contract D is B {
    // This should overshadow A's definitions.
    uint public shadowed_public_var = 2;
    uint internal shadowed_private_var = 2;
    TestContractVar public shadowed_public_contract;
    TestContractVar internal shadowed_private_contract;
}

contract E {
    // Variables cannot indirectly shadow, so this should not be counted.
    uint public public_var = 2;
    uint internal private_var = 2;
    TestContractVar public public_contract;
    TestContractVar internal private_contract;

    // This should overshadow A's definition indirectly (via 'G').
    modifier testModifier {
        assert(false);
        _;
    }
}

contract F is B {
    // This should overshadow A's definitions.
    uint public shadowed_public_var = 2;
    uint internal shadowed_private_var = 2;
    TestContractVar public shadowed_public_contract;
    TestContractVar internal shadowed_private_contract;

    // This should overshadow B's definition directly, as well as B's and C's indirectly (via 'G')
    // (graph only outputs directly if both, so B direct and C indirect should be reported).
    function getValue() public pure returns (uint) {
        return 1;
    }

    // This should indirectly shadow definition in A directly, and E indirectly (via 'G')
    modifier testModifier {
        assert(false);
        _;
    }
}

contract G is B, C, D, E, F {
    // This should overshadow definitions in A, D, and F
    uint public shadowed_public_var = 3;
    uint internal shadowed_private_var = 3;
    TestContractVar public shadowed_public_contract;

    // This contract's multiple inheritance chain should cause indirect shadowing (c3 linearization shadowing).
}
