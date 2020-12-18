contract Bug{
  address owner;
  address addr = 0x123F681646d4A755815f9CB19e1aCc8565A0c2AC;
  event Price(uint8 uprice8);
  uint8 uprice8;
  uint8 uprice8_2;
  uint8 uprice8_3;
  int16 iprice16;  
  uint8 ufee;
  int16 ifee;
  
  modifier onlyAdmin {
    require(msg.sender != owner);
    _;
  }

  function bad0_helper() public{
    require(uprice8 > 0);
    ufee = uprice8 * 100; 
  }
  
  function bad0(uint8 _price) onlyAdmin public{
    uprice8 = _price;
  }

  function bad1_helper() public{
    ifee = iprice16 * 100; 
  }
  
  function bad1(int16 _price) onlyAdmin public{
    iprice16 = _price;
  }

  function good0(uint8 _price) public { // Not protected
    uprice8_2 = _price;
  }

  function good1__helper() onlyAdmin public { // Protected
    ufee = uprice8_2 * 100; 
  }
  
  function good1(uint8 _price) onlyAdmin public {
    uprice8_2 = _price; // Used in another protected function good1_helper
  }

  function good2__helper() public { 
    ufee = uprice8_3 * 100; 
  }
  
  function good2(uint8 _price) onlyAdmin public {
    uprice8_3 = _price;
    emit Price(uprice8_3); // Event present
  }

  function good3() onlyAdmin public {
    uprice8_2 = 0; // No tainting breaks detector heuristic
  }

  function good4(uint8 _price) onlyAdmin private { // Private functions are ignored
    uprice8_2 = _price; 
  }

  function good5_helper() public {
    require(addr != address(0));
  }

  function good5(address _addr) onlyAdmin public{ // non-int/non-uint types are ignored
    addr = _addr; 
  }

  
}
