type MyType is uint256;

contract A{

    enum E{
        a,b,c
    }


    uint a = 10;
    E b = type(E).max;
    uint c = type(uint32).max;
    MyType d = MyType.wrap(100);

    function use() public returns(uint){
        E e = b;
        return a +c + MyType.unwrap(d);
    }
}