contract C {
  uint a=0;
  uint b=-1+1;
  uint c=(b=+1);

  function f() external {
    uint x = 1;
    x=+                 144444;
    x = (x=+1);
    x++;
    x = -1 + 1;
    //++x;
    //x = x++;
  }
}
