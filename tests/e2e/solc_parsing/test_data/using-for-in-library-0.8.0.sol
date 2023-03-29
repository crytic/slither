
library A {
    using B for uint256;
    
    function a(uint256 v) public view returns (uint) {
        return v.b();
    }
}

library B {
    function b(uint256 v) public view returns (uint) {
        return 1;
    }
}
