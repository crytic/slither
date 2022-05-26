contract C {
  address owner;

  modifier onlyOwner(){
    require(msg.sender == owner);
    _;
  }

  modifier check_addr(address _addr) {
    if (_addr != address(0)) {
      _;
    }
  }

  function check_addr_call(address _addr) pure internal returns(address){
    require (_addr != address(0));
    return _addr;
  }

  function bad0_set_owner(address new_owner) payable public{
    owner = new_owner; // No check before use
  }

  function bad1_send(address payable addr) payable public{
    addr.send(msg.value); // No check before send
    addr.send(msg.value); 
  }

  function bad2_transfer(address payable addr) payable public{
    addr.transfer(msg.value); // No check before transfer
  }

  function bad3_transfer(address payable addr) payable public{
    addr.transfer(msg.value); 
    require(addr != address(0)); // check after transfer just to verify detector heuristic implementation.	
  }

  function bad4_call(address payable addr) payable public{
    addr.call{value:msg.value}(""); // No check before call
  }
 
  function bad5_set_owner(address addr) public{
    require(msg.sender == owner);
    owner = addr;
  }

  function good0_set_owner(address new_owner) payable public{
    if (new_owner != address(0)) { // Check
      owner = new_owner;
    }
  }

  function good1_set_owner() payable public{
    owner = 0x0123456789012345678901234567890123456789; // No tainting
  }

  function good2_send(address payable addr) payable public{
    if (addr != address(0)) {
      addr.send(msg.value); // check before send
    }
  }
  
  function good3_transfer(address payable addr) payable public{
    if (addr != address(0)) {
      addr.transfer(msg.value); // check before transfer
    }
  }

  function good4_transfer(address payable addr) payable public{
    require(addr != address(0));
    addr.transfer(msg.value); // check in above require before transfer
  }

  function good5_transfer(address payable addr) payable public check_addr(addr) { 
    addr.transfer(msg.value); // checked in modifier before transfer
  }

  function good6_msg_sender() payable public {
    owner = msg.sender; // msg.sender does not need to be zero validated
  }

  function good7_transfer_msg_sender() payable public {
    address payable addr = msg.sender;
    addr.transfer(msg.value); // msg.sender does not need to be zero validated
  }

  function good8_set_owner(address new_owner) payable public{
    owner = check_addr_call(new_owner);
  }
}
