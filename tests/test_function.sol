pragma solidity ^0.6.12;

// solidity source used by tests/test_function.py.
// tests/test_function.py tests that the functions below get translated into correct
// `slither.core.declarations.Function` objects or its subclasses
// and that these objects behave correctly.

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

    function external_send(uint8 _c) external {
        require(!entered);
        entered = true;
        msg.sender.call{value: 1}("");
    }

    function internal_assembly(bytes calldata _d) internal returns (uint) {
        uint256 chain;
        assembly {
            chain := chainid()
        }
        return chain;
    }

    fallback() external {

    }

    receive() external payable {

    }

    constructor(address payable _e) public payable {

    }

    function private_view() private view returns (bool) {
        return entered;
    }

    function public_pure() public pure returns (bool) {
        return true;
    }
}
