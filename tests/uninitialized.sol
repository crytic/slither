contract Uninitialized{


    address destination;

    function transfer() payable{
    
        destination.transfer(msg.value);
    }

}
