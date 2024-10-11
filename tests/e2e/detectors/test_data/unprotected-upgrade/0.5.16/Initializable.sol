contract Initializable {
    modifier initializer() {
        _;
    }

    modifier reinitializer(uint64 version) {
        _;
    }
}
