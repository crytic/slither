contract Log{
    // Check that we can parse string/bytes
    function f(bytes calldata) external{
    }

    function f(bytes4) external{
    }
}

contract A{

    Log l;
    function test() internal{
        l.f("TESTA");
    }
}

