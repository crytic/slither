pragma solidity ^0.6.12;

// solidity source used by tests/test_function.py.
// tests/test_function.py tests that the functions below get translated into correct
// `slither.core.declarations.Function` objects or its subclasses
// and that these objects behave correctly.

contract TestFunction {
    bool entered = false;
    bytes32 public info;

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

contract TestFunctionCanSendEth {

    function send_direct() internal {
        address(1).send(1);
    }

    function transfer_direct() internal {
        address(1).transfer(1);
    }

    function call_direct() internal {
        address(1).call{value: 1}("");
    }

    function highlevel_call_direct() internal {
        TestFunctionCanSendEthOther(address(5)).i_am_payable{value: 1}();
    }

    function send_via_internal() public {
        send_direct();
    }

    function transfer_via_internal() public {
        transfer_direct();
    }

    function call_via_internal() public {
        call_direct();
    }

    function highlevel_call_via_internal() public {
        highlevel_call_direct();
    }

    function send_via_external() public {
        TestFunctionCanSendEthOther(address(5)).send_direct();
    }

    function transfer_via_external() public {
        TestFunctionCanSendEthOther(address(5)).transfer_direct();
    }

    function call_via_external() public {
        TestFunctionCanSendEthOther(address(5)).call_direct();
    }

    function highlevel_call_via_external() public {
        TestFunctionCanSendEthOther(address(5)).highlevel_call_direct();
    }
}

contract TestFunctionCanSendEthOther {
    function i_am_payable() external payable {

    }

    function send_direct() external {
        address(1).send(1);
    }

    function transfer_direct() external {
        address(1).transfer(1);
    }

    function call_direct() external {
        address(1).call{value: 1}("");
    }

    function highlevel_call_direct() external {
        TestFunctionCanSendEthOther(address(5)).i_am_payable{value: 1}();
    }
}
