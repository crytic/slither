contract MyConc{
    function bad(address payable dst) external payable{
        dst.call{value:msg.value}("");
    }

    function good(address payable dst) external payable{
        (bool ret, ) = dst.call{value:msg.value}("");
        require(ret);
    }

    function good2(address payable dst) external payable{
        (bool ret, ) = dst.call{value:msg.value}("");
        if (!ret) {
            revert();
        }
    }
}
