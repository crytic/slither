import "./Initializable.sol";

contract Reinitializer is Initializable {
    address payable owner;

    function initialize() external reinitializer(2) {
        require(owner == address(0));
        owner = payable(msg.sender);
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}
