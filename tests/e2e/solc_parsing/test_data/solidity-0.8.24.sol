contract A {

    modifier NonReentrant {
        assembly {
            if tload(0) { revert(0, 0) }
            tstore(0, 1)
        }
        _;
        assembly {
            tstore(0, 0)
        }
    }

    function a() NonReentrant public {
        bytes32 _blobhash = blobhash(2);
        uint _blobbasefee = block.blobbasefee;

        assembly {
            let __blobbasefee := blobbasefee()
            let _basefee := basefee()
            let __blobhash := blobhash(3)
            mcopy(0, 0x40, 0x20)
        }
    }
}

