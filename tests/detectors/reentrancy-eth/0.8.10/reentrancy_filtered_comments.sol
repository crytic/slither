interface Receiver{
    function send_funds() payable external;
}

contract TestWithBug{
    mapping(address => uint) balances;

    function withdraw(uint amount) public{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }

    // slither-disable-start all
    function withdrawFiltered(uint amount) public{
         require(amount <= balances[msg.sender]);
         Receiver(msg.sender).send_funds{value: amount}();
         balances[msg.sender] -= amount;
    }
    // slither-disable-end all
}

