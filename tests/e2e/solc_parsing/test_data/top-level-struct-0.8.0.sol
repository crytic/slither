struct my_struct {
    uint[][] a; // works fine
    uint[][3] b; // works fine
    uint[3][] c; // fails
    uint[3][3] d; // fails
    uint[2**20] e; // works fine
}
contract BaseContract{
    struct my_struct_2 {
        uint[][] f; // works fine
        uint[][3] g; // works fine
        uint[3][] h; // works fine
        uint[3][3] i; // works fine
        uint[2**20] j; // works fine
    }
    
    uint[3][] k; // works fine
}
