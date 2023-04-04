interface ITestContract {
    event NoParams();
    event Anonymous();
    event OneParam(address);
    event OneParamIndexed(address);
    error ErrorWithEnum(SomeEnum);
    error ErrorSimple();
    error ErrorWithArgs(uint256, uint256);
    error ErrorWithStruct(St);
    enum SomeEnum { ONE, TWO, THREE }
    struct St {
        uint256 v;
    }
    struct Nested {
        St st;
    }
    function stateA() external returns (uint256);
    function owner() external returns (address);
    function structsMap(address,uint256) external returns (St memory);
    function structsArray(uint256) external returns (St memory);
    function otherI() external returns (address);
    function err0() external;
    function err1() external;
    function err2(uint256,uint256) external;
    function newSt(uint256) external returns (St memory);
    function getSt(uint256) external view returns (St memory);
    function removeSt(St memory) external;
    function setOtherI(address) external;
}

