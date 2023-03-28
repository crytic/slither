pragma solidity ^0.5.0;

contract Owned {
    address public owner;

    constructor(address _owner) public {
        require(_owner != address(0), "Owner address cannot be 0");
        owner = _owner;
    }

    modifier onlyOwner {
        require(msg.sender == owner, "Only the contract owner may perform this action");
        _;
    }
}

contract Proxyable is Owned {
    /* The proxy this contract exists behind. */
    SynthProxy public proxy;

    constructor(address payable _proxy) internal {
        // This contract is abstract, and thus cannot be instantiated directly
        require(owner != address(0), "Owner must be set");

        proxy = SynthProxy(_proxy);
    }

    function setProxy(address payable _proxy) external onlyOwner {
        proxy = SynthProxy(_proxy);
    }
}


contract SynthProxy is Owned {
    Proxyable public target;

    constructor(address _owner) public Owned(_owner) {}

    function setTarget(Proxyable _target) external onlyOwner {
        target = _target;
    }

    // solhint-disable no-complex-fallback
    function() external payable {
        assembly {
            calldatacopy(0, 0, calldatasize)

            /* We must explicitly forward ether to the underlying contract as well. */
            let result := delegatecall(gas, sload(target_slot), 0, calldatasize, 0, 0)
            returndatacopy(0, 0, returndatasize)

            if iszero(result) {
                revert(0, returndatasize)
            }
            return(0, returndatasize)
        }
    }
}
