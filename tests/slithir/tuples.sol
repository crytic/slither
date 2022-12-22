contract Tuples 
{
    function f1() public returns(uint) 
    {
        uint x;
        ((x, ), ) = ((7, 7) ,7);
        return x;
    }
    
    function f2() public returns(uint)
    {
        uint x;
        (x, ) = (7, 7);
        return x;
    }

    function f3() public returns(uint) 
    {
        uint x;
        uint y;
        uint z;
        uint t;
        ((x, (y, z), t), ) = ((1, (2, 3) ,4), 5);
        return x;
    } 
}
