contract CallInLoop{

    address[] destinations;

    constructor(address[] memory newDestinations) public{
        destinations = newDestinations;
    }

    function bad() external{
        for (uint i=0; i < destinations.length; i++){
            address(uint160(destinations[i])).transfer(i);
        }
    }

}
