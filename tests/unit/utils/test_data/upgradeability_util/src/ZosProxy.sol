pragma solidity ^0.5.0;

contract ZosProxy {
  function () payable external {
    _fallback();
  }

  function _implementation() internal view returns (address);

  function _delegate(address implementation) internal {
    assembly {
      calldatacopy(0, 0, calldatasize)
      let result := delegatecall(gas, implementation, 0, calldatasize, 0, 0)
      returndatacopy(0, 0, returndatasize)
      switch result
      case 0 { revert(0, returndatasize) }
      default { return(0, returndatasize) }
    }
  }

  function _willFallback() internal {
  }

  function _fallback() internal {
    _willFallback();
    _delegate(_implementation());
  }
}

library AddressUtils {
  function isContract(address addr) internal view returns (bool) {
    uint256 size;
    assembly { size := extcodesize(addr) }
    return size > 0;
  }
}

contract UpgradeabilityProxy is ZosProxy {
  event Upgraded(address indexed implementation);

  bytes32 private constant IMPLEMENTATION_SLOT = 0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3;

  constructor(address _implementation) public payable {
    assert(IMPLEMENTATION_SLOT == keccak256("org.zeppelinos.proxy.implementation"));
    _setImplementation(_implementation);
  }

  function _implementation() internal view returns (address impl) {
    bytes32 slot = IMPLEMENTATION_SLOT;
    assembly {
      impl := sload(slot)
    }
  }

  function _upgradeTo(address newImplementation) internal {
    _setImplementation(newImplementation);
    emit Upgraded(newImplementation);
  }

  function _setImplementation(address newImplementation) private {
    require(AddressUtils.isContract(newImplementation), "Cannot set a proxy implementation to a non-contract address");
    bytes32 slot = IMPLEMENTATION_SLOT;
    assembly {
      sstore(slot, newImplementation)
    }
  }
}
