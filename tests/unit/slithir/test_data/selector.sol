interface I{
    function testFunction(uint a) external ;
}

contract A{
    function testFunction() public{}
}

contract Test{
    event TestEvent();
    struct St{
        uint a;
    }
    error TestError();

    function testFunction(uint a) public {}


    function testFunctionStructure(St memory s) public {}

    function returnEvent() public returns (bytes32){
        return TestEvent.selector;
    }

    function returnError() public returns (bytes4){
        return TestError.selector;
    }


    function returnFunctionFromContract() public returns (bytes4){
        return I.testFunction.selector;
    }


    function returnFunction() public returns (bytes4){
        return this.testFunction.selector;
    }

    function returnFunctionWithStructure() public returns (bytes4){
        return this.testFunctionStructure.selector;
    }

    function returnFunctionThroughLocaLVar() public returns(bytes4){
        A a;
        return a.testFunction.selector;
    }
}