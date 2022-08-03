abstract contract IERC20Good {
    function transfer(address to, uint value) external virtual returns (bool);
    function approve(address spender, uint value) external virtual returns (bool);
    function transferFrom(address from, address to, uint value) external virtual returns (bool);
    function totalSupply() external view virtual returns (uint);
    function balanceOf(address who) external view virtual returns (uint);
    function allowance(address owner, address spender) external view virtual returns (uint);
    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);
}

abstract contract IERC20Bad {
    function transfer(address to, uint value) external virtual returns (bool);
    function approve(address spender, uint value) external virtual returns (bool);
    function transferFrom(address from, address to, uint value) external virtual returns (bool);
    function totalSupply() external view virtual returns (uint);
    function balanceOf(address who) external view virtual returns (uint);
    function allowance(address owner, address spender) external view virtual returns (uint);
    event Transfer(address from, address to, uint value);
    event Approval(address owner, address spender, uint value);
}

abstract contract ERC20BadDerived is IERC20Bad {

}