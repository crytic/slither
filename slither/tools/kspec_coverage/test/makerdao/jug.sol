pragma solidity 0.4.24;
pragma experimental ABIEncoderV2;

import "./lib.sol";

contract VatLike {
    struct Ilk {
        uint256 Art;   // wad
        uint256 rate;  // ray
    }
    function ilks(bytes32) external returns (Ilk memory);
    function fold(bytes32,address,int) external;
}

contract Jug is LibNote {
    // --- Auth ---
    mapping (address => uint) public wards;
    function rely(address usr) external note auth { wards[usr] = 1; }
    function deny(address usr) external note auth { wards[usr] = 0; }
    modifier auth { require(wards[msg.sender] == 1); _; }

    // --- Data ---
    struct Ilk {
        uint256 duty;
        uint256  rho;
    }

    mapping (bytes32 => Ilk) public ilks;
    VatLike                  public vat;
    address                  public vow;
    uint256                  public base;

    // --- Init ---
    constructor(address vat_) public {
        wards[msg.sender] = 1;
        vat = VatLike(vat_);
    }

    // --- Math ---
    function rpow(uint x, uint n, uint b) internal pure returns (uint z) {
      assembly {
        switch x case 0 {switch n case 0 {z := b} default {z := 0}}
        default {
          switch mod(n, 2) case 0 { z := b } default { z := x }
          let half := div(b, 2)  // for rounding.
          for { n := div(n, 2) } n { n := div(n,2) } {
            let xx := mul(x, x)
            if iszero(eq(div(xx, x), x)) { revert(0,0) }
            let xxRound := add(xx, half)
            if lt(xxRound, xx) { revert(0,0) }
            x := div(xxRound, b)
            if mod(n,2) {
              let zx := mul(z, x)
              if and(iszero(iszero(x)), iszero(eq(div(zx, x), z))) { revert(0,0) }
              let zxRound := add(zx, half)
              if lt(zxRound, zx) { revert(0,0) }
              z := div(zxRound, b)
            }
          }
        }
      }
    }
    uint256 constant ONE = 10 ** 27;
    function add(uint x, uint y) internal pure returns (uint z) {
        z = x + y;
        require(z >= x);
    }
    function diff(uint x, uint y) internal pure returns (int z) {
        z = int(x) - int(y);
        require(int(x) >= 0 && int(y) >= 0);
    }
    function rmul(uint x, uint y) internal pure returns (uint z) {
        z = x * y;
        require(y == 0 || z / y == x);
        z = z / ONE;
    }

    // --- Administration ---
    function init(bytes32 ilk) external note auth {
        Ilk storage i = ilks[ilk];
        require(i.duty == 0);
        i.duty = ONE;
        i.rho  = now;
    }
    function file(bytes32 ilk, bytes32 what, uint data) external note auth {
        require(now == ilks[ilk].rho);
        if (what == "duty") ilks[ilk].duty = data;
        else revert();
    }
    function file(bytes32 what, uint data) external note auth {
        if (what == "base") base = data;
        else revert();
    }
    function file(bytes32 what, address data) external note auth {
        if (what == "vow") vow = data;
        else revert();
    }

    // --- Stability Fee Collection ---
    function drip(bytes32 ilk) external note {
        require(now >= ilks[ilk].rho);
        VatLike.Ilk memory i = vat.ilks(ilk);
        vat.fold(ilk, vow, diff(rmul(rpow(add(base, ilks[ilk].duty), now - ilks[ilk].rho, ONE), i.rate), i.rate));
        ilks[ilk].rho = now;
    }
}
