type UFixed18 is uint256;

library FixedMath
{
    function add(UFixed18 a, UFixed18 b) internal pure returns (UFixed18 c) {
        return UFixed18.wrap(UFixed18.unwrap(a) + UFixed18.unwrap(b));
    }
    function sub(UFixed18 a, UFixed18 b) internal pure returns (UFixed18 c) {
        return UFixed18.wrap(UFixed18.unwrap(a) - UFixed18.unwrap(b));
    }
}

contract ERC20 {
    using FixedMath for UFixed18;

    event Transfer(address indexed from, address indexed to, UFixed18 value);
    event Approval(address indexed owner, address indexed spender, UFixed18 value);

    mapping (address => UFixed18) private _balances;
    mapping (address => mapping (address => UFixed18)) private _allowances;
    UFixed18 private _totalSupply;

    constructor() {
        _mint(msg.sender, UFixed18.wrap(20));
    }

    function totalSupply() public view returns (UFixed18) {
        return _totalSupply;
    }

    function balanceOf(address owner) public view returns (UFixed18) {
        return _balances[owner];
    }

    function allowance(address owner, address spender) public view returns (UFixed18) {
        return _allowances[owner][spender];
    }

    function transfer(address to, UFixed18 value) public returns (bool) {
        _transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, UFixed18 value) public returns (bool) {
        _approve(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, UFixed18 value) public returns (bool) {
        _transfer(from, to, value);
        // The subtraction here will revert on overflow.
        _approve(from, msg.sender, _allowances[from][msg.sender].sub(value));
        return true;
    }

    function increaseAllowance(address spender, UFixed18 addedValue) public returns (bool) {
        // The addition here will revert on overflow.
        _approve(msg.sender, spender, _allowances[msg.sender][spender].add(addedValue));
        return true;
    }

    function decreaseAllowance(address spender, UFixed18 subtractedValue) public returns (bool) {
        // The subtraction here will revert on overflow.
        _approve(msg.sender, spender, _allowances[msg.sender][spender].sub(subtractedValue));
        return true;
    }

    function _transfer(address from, address to, UFixed18 value) internal {
        require(to != address(0), "ERC20: transfer to the zero address");

        // The subtraction and addition here will revert on overflow.
        _balances[from] = _balances[from].sub(value);
        _balances[to] = _balances[to].add(value);
        emit Transfer(from, to, value);
    }

    function _mint(address account, UFixed18 value) internal {
        require(account != address(0), "ERC20: mint to the zero address");

        // The additions here will revert on overflow.
        _totalSupply = _totalSupply.add(value);
        _balances[account] = _balances[account].add(value);
        emit Transfer(address(0), account, value);
    }

    function _burn(address account, UFixed18 value) internal {
        require(account != address(0), "ERC20: burn from the zero address");

        // The subtractions here will revert on overflow.
        _totalSupply = _totalSupply.sub(value);
        _balances[account] = _balances[account].sub(value);
        emit Transfer(account, address(0), value);
    }

    function _approve(address owner, address spender, UFixed18 value) internal {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = value;
        emit Approval(owner, spender, value);
    }

    function _burnFrom(address account, UFixed18 value) internal {
        _burn(account, value);
        _approve(account, msg.sender, _allowances[account][msg.sender].sub(value));
    }
}
