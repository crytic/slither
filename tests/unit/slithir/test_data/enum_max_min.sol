
library Q {
    enum E {a}
}

contract Z {
    enum E {a,b}
}

contract D {
    enum E {a,b,c}

    function a() public returns(uint){
        return uint(type(E).max);
    }

    function b() public returns(uint){
        return uint(type(Q.E).max);
    }

    function c() public returns(uint){
        return uint(type(Z.E).max);
    }

    function d() public returns(uint){
        return uint(type(E).min);
    }

    function e() public returns(uint){
        return uint(type(Q.E).min);
    }

    function f() public returns(uint){
        return uint(type(Z.E).min);
    }

}
