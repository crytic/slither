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
            let aParamA := paramA
            let aRetA := retA
            let aLocalA := localA

            paramA := 0
            retA := 0
            localA := 0

            let aParamB := mload(paramB)
            let aRetB := mload(retB)
            let aLocalB := mload(localB)

            mstore(paramB, 0)
            mstore(retB, 0)
            mstore(localB, 0)

            let libAddr := L
        }
    }
}