
contract ERC20Buggy {

    uint256 public _totalSupply;
    mapping(address => uint) public _balanceOf;
    mapping(address => mapping(address => uint)) public _allowance;

    function transfer(address to, uint256 value) public returns (bool success){
        _balanceOf[msg.sender] -= value;
        _balanceOf[to] += value;
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool success){
        if(_allowance[msg.sender][from] >= value){
            _allowance[msg.sender][from] -= value;
            _balanceOf[from] -= value;
            _balanceOf[to] += value;
            return true;
        }
        return false;
    }

    function approve(address _spender, uint256 value) public returns (bool success){
        _allowance[msg.sender][_spender] = value;
        return true;
    }

    function balanceOf(address from) public returns(uint) {
        return _balanceOf[from];
    }

    function allowance(address from, address to) public returns(uint) {
        return _allowance[from][to];
    }

    function totalSupply() public returns(uint){
        return _totalSupply;
    }

    event Transfer(address indexed _from, address indexed _to, uint256 _value);
    event Approval(address indexed _owner, address indexed _spender, uint256 _value);
}
