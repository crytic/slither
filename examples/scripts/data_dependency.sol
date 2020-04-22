contract Simple{

    address destination;
    address source;

    function set(address source_taint) public{
        destination = source_taint;
    }

    function set2() public{
        destination = source;
    }
}

contract Reference{

    struct St{
        uint val;
    }

    St destination;
    St source;
    St destination_indirect_1;
    St destination_indirect_2;

    function set(uint source_taint) public{
        destination.val = source_taint;
    }

    function set2() public{
        destination.val = source.val;
    }

    function set3(uint source_taint) public{
        St storage ref = destination_indirect_1;
        if(true){
            ref = destination_indirect_2;
        }
        ref.val = source_taint;
    }
}

contract SolidityVar{

    address addr_1;
    address addr_2;

    constructor() public{
        addr_1 = msg.sender;
    }

}

contract Intermediate{

    uint destination;
    uint source_intermediate;
    uint source;

    function f() public{
        destination = source_intermediate;
    }
    function f2() public{
        source_intermediate = source;
    }

}


contract Base{

    uint destination;
    uint source_intermediate;
    uint source;

    function f() public{
        destination = source_intermediate;
    }
}
contract Derived is Base{

    function f2() public{
        source_intermediate = source;
    }


}


contract PropagateThroughArguments {
    uint var_tainted;
    uint var_not_tainted;
    uint var_dependant;

    function f(uint user_input) public {
        f2(user_input, 4);
        var_dependant = var_tainted;
    }

    function f2(uint x, uint y) internal {
        var_tainted = x;
        var_not_tainted = y;
    }
}

contract PropagateThroughReturnValue {
  uint var_dependant;
  uint var_state;

  function foo() public {
    var_dependant = bar();
  }

  function bar() internal returns (uint) {
    return (var_state);
  }
}

contract Nested{

    struct St{
        uint val1;
        uint val2;
    }

    struct Nested{
        St st;
    }

    struct NestedN{
        Nested m;
        Nested l;
    }

    NestedN n;

    uint state_a;
    uint state_b;

    function f(uint a) public{
        n.l.st.val1 = a;
        n.m.st.val2 = n.l.st.val1;
    }

    function g() public{
        state_b = n.m.st.val2 + state_a;
    }

}