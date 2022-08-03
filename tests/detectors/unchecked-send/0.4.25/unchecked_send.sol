contract MyConc{
    function bad(address dst) external payable{
        dst.send(msg.value);
    }

    function good(address dst) external payable{
        require(dst.send(msg.value));
    }

    function good2(address dst) external payable{
        bool res = dst.send(msg.value);
        if(!res){
            emit Failed(dst, msg.value);
        }
    }

    event Failed(address, uint);
}
