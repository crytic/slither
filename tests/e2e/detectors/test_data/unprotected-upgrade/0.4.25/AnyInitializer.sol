import "./Initializable.sol";

contract AnyInitializer is Initializable {
    address owner;

    function anyName() external initializer {
        require(owner == address(0));
        owner = msg.sender;
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}
