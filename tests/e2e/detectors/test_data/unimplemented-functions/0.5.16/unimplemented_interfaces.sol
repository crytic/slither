/* Interfaces */
interface ISomething0 {
  function sth1(uint256) external;
}

interface ISomething1 {
  function sth1(uint256) external;
  function sth2(bytes calldata) external;
}

interface ISomething2 {
  function sth(uint256) external;
}

interface ISomething3 {
  function sth1(uint256) external;
  function sth2(bool) external;
}

interface ISomething4 {
  function sth1(uint256) external;
  function sth2(bool) external;
  function sth3(bytes calldata) external;
}

interface ISomething5 {
  function sth(uint256) external;
  function sth1(uint256) external;
}



/* Contracts */

contract bad0 { // forgets to say it is ISomething1
  function sth1(uint256 x) external {}
  function sth2(bytes calldata y) external {}
}

contract bad1 { // forgets to say it is ISomething4
  function sth1(uint256 x) external {}
  function sth2(bool b) external {}
  function sth3(bytes calldata y) external {}
}

contract bad2 is ISomething3 { // forgets to say it is ISomething4 which is a superset of ISomething3
  function sth1(uint256 x) external {}
  function sth2(bool b) external {}
  function sth3(bytes calldata y) external {}
}

contract good0 is ISomething2 {
  function sth(uint256 x) external {}
}

/* Implements ISomething5 which is a superset of ISomething0 and ISomething2 */
contract good1 is ISomething5 {
  function sth(uint256 x) external {}
  function sth1(uint256 x) external {}
}

/* good2_i is not an Interface because sth5 is not external */
contract bad3_i {
  function sth4(uint256 x) external;
  function sth5(uint256 x) public;
}

contract bad3 {
  function sth4(uint256 x) external {}
  function sth5(uint256 x) public {}
}

