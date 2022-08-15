enum Enum { A, B, C, D }

contract MinMax {
    uint a = type(uint).max;
    uint b = type(uint).min;
    uint c = uint(type(Enum).min);
    uint d =  uint(type(Enum).max);

    int constant e = type(int).max;
    int constant f = type(int).min;
    uint constant g = uint(type(Enum).max);
    uint constant h = uint(type(Enum).min);

    uint8 immutable i;
    uint8 immutable j;
    uint immutable k;
    uint immutable l;

    constructor() {
        i =  type(uint8).max;
        j = type(uint8).min;
        k =  uint(type(Enum).max);
        l =  uint(type(Enum).min);
    }

    function min() public returns(uint) { return uint(type(Enum).min); }
    function max() public returns(uint) { return uint(type(Enum).max); }
}    

