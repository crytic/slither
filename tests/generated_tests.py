# This file was automatically generated

import pytest


@pytest.mark.xfail(strict=True, reason="#2274.")
def test_issue_2274(slither_from_solidity_source):
    source = """

// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.23;

contract Bar {
    constructor() { }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1688.")
def test_issue_1688(slither_from_solidity_source):
    source = """

	function test5(uint40 x) external view returns (uint256 res) {
		res = x * 50;
	}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1537.")
def test_issue_1537(slither_from_solidity_source):
    source = """

library Constants {
    uint8 constant value = [[1, 2], [3, 4]][0][0];
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2129.")
def test_issue_2129(slither_from_solidity_source):
    source = """

contract C {
    function test() external {
        uint z = msg.sender.code.length;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1851.")
def test_issue_1851(slither_from_solidity_source):
    source = """

contract A {
    function f(uint x) public {
        g(x > 0 ? 1 : 2, x > 1 ? 3 : 4);
    }
    function g(uint x, uint y) private {
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1223.")
def test_issue_1223(slither_from_solidity_source):
    source = """


pragma solidity ^0.8.2;
import '@openzeppelin/contracts/proxy/beacon/BeaconProxy.sol';

contract C {
  struct S {
      address o;
  }

  function test() public returns (bytes memory){
      bytes memory code = type(BeaconProxy).creationCode;

      return code;
  }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1622.")
def test_issue_1622(slither_from_solidity_source):
    source = """

git clone https://github.com/code-423n4/2023-01-timeswap
yarn
cd v2-token
slither .

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1199.")
def test_issue_1199(slither_from_solidity_source):
    source = """

 function addressToUint256(address a) public pure returns (uint256) {
      return uint256(uint160(a));
  }

abstract contract Example {
  
}


"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1910.")
def test_issue_1910(slither_from_solidity_source):
    source = """

contract Test {
    function test() external returns(bytes32) {
        bytes32 a = blockhash(block.number);
        return a;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1931.")
def test_issue_1931(slither_from_solidity_source):
    source = """

contract Test {
    function test() external {
        bytes32 a = 0;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2169.")
def test_issue_2169(slither_from_solidity_source):
    source = """
shell
Modifier WalletLibrary.onlyowner() (WalletLibrary.sol#84-87) does not always execute _; or revertModifier WalletLibrary.onlymanyowners(bytes32) (WalletLibrary.sol#91-94) does not always execute _; or revertReference: https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-modifier

Pragma version^0.4.9 (WalletLibrary.sol#12) allows old versions
solc-0.4.22 is known to contain severe issues (https://solidity.readthedocs.io/en/latest/bugs.html)Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-versions-of-solidity

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1704.")
def test_issue_1704(slither_from_solidity_source):
    source = """

pragma solidity ^0.8.4;

uint256 constant MAX = 1000;
error BadError(
               uint32[MAX] y
 );

contract VendingMachine {
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2307.")
def test_issue_2307(slither_from_solidity_source):
    source = """

library SafeMath {
    uint256 private constant twelve = 12; 
    struct A {uint256 a;}
    function add(A[twelve] storage z) internal { }
}

contract MathContract {
    uint256 private constant twelve = 12; 
    using SafeMath for SafeMath.A[12];
    SafeMath.A[12] public z;
    function safeAdd() public {
        z.add();
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1467.")
def test_issue_1467(slither_from_solidity_source):
    source = """
shell
https://github.com/beehive-innovation/rain-protocol/actions/runs/3456654052/jobs/5769538607

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2016.")
def test_issue_2016(slither_from_solidity_source):
    source = """

contract Test {
    function test() external {
        int[] memory a = new int[](5);
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1829.")
def test_issue_1829(slither_from_solidity_source):
    source = """

contract Contract {
    function foo(uint[] memory arr) public {
        uint[] memory arr2 = arr;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1708.")
def test_issue_1708(slither_from_solidity_source):
    source = """

pragma solidity 0.8.13;

contract A {

    function test(uint a) external returns(bool) {
        if (a < 50) return true;
        revert("a greater than 50");
        return false;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2037.")
def test_issue_2037(slither_from_solidity_source):
    source = """
shell
# Fractions do not support underscore separators (on Python <3.11)
        val = val.replace("_", "")
    
        if "e" in val or "E" in val:
>           base, expo = val.split("e") if "e" in val else val.split("E")
E           ValueError: too many values to unpack (expected 2)

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2122.")
def test_issue_2122(slither_from_solidity_source):
    source = """

pragma solidity 0.8.19;

contract OtherTest {
    struct Z {
        int x;
        int y;
    }

    function myfunc() external {
        DeleteTest.Z z = DeleteTest.Z.wrap(3);
    }
}

contract DeleteTest {
   type Z is int;
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2050.")
def test_issue_2050(slither_from_solidity_source):
    source = """

pragma solidity ^0.8.13;

struct A {
    uint256 z;
}

contract MyTest {
    A a;

    function test() external {
        uint a = a.z;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1966.")
def test_issue_1966(slither_from_solidity_source):
    source = """

library A {
    struct S {
        int x;
    }
}

contract Test {
    struct T {
        bytes payload;
    }

    function test(T calldata t) external {
        int z = abi.decode(t.payload, (A.S)).x + 3;
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1827.")
def test_issue_1827(slither_from_solidity_source):
    source = """

contract Contract {
    function foo() public returns (uint[2] memory, uint) {
        return ([uint(1), 2], 3);
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1923.")
def test_issue_1923(slither_from_solidity_source):
    source = """

pragma solidity ^0.8.19;

interface ISomeInterface {
    function value(uint z) external returns (uint, uint);
}

contract Test {

    function test(address a) external {
        (uint256 w, uint256 x) = ISomeInterface(a).value(3);
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1436.")
def test_issue_1436(slither_from_solidity_source):
    source = """
shell
AFeed._likePost(uint256) (contracts/feeds/AFeed.sol#58-93) uses timestamp for comparisons
        Dangerous comparisons:
        - require(bool,string)(postIdx < posts.length,Post does not exist)(contracts/feeds/AFeed.sol#59)
Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#1810.")
def test_issue_1810(slither_from_solidity_source):
    source = """
shell
INFO:Printers:Contract IERC2981
        Function IERC2981.test() (*)
Contract Test
        Function Test.supportsInterface(bytes4) (*)
                Expression: interfaceId == type()(IERC2981).interfaceId
                IRs:
                        TMP_0(type(IERC2981)) = SOLIDITY_CALL type()(IERC2981)
                        REF_0 (->None) := 4171824493(bytes4)
                        TMP_1(bool) = interfaceId == REF_0
                        RETURN TMP_1

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2192.")
def test_issue_2192(slither_from_solidity_source):
    source = """
Vyper
var:uint256

@internal
def bar(a:uint256):
    pass
    self.var = 2

@external
def foo():
    self.bar(2)


"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2089.")
def test_issue_2089(slither_from_solidity_source):
    source = """

library Lib {
    function proj0(uint[3] memory a) external returns(uint) {
        return a[0];
    }
}

contract Test {
    uint constant NUM_PHASES = 3;

    using Lib for uint[3];

    function test(uint[NUM_PHASES] memory z) external {
        z.proj0();
    }
}

"""

    slither_from_solidity_source(source)


@pytest.mark.xfail(strict=True, reason="#2100.")
def test_issue_2100(slither_from_solidity_source):
    source = """

pragma solidity ^0.8.0;

contract Test {
    function f(bytes32 p0) internal pure {
        assembly {
            function g(w) {
                let length := 0
            }
            g(p0)
        }
    }
    function f(bytes32 p0, bytes32 p1) internal pure {
        assembly {
            function g(w, x) {
                let length := 0
            }
            g(p0, p1)
        }
    }
}

"""

    slither_from_solidity_source(source)


if __name__ == "__main__":
    pytest.main(["generated_tests.py", "-v"])
