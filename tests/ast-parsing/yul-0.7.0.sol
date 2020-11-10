library L {

}

contract C {
    uint storA;
    uint[] storB;
    bool storC;

    function f(uint paramA, uint[] memory paramB) public returns (uint retA, uint[] memory retB) {
        uint localA;
        uint[] memory localB;

        assembly {
            let aStorA := sload(storA.slot)
            let aParamA := paramA
            let aRetA := retA
            let aLocalA := localA

            sstore(storA.slot, 0)
            paramA := 0
            retA := 0
            localA := 0

            let aStorB := sload(storB.slot)
            let aParamB := mload(paramB)
            let aRetB := mload(retB)
            let aLocalB := mload(localB)

            sstore(storB.slot, 0)
            mstore(paramB, 0)
            mstore(retB, 0)
            mstore(localB, 0)

            let aStoreC := mul(sload(storC.slot), storC.offset)

            let libAddr := L
        }
    }
}