// overwrite abi and bin:
// solc tests/storage-layout/storage_layout-0.8.33.sol --abi --bin -o tests/storage-layout --overwrite
uint constant OFFSET = 1;

contract B layout at 0x10 + OFFSET {
    uint _q;
    uint _w;
}
