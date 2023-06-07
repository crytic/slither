pragma solidity ^0.8.4;
interface I {
  enum SomeEnum { ONE, TWO, THREE }
  error ErrorWithEnum(SomeEnum e);
}

contract TestContract is I {
    uint public stateA;
    uint private stateB;
    address public immutable owner = msg.sender;
    mapping(address => mapping(uint => St)) public structsMap;
    St[] public structsArray;
    I public otherI;

    event NoParams();
    event Anonymous() anonymous;
    event OneParam(address addr);
    event OneParamIndexed(address indexed addr);

    error ErrorSimple();
    error ErrorWithArgs(uint, uint);
    error ErrorWithStruct(St s);

    struct St{
        uint v;
    }

    struct Nested{
        St st;
    }

    function err0() public {
        revert ErrorSimple();
    }
    function err1() public {
        St memory s;
        revert ErrorWithStruct(s);
    }
    function err2(uint a, uint b) public {
        revert ErrorWithArgs(a, b);
        revert ErrorWithArgs(uint(SomeEnum.ONE), uint(SomeEnum.ONE));
    }
    function err3() internal {
        revert('test');
    }
    function err4() private {
        revert ErrorWithEnum(SomeEnum.ONE);
    }

    function newSt(uint x) public returns (St memory) {
        St memory st;
        st.v = x;
        structsMap[msg.sender][x] = st;
        return st;
    }
    function getSt(uint x) public view returns (St memory) {
        return structsMap[msg.sender][x];
    }
    function removeSt(St memory st) public {
        delete structsMap[msg.sender][st.v];
    }
    function setOtherI(I _i) public {
        otherI = _i;
    }
}