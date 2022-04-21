pragma solidity 0.6.11;

library SafeERC20 {
    function safeTransferFrom(IERC20 token, address from, address to, uint256 value) internal {}
}

interface IERC20 {
    function transferFrom(address, address, uint256) external returns(bool);
    function permit(address, address, uint256, uint256, uint8, bytes32, bytes32) external;
}

contract ERC20 is IERC20 {
    function transferFrom(address from, address to, uint256 amount) external override returns(bool) {
        return true;
    }
    function permit(address owner, address spender, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s) external override {}
}

contract C {
    using SafeERC20 for IERC20;

    IERC20 erc20;
    address notsend;
    address send;

    constructor() public {
        erc20 = new ERC20();
        notsend = address(0x3);
        send = msg.sender;
    }

    function bad1(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) public {
        erc20.permit(from, address(this), value, deadline, v, r, s);
        erc20.transferFrom(from, to, value);
    }

    // This is not detected
    function bad2(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) public {
        int_transferFrom(from,value, deadline, v, r, s, to);
    }

    function int_transferFrom(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) internal {
        erc20.permit(from, address(this), value, deadline, v, r, s);
        erc20.transferFrom(from, to, value);
    }

    function bad3(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) external {
        erc20.permit(from, address(this), value, deadline, v, r, s);
        erc20.safeTransferFrom(from, to, value);
    }    

    function bad4(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) external {
        erc20.permit(from, address(this), value, deadline, v, r, s);
        SafeERC20.safeTransferFrom(erc20, from, to, value);
    }

}
