contract Test{

    Test t;
    struct St{
        address a;
        Test t2;
    }

    St st;

    bool ret;

    function one(){
        t.test(1);
        t.test.value(0)(1);
        t.test.value(test2())(1);
        t.test.value(0).gas(1)(3);
    }
    function two(){
       
        msg.sender.call.value(0)(bytes4(keccak256(('test(uint256)'))), 0);

    }


    function three(){
        new bytes(0);
        new bytes(test3(1, test2()));
        new Test2(test2());
    }
    function test(uint a) payable{
        uint b;

        a = a + 1; 

        a = a + 1 + a;

        test(a);
        
        test(test2());

        a = test2() + 1;

        t.test.value(0)(a);

        t.test(a);
        st.t2.test(0);

        st.a.call();


        msg.sender.call.value(0)(bytes4(keccak256(('test(uint256)'))), 0);
        ret = msg.sender.call.value(0)();
        
        msg.sender.call.value(0).gas(0)();
        
        //#(b,a) = (0,1);
        
    }
    
    function test2() returns(uint){

    }


    function test3(uint, uint) returns(uint){
    }
}

contract Test2{

    constructor(uint){

    }

}
