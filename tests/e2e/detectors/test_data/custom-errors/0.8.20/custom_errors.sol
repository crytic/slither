// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

contract CustomErrorsCases {
    error Denied();
    modifier allowed(bool ok) { require(ok, "modifier"); _; } // positive
    function guarded(bool ok) external pure allowed(ok) {}

    function literalRequire(bool ok) external pure {
        require(ok, "denied"); // positive
    }

    function literalRevert() external pure {
        revert("denied"); // positive
    }

    function alreadyCustom(bool ok) external pure {
        if (!ok) revert Denied();
    }

    function dynamicMessage(bool ok, string memory message) external pure {
        require(ok, message);
    }

    function dynamicRevert(string memory message) external pure { revert(message); }
    function bareRevert() external pure { revert(); }
    function bareRequire(bool ok) external pure { require(ok); }
    function emptyMessage(bool ok) external pure { require(ok, ""); }
    function unrelated(string memory reason) external pure returns (string memory) { return reason; }
}

function topLevelRequire(bool ok) pure { require(ok, "top level"); } // positive

contract ParentErrors {
    function inheritedRevert(bool ok) public pure { require(ok, "inherited"); }
}
contract ChildErrors is ParentErrors {}
