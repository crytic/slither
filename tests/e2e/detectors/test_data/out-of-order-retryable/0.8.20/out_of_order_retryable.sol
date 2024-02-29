interface Y {
     function createRetryableTicket(
     address to,
     uint256 l2CallValue,
     uint256 maxSubmissionCost,
     address excessFeeRefundAddress,
     address callValueRefundAddress,
     uint256 gasLimit,
     uint256 maxFeePerGas,
     bytes calldata data
     ) external payable returns (uint256);
}

contract X {
function good() external {
     if (true) {
          Y(msg.sender).createRetryableTicket(
               address(1),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
     } else {
        Y(msg.sender).createRetryableTicket(
               address(2),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
     }
}
function bad1() external {
     if (true) {
        Y(msg.sender).createRetryableTicket(
               address(1),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
     }    
        Y(msg.sender).createRetryableTicket(
               address(2),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");

}
function bad2() external {
        Y(msg.sender).createRetryableTicket(
               address(1),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
          
        Y(msg.sender).createRetryableTicket(
               address(2),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
}
function bad3() external {
        Y(msg.sender).createRetryableTicket(
               address(1),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
     good2();
} 
function bad4() external {
     good2();
     good2();
}
function good2() internal {
             Y(msg.sender).createRetryableTicket(
               address(2),
               0,
               0,
               address(0),
               address(0),
               0,
               0,
               "");
}
}