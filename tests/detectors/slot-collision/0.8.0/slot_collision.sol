contract Proxy {
    address proxyOwner;
    // ...
}

contract impl {
    bool isInit;
    address owner;
    
    modifier initializer () {
        require(!isInit, "already initialized");
        _;
        isInit = true;
    }
    
    function init(address _owner) initializer public {
        owner = _owner;
    }
}