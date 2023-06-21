contract X {

}
contract TestScope {
    function scope(uint256 x) public {
        uint checked1 = x - x; 
        unchecked {
            uint unchecked1 = x - x;
            if (true) {
                uint unchecked2 = x - x;

            }
            for (uint i = 0; i < 10; i++) {
                uint unchecked3 = x - x;

            }
        }
        uint checked2 = x - x; 
        try new X() {
            unchecked {
                uint unchecked4 = x - x;
            }
            uint checked3 = x - x;
        } catch {
            unchecked {
                uint unchecked5 = x - x;
            }
            uint checked4 = x - x;
        }
        while (true) {
            unchecked {
                uint unchecked6 = x - x;
            }
            uint checked5 = x - x;
        }
    }
}