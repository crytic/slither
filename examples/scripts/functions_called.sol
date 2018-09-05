contract BaseContract{
    
    function f1(){

    }
}

contract Contract is BaseContract{

    uint a;

    function entry_point(){
        f1();
        f2();
    }

    function f1(){
        super.f1();
    }

    function f2(){

    }
    
    // not reached from entry_point
    function f3(){

    }
}
