contract MyConc{
    function bad(address dst) external payable{
        dst.call.value(msg.value)("");
    }

    function good(address dst) external payable{
        require(dst.call.value(msg.value)());
    }

}
