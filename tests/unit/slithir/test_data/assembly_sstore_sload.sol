contract Test{

    uint variable;

    function read() internal {
        assembly {
            let read_value := sload(variable.slot)
        }
    }

    function read_parameter(uint slot) internal {
        assembly {
            let read_value := sload(slot)
        }
    }

    function write() internal {
        assembly {
            sstore(variable.slot, 1)
        }
    }

    function write_parameter(uint slot) internal {
        assembly {
            sstore(slot, 1)
        }
    }

}