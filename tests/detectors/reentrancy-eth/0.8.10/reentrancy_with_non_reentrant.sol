interface Receiver{
    function send_funds() payable external;
}

contract TestWithBug{

    mapping(address => uint) balances;

    modifier nonReentrant(){
        _;
    }

    function withdraw(uint amount) nonReentrant public{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

    function withdraw_all() public{
         uint amount = balances[msg.sender];
         balances[msg.sender] = 0;
         Receiver(msg.sender).send_funds{value: amount}();
    }

}


contract TestWithoutBug{

    mapping(address => uint) balances;

    modifier nonReentrant(){
        _;
    }

    function withdraw(uint amount) nonReentrant public{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

    function withdraw_all() nonReentrant public{
         uint amount = balances[msg.sender];
         balances[msg.sender] = 0;
         Receiver(msg.sender).send_funds{value: amount}();
    }

}

contract TestWithBugInternal{

    mapping(address => uint) balances;

    modifier nonReentrant(){
        _;
    }

    function withdraw(uint amount) nonReentrant public{
        withdraw_internal(amount);
    }

    function withdraw_internal(uint amount) internal{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

    function withdraw_all() public{
        withdraw_all_internal();
    }

    function withdraw_all_internal() internal {
         uint amount = balances[msg.sender];
         balances[msg.sender] = 0;
         Receiver(msg.sender).send_funds{value: amount}();
    }

}

contract TestWithoutBugInternal{

    mapping(address => uint) balances;

    modifier nonReentrant(){
        _;
    }

    function withdraw(uint amount) nonReentrant public{
        withdraw_internal(amount);
    }

    function withdraw_internal(uint amount) internal{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

    function withdraw_all() nonReentrant public{
        withdraw_all_internal();
    }

    function withdraw_all_internal() internal {
         uint amount = balances[msg.sender];
         balances[msg.sender] = 0;
         Receiver(msg.sender).send_funds{value: amount}();
    }

}

contract TestBugWithPublicVariable{

    mapping(address => uint) public balances;

    modifier nonReentrant(){
        _;
    }

    function withdraw(uint amount) nonReentrant public{
        withdraw_internal(amount);
    }

    function withdraw_internal(uint amount) internal{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

}

contract TestWithBugNonReentrantRead{

    mapping(address => uint) balances;

    modifier nonReentrant(){
        _;
    }

    function withdraw(uint amount) nonReentrant public{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

    // Simulate a reentrancy that allows to read variable in a potential incorrect state during a reentrancy
    // This is more likely to impact protocol like reentrancy
    function read() public returns(uint){
         uint amount = balances[msg.sender];
         return amount;
    }

}
