 contract Test {   
    error myError();
}

interface VM  {
    function expectRevert(bytes4) external;
    function expectRevert(bytes calldata) external;
}
contract A {
    function b(address c) public {
        VM(c).expectRevert(Test.myError.selector);
    }
}
