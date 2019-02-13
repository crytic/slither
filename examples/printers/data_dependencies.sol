contract MyContract{
    uint a = 0;
    uint b = 0;
    uint c = 0;

    function setA(uint input_a, uint input_b) public{
        setB(input_b);
        a = input_a;
    }

    function setB(uint input) internal{
        b = input;
    }

}
