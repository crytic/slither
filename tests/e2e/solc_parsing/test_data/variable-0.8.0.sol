contract C {
    struct S {
        uint a;
    }

    mapping(uint => uint) m;
    string s;
    bytes b;
    S t;
    uint[] a;

    uint immutable immutableInt = 1;

    function basic() public {
        address address_;
        bool bool_;
        string memory stringMemory_;
        string storage stringStorage_ = s;
        string calldata stringCalldata_;
        int int_;
        int256 int256_;
        int8 int8_;
        uint uint_;
        uint256 uint256_;
        uint8 uint8_;
        bytes1 byte_;
        bytes memory bytesMemory_;
        bytes storage bytesStorage_ = b;
        bytes calldata bytesCalldata_;
        bytes32 byte32_;
        fixed fixed_;
        fixed128x18 fixed128x18_;
        fixed8x0 fixed8x0_;
        ufixed ufixed_;
        ufixed128x18 ufixed128x18_;
        ufixed8x0 ufixed8x0_;

        S memory sMemory_;
        S storage sStorage_ = t;
        S calldata sCalldata_;

        mapping(uint=>uint) storage mappingStorage_ = m;

        uint[] memory arrayMemory_;
        uint[] storage arrayStorage_ = a;
        uint[] calldata arrayCalldata_;

        function() internal funcEmptyInternalEmpty_;
        function(uint) internal funcUintInternalEmpty_;
        function(uint) internal returns (uint) funcUintInternalUint_;
        function(uint) external payable returns (uint) funcUintExternalPayableUint_;
        function(uint) external view returns (uint) funcUintExternalViewUint_;

        address payable addressPayable_;
    }
}
