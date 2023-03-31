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
            let aStorA := sload(storA_slot)
            let aParamA := paramA
            let aRetA := retA
            let aLocalA := localA

            sstore(storA_slot, 0)
            paramA := 0
            retA := 0
            localA := 0

            let aStorB := sload(storB_slot)
            let aParamB := mload(paramB)
            let aRetB := mload(retB)
            let aLocalB := mload(localB)

            sstore(storB_slot, 0)
            mstore(paramB, 0)
            mstore(retB, 0)
            mstore(localB, 0)

            let aStoreC := mul(sload(storC_slot), storC_offset)

            // let libAddr := L // Not supported for now
        }
    }
}
