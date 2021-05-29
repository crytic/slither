interface ISomething {
    function f1() external returns(uint);
}

contract Something {
    function f1() external returns(uint){
        return 42;
    }
}