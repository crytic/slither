contract Test{

    address destination;

    mapping (address => uint) balances;

    constructor(){
        balances[msg.sender] = 0;
    }

    function direct(){
        msg.sender.send(this.balance);
    }

    function init(){
        destination = msg.sender;
    }

    function indirect(){
        destination.send(this.balance);
    }

    // these are legitimate calls
    // and should not be detected
    function repay() payable{
        msg.sender.transfer(msg.value);
    }

    function withdraw(){
        uint val = balances[msg.sender];
        msg.sender.send(val);
    }

    function buy() payable{
        uint value_send = msg.value;
        uint value_spent = 0 ; // simulate a buy of tokens
        uint remaining = value_send - value_spent;
        msg.sender.send(remaining);
}

}
