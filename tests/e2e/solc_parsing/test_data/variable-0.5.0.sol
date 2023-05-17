contract C {
    struct S {
        uint a;
    }

    mapping(uint => uint) m;
    string s;
    bytes b;
    S t;
    uint[] a;

    function basic() public {
        address address_;
        bool bool_;
        string memory stringMemory_;
        string storage stringStorage_ = s;
        int int_;
        int256 int256_;
        int8 int8_;
        uint uint_;
        uint256 uint256_;
        uint8 uint8_;
        byte byte_;
        bytes memory bytesMemory_;
        bytes storage bytesStorage_ = b;
        bytes32 byte32_;
    }

    function basic2() public {
        fixed fixed_;
        fixed128x18 fixed128x18_;
        fixed8x0 fixed8x0_;
        ufixed ufixed_;
        ufixed128x18 ufixed128x18_;
        ufixed8x0 ufixed8x0_;

        S memory sMemory_;
        S storage sStorage_ = t;

        mapping(uint=>uint) storage mappingStorage_ = m;

        uint[] memory arrayMemory_;
        uint[] storage arrayStorage_ = a;

        function() internal funcEmptyInternalEmpty_;
        function(uint) internal funcUintInternalEmpty_;
        function(uint) internal returns (uint) funcUintInternalUint_;
        function(uint) external payable returns (uint) funcUintExternalPayableUint_;
        function(uint) external view returns (uint) funcUintExternalViewUint_;

        address payable addressPayable_;
    }
}