contract C {
    struct S {
        uint a;
    }

    mapping(uint => uint) m;

    function basic() public {
        address address_;
        bool bool_;
        string memory stringMemory_;
        string storage stringStorage_;
        int int_;
        int256 int256_;
        int8 int8_;
        uint uint_;
        uint256 uint256_;
        uint8 uint8_;
        byte byte_;
        bytes memory bytesMemory_;
        bytes storage bytesStorage_;
        bytes32 byte32_;
        fixed fixed_;
        ufixed ufixed_;
    }

    function complex() public {
        S memory sMemory_;
        S storage sStorage_;

        mapping(uint=>uint) mappingStorage_ = m;

        uint[] memory arrayMemory_;
        uint[] storage arrayStorage_;
    }
}