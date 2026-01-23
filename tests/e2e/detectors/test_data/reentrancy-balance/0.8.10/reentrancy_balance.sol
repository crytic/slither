// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

interface IExternalCall {
    function pay(uint256 amount) external;
}

contract ReentrancyBalanceTest {
    error IncorrectAmountReceived();

    IERC20 private token;

    function getBalance() internal view returns (uint256) {
        return token.balanceOf(address(this));
    }

    // Bad: balance read before external call, stale balance used in condition after
    function bad1(IERC20 tk) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        IExternalCall(msg.sender).pay(amount_to_pay);
        require(
            tk.balanceOf(address(this)) - balance_before >= amount_to_pay,
            "Insufficient balance"
        );
    }

    // Bad: internal function contains external call
    function bad2(IERC20 tk) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        internalCall();
        if (tk.balanceOf(address(this)) - balance_before > amount_to_pay) {
            revert IncorrectAmountReceived();
        }
    }

    function internalCall() internal {
        IExternalCall(msg.sender).pay(8);
    }

    // Bad: low-level call
    function bad3(IERC20 tk) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        (bool success, ) = msg.sender.call("");
        require(success);
        if (tk.balanceOf(address(this)) - balance_before > amount_to_pay) {
            revert IncorrectAmountReceived();
        }
    }

    // Bad: conditional external call
    function bad4(IERC20 tk, bool should_pay) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        if (should_pay) {
            IExternalCall(msg.sender).pay(amount_to_pay);
        }
        if (tk.balanceOf(address(this)) - balance_before > amount_to_pay) {
            revert IncorrectAmountReceived();
        }
    }
    // Bad: balance read via internal function wrapper
    function bad5() public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = getBalance();
        IExternalCall(msg.sender).pay(amount_to_pay);
        require(getBalance() - balance_before >= amount_to_pay);
    }

    // Bad: balance read before external call used in condition
    function bad6(IERC20 tk) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        IExternalCall(msg.sender).pay(amount_to_pay);
        uint balance_after = tk.balanceOf(address(this));
        require(
            balance_after - balance_before >= amount_to_pay,
            "Insufficient balance"
        );
    }

    // Good: balance_before not used after external call in condition
    function good(IERC20 tk) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        IExternalCall(msg.sender).pay(amount_to_pay);
        require(tk.balanceOf(address(this)) > amount_to_pay);
    }

    // Good: balance_after is used in condition
    function good2(IERC20 tk) public {
        uint256 amount_to_pay = 100;
        uint256 balance_before = tk.balanceOf(address(this));
        IExternalCall(msg.sender).pay(amount_to_pay);
        uint256 balance_after = tk.balanceOf(address(this));
        require(balance_after > amount_to_pay);
    }

}
