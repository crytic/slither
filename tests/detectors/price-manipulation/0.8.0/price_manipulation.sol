interface IERC20{
    function balanceOf(address) view external returns(uint);
}
contract A{
    IERC20 tokenA;
    IERC20 tokenB;
    address _lpaddr;

    function getprice() public view returns (uint256 _price) {
        uint256 lpTokenA=tokenA.balanceOf(_lpaddr); 
        uint256 lpTokenB=tokenB.balanceOf(_lpaddr); 
        _price = lpTokenA * 10**18 / lpTokenB;
    }
}