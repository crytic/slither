contract Bug{
  uint totalSupply;
  uint price;
  address owner;
  address operator;
  address addr = 0x123F681646d4A755815f9CB19e1aCc8565A0c2AC;
  event Supply(uint totalSupply);
  event Owner(address owner);

  modifier onlyAdmin {
    require(msg.sender != owner);
    _;
  }
  
  function bad0() onlyAdmin external {
    owner = msg.sender; // Tainting
  }

  function bad1(address newOwner) onlyAdmin external {
    owner = newOwner; // Tainting
  }

  function bad2(address newOwner) onlyAdmin external {
    require(newOwner != address(0));
    owner = newOwner; // Tainting
  }
  
  function good0(uint a) external { // Not Protected breaks detector heuristic
    totalSupply += a; 
  }

  function good1() onlyAdmin external {
    owner = msg.sender; 
    emit Owner(owner); // Event present breaks detector heuristic
  }

  function good2() onlyAdmin external {
    owner = addr; // No tainting breaks detector heuristic
  }

  function good3(address newOwner) onlyAdmin private { // Private functions are ignored
    owner = newOwner; 
  }

  function good4(uint newPrice) onlyAdmin public { // non-address types are ignored
    price = newPrice; 
  }

  function good5(address newOwner) onlyAdmin external {
    operator = newOwner; // operator is not used for access control in any modifier
  }
}
