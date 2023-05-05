library L {

}
uint256 constant offset = 100;

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
            sstore(offset, 0)
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
            mstore(offset, 0)

            let aStoreC := mul(sload(storC.slot), storC.offset)

            // let libAddr := L // Not supported for now
        }
    }


    struct St{
        uint a;
    }

    function f() internal returns(St storage st){
        assembly{
            st.slot := 0x0000000000000000000000000000000000000000000000000000000000000000
        }
    }

}

// function from https://docs.soliditylang.org/en/v0.8.0/assembly.html
function at(address _addr) view returns (bytes memory o_code) {
    assembly {
        // retrieve the size of the code, this needs assembly
        let size := extcodesize(_addr)
        // allocate output byte array - this could also be done without assembly
        // by using o_code = new bytes(size)
        o_code := mload(0x40)
        // new "memory end" including padding
        mstore(0x40, add(o_code, and(add(add(size, 0x20), 0x1f), not(0x1f))))
        // store length in memory
        mstore(o_code, size)
        // actually retrieve the code, this needs assembly
        extcodecopy(_addr, add(o_code, 0x20), 0, size)
    }
}


function test(){

	assembly {
		let v
	}

	assembly {
		let v := "test"
	}

}

