import "./Initializable.sol";

contract NativeCallcode is Initializable{
    address owner;

    function initialize() external initializer{
        require(owner == address(0));
        owner = msg.sender;
    }
    function execute(address target, bytes data) external{
        require(msg.sender == owner);
        require(target.callcode(data));
    }
}
