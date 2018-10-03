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

    function repay() payable{
        msg.sender.transfer(msg.value);
    }

    function withdraw(){
        msg.sender.send(balances[msg.sender]);
    }

}
