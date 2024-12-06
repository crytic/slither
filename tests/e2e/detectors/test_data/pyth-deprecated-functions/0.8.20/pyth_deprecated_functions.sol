
// Fake Pyth interface
interface IPyth {
    function getPrice(bytes32 id) external returns (uint256 price);
    function notDeprecated(bytes32 id) external returns (uint256 price);
}

interface INotPyth {
    function getPrice(bytes32 id) external returns (uint256 price);
}

contract C {

    IPyth pyth;
    INotPyth notPyth;
    
    constructor(IPyth _pyth, INotPyth _notPyth) {
        pyth = _pyth;
        notPyth = _notPyth;
    }
    
    function Deprecated(bytes32 priceId) public {
        uint256 price = pyth.getPrice(priceId);
    }

    function notDeprecated(bytes32 priceId) public {
        uint256 price = pyth.notDeprecated(priceId);
    }

    function notPythCall(bytes32 priceId) public {
        uint256 price = notPyth.getPrice(priceId);
    }


}    
