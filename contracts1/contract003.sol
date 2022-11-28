// SPDX-License-Identifier: Unlicensed
pragma solidity ^0.8.13;

// IERC721 - NFC standards
interface IERC721 {
    function send(
        address _from,
        address _to,
        uint _id
    ) external;
}

contract DutchAuction {
    // Dutch auction happens for 7 days
    // Price reduces day by day
    //  700 on day1 , 550 on day 2........ like that
    uint private constant DURATION = 7 days;

    IERC721 public immutable nft;
    uint public immutable nftId;

    address payable public immutable seller;
    uint public immutable openingPrice;
    uint public immutable opensAt;
    uint public immutable endsAt;
    uint public immutable disRate;

    constructor(
        uint _startRate,
        uint _disRate,
        address _nft,
        uint _id
    ) {
        seller = payable(msg.sender);
        openingPrice = _startRate;
        opensAt = block.timestamp;
        endsAt = block.timestamp + DURATION;
        disRate = _disRate;

        require(_startRate >= _disRate * DURATION, "starting price < min");

        nft = IERC721(_nft);
        nftId = _id;
    }

    function getPrice() public view returns (uint) {
        uint remTime = block.timestamp - opensAt;
        uint disc = disRate * remTime;
        return openingPrice - disc;
    }

    function buy() external payable {
        require(block.timestamp < endsAt, "auction closed");

        uint price = getPrice();
        require(msg.value >= price, "value always < price");

        nft.send(seller, msg.sender, nftId);
        uint refund = msg.value - price;
        //  Check for losing bidders and return the amount
        //  Checking negative refund
        if (refund > 0) {
            payable(msg.sender).transfer(refund);
        }
        selfdestruct(seller);
    }
}