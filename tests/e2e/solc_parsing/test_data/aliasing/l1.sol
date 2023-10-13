import "./l2.sol" as L2;
import {MyErr as MyImportError} from "./l3.sol";

type fd is uint;
error MyError();
uint constant qwe = 34;

struct SS {
 uint g;
}

enum MyEnum {
 A,
 B
}

function tpf(MyEnum p) returns(uint) {return 4;}
function tpf(fd p) pure returns(uint) {return 4;}
function tpf(uint e, SS memory g) view returns(uint) {return 4;}

library MyC {
 function callme() public {}

}
