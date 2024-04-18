import "./l2.sol" as L2;




uint constant qwe = 34;

struct SS {
 uint g;
}

enum MyEnum {
 A,
 B
}

function tpf(MyEnum p) returns(uint) {return 4;}

function tpf(uint e, SS memory g) view returns(uint) {return 4;}

library MyC {
 function callme() public {}

}
