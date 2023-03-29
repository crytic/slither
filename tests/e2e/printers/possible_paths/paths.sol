contract A{
    function destination() private{

    }

    function call() public{
        destination();
    }
}

contract B{


    function call2(A a) public{
        a.call();
    }
} 
