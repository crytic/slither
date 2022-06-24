import "./Initializable.sol";
import "./OnlyProxy.sol";

contract Whitelisted is Initializable, OnlyProxy{
    address owner;

    function initialize() external initializer onlyProxy {
        owner = msg.sender;
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}
