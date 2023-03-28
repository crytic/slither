type MyType is uint256;

library MyLib {
    using A for MyType;
    using B for uint;
    function a() internal returns(uint){
        MyType myvar = MyType.wrap(4);
        return MyType.unwrap(myvar.b()).c();
    }
}

library A {
    function b(MyType e) public returns(MyType){
        return MyType.wrap(3);
    }

}
library B {
    function c(uint e) public returns(uint){
        return 345;
    }
}