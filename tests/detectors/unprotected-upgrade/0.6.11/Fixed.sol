import "./Initializable.sol";

contract Fixed is Initializable{
    address payable owner;

    constructor() public{
        owner = msg.sender;
    }

    function initialize() external initializer{
        require(owner == address(0));
        owner = msg.sender;
    }
    function kill() external{
        require(msg.sender == owner);
        selfdestruct(owner);
    }

    function other_function() external{

    }
}


contract Not_Upgradeable{
}

contract UpgradeableNoDestruct is Initializable{
    address payable owner;

    constructor() public{
        owner = msg.sender;
    }

    function initialize() external initializer{
        require(owner == address(0));
        owner = msg.sender;
    }
}

contract Fixed2 is Initializable {
    address payable owner;

    constructor() public initializer {}

    function initialize() external initializer {
        require(owner == address(0));
        owner = msg.sender;
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}