import "./Initializable.sol";

contract AssemblyDelegatecall is Initializable{
    address payable owner;

    function initialize() external initializer{
        require(owner == address(0));
        owner = payable(msg.sender);
    }
    function execute(address target) external{
        require(msg.sender == owner);
        assembly {
            let success := delegatecall(gas(), target, 0, 0, 0, 0)
            if iszero(success) { revert(0, 0) }
        }
    }
}

contract AssemblyCallcode is Initializable{
    address payable owner;

    function initialize() external initializer{
        require(owner == address(0));
        owner = payable(msg.sender);
    }
    function execute(address target) external{
        require(msg.sender == owner);
        assembly {
            let success := callcode(gas(), target, 0, 0, 0, 0, 0)
            if iszero(success) { revert(0, 0) }
        }
    }
}

contract AssemblySelfdestruct is Initializable{
    address payable owner;

    function initialize() external initializer{
        require(owner == address(0));
        owner = payable(msg.sender);
    }
    function kill() external{
        require(msg.sender == owner);
        assembly {
            selfdestruct(caller())
        }
    }
}
