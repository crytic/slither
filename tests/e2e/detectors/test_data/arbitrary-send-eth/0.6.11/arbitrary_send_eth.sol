contract Test{

    address payable destination;
    address payable immutable destination_imm;
    mapping (address => uint) balances;

    constructor() public{
        destination_imm = payable(msg.sender);
        balances[msg.sender] = 0;
    }

    function send_immutable() public{
        destination_imm.send(address(this).balance);
    }

    function direct() public{
        msg.sender.send(address(this).balance);
    }

    function init() public{
        destination = msg.sender;
    }

    function indirect() public{
        destination.send(address(this).balance);
    }

    // these are legitimate calls
    // and should not be detected
    function repay() payable public{
        msg.sender.transfer(msg.value);
    }

    function withdraw() public{
        uint val = balances[msg.sender];
        msg.sender.send(val);
    }

    function buy() payable public{
        uint value_send = msg.value;
        uint value_spent = 0 ; // simulate a buy of tokens
        uint remaining = value_send - value_spent;
        msg.sender.send(remaining);
}

}
