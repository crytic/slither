contract T {
 function bad() public {
   require(msg.sender == tx.origin);
 }

 function bad2(uint y) public {
   if (msg.sender == tx.origin && y == 45) {return;}
 }

function bad3() internal view returns (bool) {
    return msg.sender == tx.origin;
}

 function good(uint y) public {
   if (msg.sender == tx.origin && msg.sender.code.length == 0) {return;}
 }

function good2() public {
   require(msg.sender == tx.origin && msg.sender.code.length == 0);
 }

function good3() internal view returns (bool) {
    return msg.sender == tx.origin && msg.sender.code.length == 0;
}

modifier bad4() {
   require(msg.sender == tx.origin);
   _;
 }

}