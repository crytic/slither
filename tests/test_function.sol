pragma solidity ^0.6.12;

// solidity source used by tests/test_function.py.
// tests/test_function.py tests that the functions
// below get

contract TestFunction {
    bool entered = false;

    function external_payable(uint _a) external payable returns (uint) {
        return 1;
    }

    function public_reenter() public {
        msg.sender.call("");
    }

    function public_payable_reenter_send(bool _b) public payable {
        msg.sender.call{value: 1}("");
    }

    function external_send(uint _a) external {
        require(!entered);
        entered = true;
        msg.sender.call{value: 1}("");
    }

    function _internal(uint _a) internal returns (uint) {
        uint256 chain;
        assembly {
            chain := chainid()
        }
        return chain;
    }

    fallback() external {

    }
}
