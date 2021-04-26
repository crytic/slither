import "./Initializable.sol";

contract Buggy is Initializable{
    address payable owner;

    function initialize() external initializer{
        require(owner == address(0));
        owner = msg.sender;
    }
    function kill() external{
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}