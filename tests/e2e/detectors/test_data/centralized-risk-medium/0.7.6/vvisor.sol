// SPDX-License-Identifier: BUSL-1.1
// SPDX-License-Identifier: GPL-3.0-only
pragma solidity 0.7.6;
pragma abicoder v2;

interface IVisor {
    function owner() external returns(address);
    function delegatedTransferERC20( address token, address to, uint256 amount) external;
    function mint() external;
}

// @title Rewards Hypervisor
// @notice fractionalize balance 
contract RewardsHypervisor {

    address public owner;
    address vvisr=address(0);
    address visr=address(0);
    modifier onlyOwner {
        require(msg.sender == owner, "only owner");
        _;
    }


    // @param visr Amount of VISR transfered from sender to Hypervisor
    // @param to Address to which liquidity tokens are minted
    // @param from Address from which tokens are transferred 
    // @return shares Quantity of liquidity tokens minted as a result of deposit
    function deposit(
        uint256 visrDeposit,
        address payable from,
        address to
    ) external returns (uint256 shares) {
        require(visrDeposit > 0, "deposits must be nonzero");
        require(to != address(0) && to != address(this), "to");
        require(from != address(0) && from != address(this), "from");

        shares = visrDeposit;

        require(IVisor(from).owner() == msg.sender); 
        IVisor(from).delegatedTransferERC20(address(visr), address(this), visrDeposit);
        IVisor(address(0)).mint();

        
    }
}