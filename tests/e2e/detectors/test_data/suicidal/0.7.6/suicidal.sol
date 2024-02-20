
contract C{

    function i_am_a_backdoor() public{
        selfdestruct(msg.sender);
    }

    function i_am_a_backdoor2(address payable to) public{
        internal_selfdestruct(to);
    }

    function internal_selfdestruct(address payable to) internal {
        selfdestruct(to);
    }

}
