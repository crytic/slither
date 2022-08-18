import "./Initializable.sol";

contract Fixed is Initializable{
    address payable owner;

    constructor() {
        owner = payable(msg.sender);
    }

    function initialize() external initializer{
        require(owner == address(0));
        owner = payable(msg.sender);

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

    constructor() {
        owner = payable(msg.sender);
    }

    function initialize() external initializer{
        require(owner == address(0));
        owner = payable(msg.sender);
    }
}

contract Fixed2 is Initializable {
    address payable owner;

    constructor() initializer {}

    function initialize() external initializer {
        require(owner == address(0));
        owner = payable(msg.sender);
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}

contract Fixed3 is Initializable {
    address payable owner;

    constructor() {
        _disableInitializers();
    }

    function initialize() external initializer {
        require(owner == address(0));
        owner = payable(msg.sender);
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}