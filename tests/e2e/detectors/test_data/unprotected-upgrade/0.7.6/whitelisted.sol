import "./Initializable.sol";
import "./OnlyProxy.sol";
import "./OnlyDelegateCall.sol";

contract Whitelisted is Initializable, OnlyProxy{
    address payable owner;

    function initialize() external initializer onlyProxy {
        owner = msg.sender;
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}

contract WhitelistedDelegateCall is Initializable, OnlyDelegateCall{
    address payable owner;

    function initialize() external initializer onlyDelegateCall {
        owner = msg.sender;
    }

    function kill() external {
        require(msg.sender == owner);
        selfdestruct(owner);
    }
}
