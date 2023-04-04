contract CallInLoopBase {

    address[] destinations_base;
    
    constructor(address[] newDestinations) public {
        destinations_base = newDestinations;
    }

    function bad_base() external{
        for (uint i=0; i < destinations_base.length; i++){
            destinations_base[i].transfer(i);
        }
    }
}

contract CallInLoop is CallInLoopBase{

    address[] destinations;

    constructor(address[] newDestinations) CallInLoopBase(newDestinations) public{
        destinations = newDestinations;
    }

    function bad() external{
        for (uint i=0; i < destinations.length; i++){
            destinations[i].transfer(i);
        }
    }

    function bad2() external {
        for (uint i=0; i < destinations.length; i++){
            for (uint j=0; j < destinations.length; j++){
                // Do something
            }    
            destinations[i].transfer(i);
        }
    }

    function bad3() external {
        for (uint i=0; i < destinations.length; i++){   
            bad3_internal(destinations[i], i);
        }
    }

    function bad3_internal(address a, uint i) internal {
        a.transfer(i);
    }

}
