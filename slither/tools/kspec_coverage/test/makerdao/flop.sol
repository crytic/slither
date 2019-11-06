/// flop.sol -- Debt auction

// Copyright (C) 2018 Rain <rainbreak@riseup.net>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

pragma solidity 0.4.24;

import "./lib.sol";

contract VatLike {
    function move(address,address,uint) external;
}
contract GemLike {
    function mint(address,uint) external;
}

/*
   This thing creates gems on demand in return for dai.

 - `lot` gems for sale
 - `bid` dai paid
 - `gal` receives dai income
 - `ttl` single bid lifetime
 - `beg` minimum bid increase
 - `end` max auction duration
*/

contract Flopper is LibNote {
    // --- Auth ---
    mapping (address => uint) public wards;
    function rely(address usr) external note auth { wards[usr] = 1; }
    function deny(address usr) external note auth { wards[usr] = 0; }
    modifier auth { require(wards[msg.sender] == 1); _; }

    // --- Data ---
    struct Bid {
        uint256 bid;
        uint256 lot;
        address guy;  // high bidder
        uint48  tic;  // expiry time
        uint48  end;
    }

    mapping (uint => Bid) public bids;

    VatLike  public   vat;
    GemLike  public   gem;

    uint256  constant ONE = 1.00E18;
    uint256  public   beg = 1.05E18;  // 5% minimum bid increase
    uint256  public   pad = 1.50E18;  // 50% lot increase for tick
    uint48   public   ttl = 3 hours;  // 3 hours bid lifetime
    uint48   public   tau = 2 days;   // 2 days total auction length
    uint256  public kicks = 0;
    uint256  public live;

    // --- Events ---
    event Kick(
      uint256 id,
      uint256 lot,
      uint256 bid,
      address indexed gal
    );

    // --- Init ---
    constructor(address vat_, address gem_) public {
        wards[msg.sender] = 1;
        vat = VatLike(vat_);
        gem = GemLike(gem_);
        live = 1;
    }

    // --- Math ---
    function add(uint48 x, uint48 y) internal pure returns (uint48 z) {
        require((z = x + y) >= x);
    }
    function mul(uint x, uint y) internal pure returns (uint z) {
        require(y == 0 || (z = x * y) / y == x);
    }

    // --- Admin ---
    function file(bytes32 what, uint data) external note auth {
        if (what == "beg") beg = data;
        else if (what == "pad") pad = data;
        else if (what == "ttl") ttl = uint48(data);
        else if (what == "tau") tau = uint48(data);
        else revert();
    }

    // --- Auction ---
    function kick(address gal, uint lot, uint bid) external auth returns (uint id) {
        require(live == 1);
        require(kicks < uint(-1));
        id = ++kicks;

        bids[id].bid = bid;
        bids[id].lot = lot;
        bids[id].guy = gal;
        bids[id].end = add(uint48(now), tau);

        emit Kick(id, lot, bid, gal);
    }
    function tick(uint id) external note {
        require(bids[id].end < now);
        require(bids[id].tic == 0);
        bids[id].lot = mul(pad, bids[id].lot) / ONE;
        bids[id].end = add(uint48(now), tau);
    }
    function dent(uint id, uint lot, uint bid) external note {
        require(live == 1);
        require(bids[id].guy != address(0));
        require(bids[id].tic > now || bids[id].tic == 0);
        require(bids[id].end > now);

        require(bid == bids[id].bid);
        require(lot <  bids[id].lot);
        require(mul(beg, lot) <= mul(bids[id].lot, ONE));

        vat.move(msg.sender, bids[id].guy, bid);

        bids[id].guy = msg.sender;
        bids[id].lot = lot;
        bids[id].tic = add(uint48(now), ttl);
    }
    function deal(uint id) external note {
        require(live == 1);
        require(bids[id].tic != 0 && (bids[id].tic < now || bids[id].end < now));
        gem.mint(bids[id].guy, bids[id].lot);
        delete bids[id];
    }

    function cage() external note auth {
       live = 0;
    }
    function yank(uint id) external note {
        require(live == 0);
        require(bids[id].guy != address(0));
        vat.move(address(this), bids[id].guy, bids[id].bid);
        delete bids[id];
    }
}
