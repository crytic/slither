type Bitmap is uint256;

function getBit(Bitmap bm, uint8 index) returns (bool) {
    uint256 mask = 1 << index;
    return Bitmap.unwrap(bm) & mask!=0;
}
using {getBit} for Bitmap global;

contract TopLevelUsingFor {
    mapping(address => Bitmap) permission;
    Bitmap testMap;
    function canDoThing() public returns(bool) {
        Bitmap callerBitmap = permission[msg.sender];
        uint test = 33;
        return callerBitmap.getBit(1);
    }
    function canTry() public returns(bool) {
        return getBit(testMap,1);
    }
}

