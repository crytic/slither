contract Test{

    mapping(uint => mapping(uint => address)) authorized_destination;

    address destination;

    function init(){
        authorized_destination[0][0] = msg.sender;
    }

    function setup(uint idx){
        destination = authorized_destination[0][0];
    }

    function withdraw(){
        destination.transfer(this.balance);
    }
}
