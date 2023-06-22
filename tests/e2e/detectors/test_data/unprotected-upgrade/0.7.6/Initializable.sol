contract Initializable{
    uint8 private _initialized;
    bool private _initializing;

    modifier initializer() {
        _;
    }

    function _disableInitializers() internal virtual {
        require(!_initializing, "Initializable: contract is initializing");
        if (_initialized < type(uint8).max) {
            _initialized = type(uint8).max;
        }
    }
}