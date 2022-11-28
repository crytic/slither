// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

contract AuctionSmartContract {
    // Bid, withdraw and close auction functions
    // variable params for the auction
    // Receiver address
    address payable public receiver;
    // Closing time stamp
    uint public closingTime;

    // Top Bidder address
    address public topBidder;
    // Top Bid value
    uint public topBid;

    // Withdrawls
    mapping(address => uint) withdrawl;

    // Check auction closed or not, true or false
    bool closed;

    // Events in auction
    event topBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);

    constructor(uint _biddingTime, address payable _receiver) {
        receiver = _receiver;
        closingTime = block.timestamp + _biddingTime;
    }

    /// Bid on the auction with a value and amount will be returned if auction not won
    function bid() public payable {

        // Check current time is not more than closing time of auction
        require(block.timestamp <= closingTime, "The auction has already closed.");

        // Finf the top bid
        require(msg.value >= topBid, "There's already a higher bid. Try bidding higher!");

        if(topBid != 0) {
            withdrawl[topBidder] += topBid;
        }

        topBidder = msg.sender;
        topBid = msg.value;

        // Emit an event
        emit topBidIncreased(msg.sender, msg.value);
    }

    // with draw function
    function withdraw() public returns(bool) {
        // Amount to be withdrawn
        uint amount = withdrawl[msg.sender];

        if(amount > 0) {
            withdrawl[msg.sender] = 0;

            if(!payable(msg.sender).send(amount)) {
                withdrawl[msg.sender] = amount;
                return false;
            }
        }

        return true;
    }

    /// Close the auction and notify the highest bidder
    function auctionClosed() public {
      
      // Check the time to close
      require(block.timestamp >= closingTime, "The auction hasn't closed yet.");
      require(!closed, "auctionEnd has already been called.");

      closed = true;
      emit AuctionEnded(topBidder, topBid);

      receiver.transfer(topBid);
    }
}