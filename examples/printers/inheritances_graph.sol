contract Contract1{

    uint myvar;

    function myfunc() public{}
}

contract Contract2{

    uint public myvar2;

    function myfunc2() public{}

    function privatefunc() private{}
}

contract Contract3 is Contract1, Contract2{

    function myfunc() public{} // override myfunc

}
