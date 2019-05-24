pragma solidity 0.4.25;

// File: contracts\interface\PlayerBookInterface.sol

interface PlayerBookInterface {
    function getPlayerID(address _Addr) external returns (uint256);
    function getPlayerName(uint256 _PID) external view returns (bytes32);
    function getPlayerLAff(uint256 _PID) external view returns (uint256);
    function getPlayerAddr(uint256 _PID) external view returns (address);
    function getNameFee() external view returns (uint256);
    function registerNameXIDFromDapp(address _Addr, bytes32 _Name, uint256 _affCode, bool _all) external payable returns(bool, uint256);
    function registerNameXaddrFromDapp(address _Addr, bytes32 _Name, address _affCode, bool _all) external payable returns(bool, uint256);
    function registerNameXnameFromDapp(address _Addr, bytes32 _Name, bytes32 _affCode, bool _all) external payable returns(bool, uint256);
}

// File: contracts\library\SafeMath.sol

/**
 * @title SafeMath v0.1.9
 * @dev Math operations with safety checks that throw on error
 * change notes:  original SafeMath library from OpenZeppelin modified by Inventor
 * - added sqrt
 * - added sq
 * - added pwr 
 * - changed asserts to requires with error log outputs
 * - removed div, its useless
 */
library SafeMath {
    
    /**
    * @dev Multiplies two numbers, throws on overflow.
    */
    function mul(uint256 a, uint256 b) 
        internal 
        pure 
        returns (uint256 c) 
    {
        if (a == 0) {
            return 0;
        }
        c = a * b;
        require(c / a == b, "SafeMath mul failed");
        return c;
    }

    /**
    * @dev Integer division of two numbers, truncating the quotient.
    */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        // assert(b > 0); // Solidity automatically throws when dividing by 0
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold
        return c;
    }
    
    /**
    * @dev Subtracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
    */
    function sub(uint256 a, uint256 b)
        internal
        pure
        returns (uint256) 
    {
        require(b <= a, "SafeMath sub failed");
        return a - b;
    }

    /**
    * @dev Adds two numbers, throws on overflow.
    */
    function add(uint256 a, uint256 b)
        internal
        pure
        returns (uint256 c) 
    {
        c = a + b;
        require(c >= a, "SafeMath add failed");
        return c;
    }
    
    /**
     * @dev gives square root of given x.
     */
    function sqrt(uint256 x)
        internal
        pure
        returns (uint256 y) 
    {
        uint256 z = ((add(x,1)) / 2);
        y = x;
        while (z < y) 
        {
            y = z;
            z = ((add((x / z),z)) / 2);
        }
    }
    
    /**
     * @dev gives square. multiplies x by x
     */
    function sq(uint256 x)
        internal
        pure
        returns (uint256)
    {
        return (mul(x,x));
    }
    
    /**
     * @dev x to the power of y 
     */
    function pwr(uint256 x, uint256 y)
        internal 
        pure 
        returns (uint256)
    {
        if (x==0)
            return (0);
        else if (y==0)
            return (1);
        else 
        {
            uint256 z = x;
            for (uint256 i=1; i < y; i++)
                z = mul(z,x);
            return (z);
        }
    }
}

// File: contracts\library\UintCompressor.sol

/**
* @title -UintCompressor- v0.1.9
* ┌┬┐┌─┐┌─┐┌┬┐   ╦╦ ╦╔═╗╔╦╗  ┌─┐┬─┐┌─┐┌─┐┌─┐┌┐┌┌┬┐┌─┐
*  │ ├┤ ├─┤│││   ║║ ║╚═╗ ║   ├─┘├┬┘├┤ └─┐├┤ │││ │ └─┐
*  ┴ └─┘┴ ┴┴ ┴  ╚╝╚═╝╚═╝ ╩   ┴  ┴└─└─┘└─┘└─┘┘└┘ ┴ └─┘
*                                  _____                      _____
*                                 (, /     /)       /) /)    (, /      /)          /)
*          ┌─┐                      /   _ (/_      // //       /  _   // _   __  _(/
*          ├─┤                  ___/___(/_/(__(_/_(/_(/_   ___/__/_)_(/_(_(_/ (_(_(_
*          ┴ ┴                /   /          .-/ _____   (__ /                               
*                            (__ /          (_/ (, /                                      /)™ 
*                                                 /  __  __ __ __  _   __ __  _  _/_ _  _(/
* ┌─┐┬─┐┌─┐┌┬┐┬ ┬┌─┐┌┬┐                          /__/ (_(__(_)/ (_/_)_(_)/ (_(_(_(__(/_(_(_
* ├─┘├┬┘│ │ │││ ││   │                      (__ /              .-/  © Jekyll Island Inc. 2018
* ┴  ┴└─└─┘─┴┘└─┘└─┘ ┴                                        (_/
*    _  _   __   __ _  ____     ___   __   _  _  ____  ____  ____  ____  ____   __   ____ 
*===/ )( \ (  ) (  ( \(_  _)===/ __) /  \ ( \/ )(  _ \(  _ \(  __)/ ___)/ ___) /  \ (  _ \===*
*   ) \/ (  )(  /    /  )(    ( (__ (  O )/ \/ \ ) __/ )   / ) _) \___ \\___ \(  O ) )   /
*===\____/ (__) \_)__) (__)====\___) \__/ \_)(_/(__)  (__\_)(____)(____/(____/ \__/ (__\_)===*
*
* ╔═╗┌─┐┌┐┌┌┬┐┬─┐┌─┐┌─┐┌┬┐  ╔═╗┌─┐┌┬┐┌─┐ ┌──────────┐
* ║  │ ││││ │ ├┬┘├─┤│   │   ║  │ │ ││├┤  │ Inventor │
* ╚═╝└─┘┘└┘ ┴ ┴└─┴ ┴└─┘ ┴   ╚═╝└─┘─┴┘└─┘ └──────────┘
*/

library UintCompressor {
    using SafeMath for *;
    
    function insert(uint256 _Var, uint256 _Include, uint256 _Start, uint256 _End)
        internal
        pure
        returns(uint256)
    {
        // check conditions 
        require(_End < 77 && _Start < 77, "start/end must be less than 77");
        require(_End >= _Start, "end must be >= start");
        
        // format our start/end points
        _End = exponent(_End).mul(10);
        _Start = exponent(_Start);
        
        // check that the include data fits into its segment 
        require(_Include < (_End / _Start));
        
        // build middle
        if (_Include > 0)
            _Include = _Include.mul(_Start);
        
        return((_Var.sub((_Var / _Start).mul(_Start))).add(_Include).add((_Var / _End).mul(_End)));
    }
    
    function extract(uint256 _Input, uint256 _Start, uint256 _End)
	    internal
	    pure
	    returns(uint256)
    {
        // check conditions
        require(_End < 77 && _Start < 77, "start/end must be less than 77");
        require(_End >= _Start, "end must be >= start");
        
        // format our start/end points
        _End = exponent(_End).mul(10);
        _Start = exponent(_Start);
        
        // return requested section
        return((((_Input / _Start).mul(_Start)).sub((_Input / _End).mul(_End))) / _Start);
    }
    
    function exponent(uint256 _Position)
        private
        pure
        returns(uint256)
    {
        return((10).pwr(_Position));
    }
}

// File: contracts\library\NameFilter.sol

/**
* @title -Name Filter- v0.1.9
* ┌┬┐┌─┐┌─┐┌┬┐   ╦╦ ╦╔═╗╔╦╗  ┌─┐┬─┐┌─┐┌─┐┌─┐┌┐┌┌┬┐┌─┐
*  │ ├┤ ├─┤│││   ║║ ║╚═╗ ║   ├─┘├┬┘├┤ └─┐├┤ │││ │ └─┐
*  ┴ └─┘┴ ┴┴ ┴  ╚╝╚═╝╚═╝ ╩   ┴  ┴└─└─┘└─┘└─┘┘└┘ ┴ └─┘
*                                  _____                      _____
*                                 (, /     /)       /) /)    (, /      /)          /)
*          ┌─┐                      /   _ (/_      // //       /  _   // _   __  _(/
*          ├─┤                  ___/___(/_/(__(_/_(/_(/_   ___/__/_)_(/_(_(_/ (_(_(_
*          ┴ ┴                /   /          .-/ _____   (__ /                               
*                            (__ /          (_/ (, /                                      /)™ 
*                                                 /  __  __ __ __  _   __ __  _  _/_ _  _(/
* ┌─┐┬─┐┌─┐┌┬┐┬ ┬┌─┐┌┬┐                          /__/ (_(__(_)/ (_/_)_(_)/ (_(_(_(__(/_(_(_
* ├─┘├┬┘│ │ │││ ││   │                      (__ /              .-/  © Jekyll Island Inc. 2018
* ┴  ┴└─└─┘─┴┘└─┘└─┘ ┴                                        (_/
*              _       __    _      ____      ____  _   _    _____  ____  ___  
*=============| |\ |  / /\  | |\/| | |_ =====| |_  | | | |    | |  | |_  | |_)==============*
*=============|_| \| /_/--\ |_|  | |_|__=====|_|   |_| |_|__  |_|  |_|__ |_| \==============*
*
* ╔═╗┌─┐┌┐┌┌┬┐┬─┐┌─┐┌─┐┌┬┐  ╔═╗┌─┐┌┬┐┌─┐ ┌──────────┐
* ║  │ ││││ │ ├┬┘├─┤│   │   ║  │ │ ││├┤  │ Inventor │
* ╚═╝└─┘┘└┘ ┴ ┴└─┴ ┴└─┘ ┴   ╚═╝└─┘─┴┘└─┘ └──────────┘
*/

library NameFilter {
    /**
     * @dev filters name strings
     * -converts uppercase to lower case.  
     * -makes sure it does not start/end with a space
     * -makes sure it does not contain multiple spaces in a row
     * -cannot be only numbers
     * -cannot start with 0x 
     * -restricts characters to A-Z, a-z, 0-9, and space.
     * @return reprocessed string in bytes32 format
     */
    function nameFilter(string _Input)
        internal
        
        returns(bytes32)
    {
        bytes memory _temp = bytes(_Input);
        uint256 _length = _temp.length;
        
        //sorry limited to 32 characters
        require (_length <= 32 && _length > 0, "string must be between 1 and 32 characters");
        // make sure it doesnt start with or end with space
        require(_temp[0] != 0x20 && _temp[_length-1] != 0x20, "string cannot start or end with space");
        // make sure first two characters are not 0x
        if (_temp[0] == 0x30)
        {
            require(_temp[1] != 0x78, "string cannot start with 0x");
            require(_temp[1] != 0x58, "string cannot start with 0X");
        }
        
        // create a bool to track if we have a non number character
        bool _hasNonNumber;
        
        // convert & check
        for (uint256 i = 0; i < _length; i++)
        {
            // if its uppercase A-Z
            if (_temp[i] > 0x40 && _temp[i] < 0x5b)
            {
                // convert to lower case a-z
                _temp[i] = byte(uint(_temp[i]) + 32);
                
                // we have a non number
                if (_hasNonNumber == false)
                    _hasNonNumber = true;
            } else {
                require
                (
                    // require character is a space
                    _temp[i] == 0x20 || 
                    // OR lowercase a-z
                    (_temp[i] > 0x60 && _temp[i] < 0x7b) ||
                    // or 0-9
                    (_temp[i] > 0x2f && _temp[i] < 0x3a),
                    "string contains invalid characters"
                );
                // make sure theres not 2x spaces in a row
                if (_temp[i] == 0x20)
                    require( _temp[i+1] != 0x20, "string cannot contain consecutive spaces");
                
                // see if we have a character other than a number
                if (_hasNonNumber == false && (_temp[i] < 0x30 || _temp[i] > 0x39))
                    _hasNonNumber = true;    
            }
        }
        
        require(_hasNonNumber == true, "string cannot be only numbers");
        
        bytes32 _ret;
        assembly {
            _ret := mload(add(_temp, 32))
        }
        return (_ret);
    }
}

// File: contracts\library\F3DKeysCalcLong.sol

//==============================================================================
//  |  _      _ _ | _  .
//  |<(/_\/  (_(_||(_  .
//=======/======================================================================
library F3DKeysCalcLong {
    using SafeMath for *;
    /**
     * @dev calculates number of keys received given X eth 
     *  _curEth current amount of eth in contract 
     *  _newEth eth being spent
     * @return amount of ticket purchased
     */
    function keysRec(uint256 _CurEth, uint256 _NewEth)
        internal
        pure
        returns (uint256)
    {
        return(keys((_CurEth).add(_NewEth)).sub(keys(_CurEth)));
    }
    
    /**
     * @dev calculates amount of eth received if you sold X keys 
     *  _curKeys current amount of keys that exist 
     *  _sellKeys amount of keys you wish to sell
     * @return amount of eth received
     */
    function ethRec(uint256 _CurKeys, uint256 _SellKeys)
        internal
        pure
        returns (uint256)
    {
        return((eth(_CurKeys)).sub(eth(_CurKeys.sub(_SellKeys))));
    }

    /**
     * @dev calculates how many keys would exist with given an amount of eth
     *  _eth eth "in contract"
     * @return number of keys that would exist
     */
    function keys(uint256 _Eth) 
        internal
        pure
        returns(uint256)
    {
        return ((((((_Eth).mul(1000000000000000000)).mul(312500000000000000000000000)).add(5624988281256103515625000000000000000000000000000000000000000000)).sqrt()).sub(74999921875000000000000000000000)) / (156250000);
    }
    
    /**
     * @dev calculates how much eth would be in contract given a number of keys
     *  _keys number of keys "in contract" 
     * @return eth that would exists
     */
    function eth(uint256 _Keys) 
        internal
        pure
        returns(uint256)  
    {
        return ((78125000).mul(_Keys.sq()).add(((149999843750000).mul(_Keys.mul(1000000000000000000))) / (2))) / ((1000000000000000000).sq());
    }
}

// File: contracts\library\F3Ddatasets.sol

//==============================================================================
//   __|_ _    __|_ _  .
//  _\ | | |_|(_ | _\  .
//==============================================================================
library F3Ddatasets {
    //compressedData key
    // [76-33][32][31][30][29][28-18][17][16-6][5-3][2][1][0]
        // 0 - new player (bool)
        // 1 - joined round (bool)
        // 2 - new  leader (bool)
        // 3-5 - air drop tracker (uint 0-999)
        // 6-16 - round end time
        // 17 - winnerTeam
        // 18 - 28 timestamp 
        // 29 - team
        // 30 - 0 = reinvest (round), 1 = buy (round), 2 = buy (ico), 3 = reinvest (ico)
        // 31 - airdrop happened bool
        // 32 - airdrop tier 
        // 33 - airdrop amount won
    //compressedIDs key
    // [77-52][51-26][25-0]
        // 0-25 - pID 
        // 26-51 - winPID
        // 52-77 - rID
    struct EventReturns {
        uint256 compressedData;
        uint256 compressedIDs;
        address winnerAddr;         // winner address
        bytes32 winnerName;         // winner name
        uint256 amountWon;          // amount won
        uint256 newPot;             // amount in new pot
        uint256 P3DAmount;          // amount distributed to p3d
        uint256 genAmount;          // amount distributed to gen
        uint256 potAmount;          // amount added to pot
    }
    struct Player {
        address addr;   // player address
        bytes32 name;   // player name
        uint256 win;    // winnings vault
        uint256 gen;    // general vault
        uint256 aff;    // affiliate vault
        uint256 lrnd;   // last round played
        uint256 laff;   // last affiliate id used
    }
    struct PlayerRounds {
        uint256 eth;    // eth player has added to round (used for eth limiter)
        uint256 keys;   // keys
        uint256 mask;   // player mask 
        uint256 ico;    // ICO phase investment
    }
    struct Round {
        uint256 plyr;   // pID of player in lead， lead领导吗？
        uint256 team;   // tID of team in lead
        uint256 end;    // time ends/ended
        bool ended;     // has round end function been ran  这个开关值得研究下
        uint256 strt;   // time round started
        uint256 keys;   // keys
        uint256 eth;    // total eth in
        uint256 pot;    // eth to pot (during round) / final amount paid to winner (after round ends)
        uint256 mask;   // global mask
        uint256 ico;    // total eth sent in during ICO phase
        uint256 icoGen; // total eth for gen during ICO phase
        uint256 icoAvg; // average key price for ICO phase
    }
    struct TeamFee {
        uint256 gen;    // % of buy in thats paid to key holders of current round
        uint256 p3d;    // % of buy in thats paid to p3d holders
    }
    struct PotSplit {
        uint256 gen;    // % of pot thats paid to key holders of current round
        uint256 p3d;    // % of pot thats paid to p3d holders
    }
}

// File: contracts\F3Devents.sol

contract F3Devents {
    // fired whenever a player registers a name
    event OnNewName
    (
        uint256 indexed playerID,
        address indexed playerAddress,
        bytes32 indexed playerName,
        bool isNewPlayer,
        uint256 affiliateID,
        address affiliateAddress,
        bytes32 affiliateName,
        uint256 amountPaid,
        uint256 timeStamp
    );
    
    // fired at end of buy or reload
    event OnEndTx
    (
        uint256 compressedData,     
        uint256 compressedIDs,      
        bytes32 playerName,
        address playerAddress,
        uint256 ethIn,
        uint256 keysBought,
        address winnerAddr,
        bytes32 winnerName,
        uint256 amountWon,
        uint256 newPot,
        uint256 P3DAmount,
        uint256 genAmount,
        uint256 potAmount,
        uint256 airDropPot
    );
    
	// fired whenever theres a withdraw
    event OnWithdraw
    (
        uint256 indexed playerID,
        address playerAddress,
        bytes32 playerName,
        uint256 ethOut,
        uint256 timeStamp
    );
    
    // fired whenever a withdraw forces end round to be ran
    event OnWithdrawAndDistribute
    (
        address playerAddress,
        bytes32 playerName,
        uint256 ethOut,
        uint256 compressedData,
        uint256 compressedIDs,
        address winnerAddr,
        bytes32 winnerName,
        uint256 amountWon,
        uint256 newPot,
        uint256 P3DAmount,
        uint256 genAmount
    );
    
    // (fomo3d long only) fired whenever a player tries a buy after round timer 
    // hit zero, and causes end round to be ran.
    event OnBuyAndDistribute
    (
        address playerAddress,
        bytes32 playerName,
        uint256 ethIn,
        uint256 compressedData,
        uint256 compressedIDs,
        address winnerAddr,
        bytes32 winnerName,
        uint256 amountWon,
        uint256 newPot,
        uint256 P3DAmount,
        uint256 genAmount
    );
    
    // (fomo3d long only) fired whenever a player tries a reload after round timer 
    // hit zero, and causes end round to be ran.
    event OnReLoadAndDistribute
    (
        address playerAddress,
        bytes32 playerName,
        uint256 compressedData,
        uint256 compressedIDs,
        address winnerAddr,
        bytes32 winnerName,
        uint256 amountWon,
        uint256 newPot,
        uint256 P3DAmount,
        uint256 genAmount
    );
    
    // fired whenever an affiliate is paid
    event OnAffiliatePayout
    (
        uint256 indexed affiliateID,
        address affiliateAddress,
        bytes32 affiliateName,
        uint256 indexed roundID,
        uint256 indexed buyerID,
        uint256 amount,
        uint256 timeStamp
    );
    
    // received pot swap deposit
    event OnPotSwapDeposit
    (
        uint256 roundID,
        uint256 amountAddedToPot
    );
}

// File: contracts\modularLong.sol

contract Modularlong is F3Devents {}

// File: contracts\FoMo3Dlong.sol

contract FoMo3Dlong is Modularlong {
    using SafeMath for *;
    using NameFilter for string;
    using F3DKeysCalcLong for uint256;
	

    //TODO:
    //JIincForwarderInterface constant private Jekyll_Island_Inc = JIincForwarderInterface(0x508D1c04cd185E693d22125f3Cc6DC81F7Ce9477);
    PlayerBookInterface constant private PlayerBook = PlayerBookInterface(0x19dB4339c0ad1BE41FE497795FF2c5263962a573);
  
    address public constant TEAMWALLET = 0xE9675cdAf47bab3Eef5B1f1c2b7f8d41cDcf9b29;
    address[] public leaderWallets;
//==============================================================================
//     _ _  _  |`. _     _ _ |_ | _  _  .
//    (_(_)| |~|~|(_||_|| (_||_)|(/__\  .  (game settings)
//=================_|===========================================================
    string constant public name = "Peach Will";
    string constant public symbol = "PW";
    uint256 private constant RNDEXTRA_ = 1 hours; //24 hours;     // length of the very first ICO 
    uint256 private constant RNDGAP_ = 15 seconds;         // length of ICO phase, set to 1 year for EOS.
    uint256 constant private RNDINIT_ = 10 hours; //1 hours;                // round timer starts at this
    uint256 constant private RNDINC_ = 88 seconds;              // every full key purchased adds this much to the timer
    uint256 constant private RNDMAX_ =  10 hours; // 24 hours;                // max length a round timer can be
//==============================================================================
//     _| _ _|_ _    _ _ _|_    _   .
//    (_|(_| | (_|  _\(/_ | |_||_)  .  (data used to store game info that changes)
//=============================|================================================
	uint256 public airDropPot_;             // person who gets the airdrop wins part of this pot
    uint256 public airDropTracker_ = 0;     // incremented each time a "qualified" tx occurs.  used to determine winning air drop
    uint256 public rID_;    // round id number / total rounds that have happened
//****************
// PLAYER DATA 
//****************
    mapping (address => uint256) public pIDxAddr_;          // (addr => pID) returns player id by address
    mapping (bytes32 => uint256) public pIDxName_;          // (name => pID) returns player id by name
    mapping (uint256 => F3Ddatasets.Player) public plyr_;   // (pID => data) player data
    mapping (uint256 => mapping (uint256 => F3Ddatasets.PlayerRounds)) public plyrRnds_;    // (pID => rID => data) player round data by player id & round id
    mapping (uint256 => mapping (bytes32 => bool)) public plyrNames_; // (pID => name => bool) list of names a player owns.  (used so you can change your display name amongst any name you own)
//****************
// ROUND DATA 
//****************
    mapping (uint256 => F3Ddatasets.Round) public round_;   // (rID => data) round data
    mapping (uint256 => mapping(uint256 => uint256)) public rndTmEth_;      // (rID => tID => data) eth in per team, by round id and team id
//****************
// TEAM FEE DATA , Team的费用分配数据
//****************
    mapping (uint256 => F3Ddatasets.TeamFee) public fees_;          // (team => fees) fee distribution by team
    mapping (uint256 => F3Ddatasets.PotSplit) public potSplit_;     // (team => fees) pot split distribution by team
//==============================================================================
//     _ _  _  __|_ _    __|_ _  _  .
//    (_(_)| |_\ | | |_|(_ | (_)|   .  (initial data setup upon contract deploy)
//==============================================================================
    constructor()
        public
    {
		// Team allocation structures
        // 0 = whales
        // 1 = bears
        // 2 = sneks
        // 3 = bulls

		// Team allocation percentages
        // (F3D, P3D) + (Pot , Referrals, Community)
            // Referrals / Community rewards are mathematically designed to come from the winner's share of the pot.
        fees_[0] = F3Ddatasets.TeamFee(54,0);   //20% to pot, 10% to aff, 10% to com, 5% to leader swap, 1% to air drop pot
        fees_[1] = F3Ddatasets.TeamFee(41,0);   //33% to pot, 10% to aff, 10% to com, 5% to leader swap, 1% to air drop pot
        fees_[2] = F3Ddatasets.TeamFee(30,0);  //44% to pot, 10% to aff, 10% to com, 5% to leader swap, 1% to air drop pot
        fees_[3] = F3Ddatasets.TeamFee(40,0);   //34% to pot, 10% to aff, 10% to com, 5% to leader swap, 1% to air drop pot
        
        // how to split up the final pot based on which team was picked
        // (F3D, P3D)
        potSplit_[0] = F3Ddatasets.PotSplit(37,0);  //48% to winner, 10% to next round, 5% to com
        potSplit_[1] = F3Ddatasets.PotSplit(34,0);   //48% to winner, 13% to next round, 5% to com
        potSplit_[2] = F3Ddatasets.PotSplit(25,0);  //48% to winner, 22% to next round, 5% to com
        potSplit_[3] = F3Ddatasets.PotSplit(32,0);  //48% to winner, 15% to next round, 5% to com

        leaderWallets.length = 4;
        leaderWallets[0]= 0x326d8d593195a3153f6d55d7791c10af9bcef597;
        leaderWallets[1]= 0x15B474F7DE7157FA0dB9FaaA8b82761E78E804B9;
        leaderWallets[2]= 0x0c2d482FBc1da4DaCf3CD05b6A5955De1A296fa8;
        leaderWallets[3]= 0xD3d96E74aFAE57B5191DC44Bdb08b037355523Ba;

    }
//==============================================================================
//     _ _  _  _|. |`. _  _ _  .
//    | | |(_)(_||~|~|(/_| _\  .  (these are safety checks)
//==============================================================================
    /**
     * @dev used to make sure no one can interact with contract until it has 
     * been activated. 
     */
    modifier isActivated() {
        require(activated_ == true, "its not ready yet.  check ?eta in discord"); 
        _;
    }
    
    /**
     * @dev prevents contracts from interacting with fomo3d 
     */
    modifier isHuman() {
        address _Addr = msg.sender;
        require (_Addr == tx.origin);
        
        uint256 _codeLength;
        
        assembly {_codeLength := extcodesize(_Addr)}
        require(_codeLength == 0, "sorry humans only");
        _;
    }

    /**
     * @dev sets boundaries for incoming tx 
     */
    modifier isWithinLimits(uint256 _eth) {
        require(_eth >= 1000000000, "pocket lint: not a valid currency");
        require(_eth <= 100000000000000000000000, "no vitalik, no");
        _;    
    }

    /**
     * 
     */
    modifier onlyDevs() {
        //TODO:
        require(
            msg.sender == 0xE9675cdAf47bab3Eef5B1f1c2b7f8d41cDcf9b29 ||
            msg.sender == 0x0020116131498D968DeBCF75E5A11F77e7e1CadE,
            "only team just can activate"
        );
        _;
    }
    
//==============================================================================
//     _    |_ |. _   |`    _  __|_. _  _  _  .
//    |_)|_||_)||(_  ~|~|_|| |(_ | |(_)| |_\  .  (use these to interact with contract)
//====|=========================================================================
    /**
     * @dev emergency buy uses last stored affiliate ID and team snek
     */
    function()
        isActivated()
        isHuman()
        isWithinLimits(msg.value)
        external
        payable
    {
        // set up our tx event data and determine if player is new or not
        F3Ddatasets.EventReturns memory _eventData_ = determinePID(_eventData_);
            
        // fetch player id
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // buy core 
        buyCore(_PID, plyr_[_PID].laff, 2, _eventData_);
    }
    
    /**
     * @dev converts all incoming ethereum to keys.
     * -functionhash- 0x8f38f309 (using ID for affiliate)
     * -functionhash- 0x98a0871d (using address for affiliate)
     * -functionhash- 0xa65b37a1 (using name for affiliate)
     *  _affCode the ID/address/name of the player who gets the affiliate fee
     *  _Team what team is the player playing for?
     */
    function buyXid(uint256 _AffCode, uint256 _Team)
        isActivated()
        isHuman()
        isWithinLimits(msg.value)
        public
        payable
    {
        // set up our tx event data and determine if player is new or not
        F3Ddatasets.EventReturns memory _eventData_ = determinePID(_eventData_);
        
        // fetch player id
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // manage affiliate residuals
        // if no affiliate code was given or player tried to use their own, lolz
        if (_AffCode == 0 || _AffCode == _PID)
        {
            // use last stored affiliate code 
            _AffCode = plyr_[_PID].laff;
            
        // if affiliate code was given & its not the same as previously stored 
        } else if (_AffCode != plyr_[_PID].laff) {
            // update last affiliate 
            plyr_[_PID].laff = _AffCode;
        }
        
        // verify a valid team was selected
        _Team = verifyTeam(_Team);
        
        // buy core 
        buyCore(_PID, _AffCode, _Team, _eventData_);
    }
    
    function buyXaddr(address _AffCode, uint256 _Team)
        isActivated()
        isHuman()
        isWithinLimits(msg.value)
        public
        payable
    {
        // set up our tx event data and determine if player is new or not
        F3Ddatasets.EventReturns memory _eventData_ = determinePID(_eventData_);
        
        // fetch player id
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // manage affiliate residuals
        uint256 _AffID;
        // if no affiliate code was given or player tried to use their own, lolz
        if (_AffCode == address(0) || _AffCode == msg.sender)
        {
            // use last stored affiliate code
            _AffID = plyr_[_PID].laff;
        
        // if affiliate code was given    
        } else {
            // get affiliate ID from aff Code 
            _AffID = pIDxAddr_[_AffCode];
            
            // if affID is not the same as previously stored 
            if (_AffID != plyr_[_PID].laff)
            {
                // update last affiliate
                plyr_[_PID].laff = _AffID;
            }
        }
        
        // verify a valid team was selected
        _Team = verifyTeam(_Team);
        
        // buy core 
        buyCore(_PID, _AffID, _Team, _eventData_);
    }
    
    function buyXname(bytes32 _AffCode, uint256 _Team)
        isActivated()
        isHuman()
        isWithinLimits(msg.value)
        public
        payable
    {
        // set up our tx event data and determine if player is new or not
        F3Ddatasets.EventReturns memory _eventData_ = determinePID(_eventData_);
        
        // fetch player id
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // manage affiliate residuals
        uint256 _AffID;
        // if no affiliate code was given or player tried to use their own, lolz
        if (_AffCode == '' || _AffCode == plyr_[_PID].name)
        {
            // use last stored affiliate code
            _AffID = plyr_[_PID].laff;
        
        // if affiliate code was given
        } else {
            // get affiliate ID from aff Code
            _AffID = pIDxName_[_AffCode];
            
            // if affID is not the same as previously stored
            if (_AffID != plyr_[_PID].laff)
            {
                // update last affiliate
                plyr_[_PID].laff = _AffID;
            }
        }
        
        // verify a valid team was selected
        _Team = verifyTeam(_Team);
        
        // buy core 
        buyCore(_PID, _AffID, _Team, _eventData_);
    }
    
    /**
     * @dev essentially the same as buy, but instead of you sending ether 
     * from your wallet, it uses your unwithdrawn earnings.
     * -functionhash- 0x349cdcac (using ID for affiliate)
     * -functionhash- 0x82bfc739 (using address for affiliate)
     * -functionhash- 0x079ce327 (using name for affiliate)
     *  _affCode the ID/address/name of the player who gets the affiliate fee
     *  _Team what team is the player playing for?
     *  _eth amount of earnings to use (remainder returned to gen vault)
     */
    function reLoadXid(uint256 _AffCode, uint256 _Team, uint256 _Eth)
        isActivated()
        isHuman()
        isWithinLimits(_Eth)
        public
    {
        // set up our tx event data
        F3Ddatasets.EventReturns memory _eventData_;
        
        // fetch player ID
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // manage affiliate residuals
        // if no affiliate code was given or player tried to use their own, lolz
        if (_AffCode == 0 || _AffCode == _PID)
        {
            // use last stored affiliate code 
            _AffCode = plyr_[_PID].laff;
            
        // if affiliate code was given & its not the same as previously stored 
        } else if (_AffCode != plyr_[_PID].laff) {
            // update last affiliate 
            plyr_[_PID].laff = _AffCode;
        }

        // verify a valid team was selected
        _Team = verifyTeam(_Team);

        // reload core
        reLoadCore(_PID, _AffCode, _Team, _Eth, _eventData_);
    }
    
    function reLoadXaddr(address _AffCode, uint256 _Team, uint256 _Eth)
        isActivated()
        isHuman()
        isWithinLimits(_Eth)
        public
    {
        // set up our tx event data
        F3Ddatasets.EventReturns memory _eventData_;
        
        // fetch player ID
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // manage affiliate residuals
        uint256 _AffID;
        // if no affiliate code was given or player tried to use their own, lolz
        if (_AffCode == address(0) || _AffCode == msg.sender)
        {
            // use last stored affiliate code
            _AffID = plyr_[_PID].laff;
        
        // if affiliate code was given    
        } else {
            // get affiliate ID from aff Code 
            _AffID = pIDxAddr_[_AffCode];
            
            // if affID is not the same as previously stored 
            if (_AffID != plyr_[_PID].laff)
            {
                // update last affiliate
                plyr_[_PID].laff = _AffID;
            }
        }
        
        // verify a valid team was selected
        _Team = verifyTeam(_Team);
        
        // reload core
        reLoadCore(_PID, _AffID, _Team, _Eth, _eventData_);
    }
    
    function reLoadXname(bytes32 _AffCode, uint256 _Team, uint256 _Eth)
        isActivated()
        isHuman()
        isWithinLimits(_Eth)
        public
    {
        // set up our tx event data
        F3Ddatasets.EventReturns memory _eventData_;
        
        // fetch player ID
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // manage affiliate residuals
        uint256 _AffID;
        // if no affiliate code was given or player tried to use their own, lolz
        if (_AffCode == '' || _AffCode == plyr_[_PID].name)
        {
            // use last stored affiliate code
            _AffID = plyr_[_PID].laff;
        
        // if affiliate code was given
        } else {
            // get affiliate ID from aff Code
            _AffID = pIDxName_[_AffCode];
            
            // if affID is not the same as previously stored
            if (_AffID != plyr_[_PID].laff)
            {
                // update last affiliate
                plyr_[_PID].laff = _AffID;
            }
        }
        
        // verify a valid team was selected
        _Team = verifyTeam(_Team);
        
        // reload core
        reLoadCore(_PID, _AffID, _Team, _Eth, _eventData_);
    }

    /**
     * @dev withdraws all of your earnings.
     * -functionhash- 0x3ccfd60b
     */
    function withdraw()
        isActivated()
        isHuman()
        external
    {
        // setup local rID 
        uint256 _RID = rID_;
        
        // grab time
        uint256 _now = now;
        
        // fetch player ID
        uint256 _PID = pIDxAddr_[msg.sender];
        
        // setup temp var for player eth
        uint256 _eth;
        
        // check to see if round has ended and no one has run round end yet
        if (_now > round_[_RID].end && round_[_RID].ended == false && round_[_RID].plyr != 0)
        {
            // set up our tx event data
            F3Ddatasets.EventReturns memory _eventData_;
            
            // end the round (distributes pot)
			round_[_RID].ended = true;
            _eventData_ = endRound(_eventData_);
            
			// get their earnings
            _eth = withdrawEarnings(_PID);
            
            // gib moni
            if (_eth > 0)
                plyr_[_PID].addr.transfer(_eth);    
            
            // build event data
            _eventData_.compressedData = _eventData_.compressedData + (_now * 1000000000000000000);
            _eventData_.compressedIDs = _eventData_.compressedIDs + _PID;
            
            // fire withdraw and distribute event
            emit F3Devents.OnWithdrawAndDistribute
            (
                msg.sender, 
                plyr_[_PID].name, 
                _eth, 
                _eventData_.compressedData, 
                _eventData_.compressedIDs, 
                _eventData_.winnerAddr, 
                _eventData_.winnerName, 
                _eventData_.amountWon, 
                _eventData_.newPot, 
                _eventData_.P3DAmount, 
                _eventData_.genAmount
            );
            
        // in any other situation
        } else {
            // get their earnings
            _eth = withdrawEarnings(_PID);
            
            // gib moni
            if (_eth > 0)
                plyr_[_PID].addr.transfer(_eth);
            
            // fire withdraw event
            emit F3Devents.OnWithdraw(_PID, msg.sender, plyr_[_PID].name, _eth, _now);
        }
    }
    
    /**
     * @dev use these to register names.  they are just wrappers that will send the
     * registration requests to the PlayerBook contract.  So registering here is the 
     * same as registering there.  UI will always display the last name you registered.
     * but you will still own all previously registered names to use as affiliate 
     * links.
     * - must pay a registration fee.
     * - name must be unique
     * - names will be converted to lowercase
     * - name cannot start or end with a space 
     * - cannot have more than 1 space in a row
     * - cannot be only numbers
     * - cannot start with 0x 
     * - name must be at least 1 char
     * - max length of 32 characters long
     * - allowed characters: a-z, 0-9, and space
     * -functionhash- 0x921dec21 (using ID for affiliate)
     * -functionhash- 0x3ddd4698 (using address for affiliate)
     * -functionhash- 0x685ffd83 (using name for affiliate)
     *  _NameString players desired name
     *  _affCode affiliate ID, address, or name of who referred you
     *  _all set to true if you want this to push your info to all games 
     * (this might cost a lot of gas)
     */
    function registerNameXID(string _NameString, uint256 _AffCode, bool _All)
        isHuman()
        external
        payable
    {
        bytes32 _Name = _NameString.nameFilter();
        address _Addr = msg.sender;
        uint256 _paid = msg.value;
        (bool _isNewPlayer, uint256 _AffID) = PlayerBook.registerNameXIDFromDapp.value(_paid)(_Addr, _Name, _AffCode, _All);
        
        uint256 _PID = pIDxAddr_[_Addr];
        
        // fire event
        emit F3Devents.OnNewName(_PID, _Addr, _Name, _isNewPlayer, _AffID, plyr_[_AffID].addr, plyr_[_AffID].name, _paid, now);
    }
    
    function registerNameXaddr(string _NameString, address _AffCode, bool _All)
        isHuman()
        external
        payable
    {
        bytes32 _Name = _NameString.nameFilter();
        address _Addr = msg.sender;
        uint256 _paid = msg.value;
        (bool _isNewPlayer, uint256 _AffID) = PlayerBook.registerNameXaddrFromDapp.value(msg.value)(msg.sender, _Name, _AffCode, _All);
        
        uint256 _PID = pIDxAddr_[_Addr];
        
        // fire event
        emit F3Devents.OnNewName(_PID, _Addr, _Name, _isNewPlayer, _AffID, plyr_[_AffID].addr, plyr_[_AffID].name, _paid, now);
    }
    
    function registerNameXname(string _NameString, bytes32 _AffCode, bool _All)
        isHuman()
        external
        payable
    {
        bytes32 _Name = _NameString.nameFilter();
        address _Addr = msg.sender;
        uint256 _paid = msg.value;
        (bool _isNewPlayer, uint256 _AffID) = PlayerBook.registerNameXnameFromDapp.value(msg.value)(msg.sender, _Name, _AffCode, _All);
        
        uint256 _PID = pIDxAddr_[_Addr];
        
        // fire event
        emit F3Devents.OnNewName(_PID, _Addr, _Name, _isNewPlayer, _AffID, plyr_[_AffID].addr, plyr_[_AffID].name, _paid, now);
    }
//==============================================================================
//     _  _ _|__|_ _  _ _  .
//    (_|(/_ |  | (/_| _\  . (for UI & viewing things on etherscan)
//=====_|=======================================================================
    /**
     * @dev return the price buyer will pay for next 1 individual key.
     * -functionhash- 0x018a25e8
     * @return price for next key bought (in wei format)
     */
    function getBuyPrice()
        external 
        view 
        returns(uint256)
    {  
        // setup local rID
        uint256 _RID = rID_;
        
        // grab time
        uint256 _now = now;
        
        // are we in a round?
        if (_now > round_[_RID].strt + RNDGAP_ && (_now <= round_[_RID].end || (_now > round_[_RID].end && round_[_RID].plyr == 0)))
            return ( (round_[_RID].keys.add(1000000000000000000)).ethRec(1000000000000000000) );
        else // rounds over.  need price for new round
            return ( 75000000000000 ); // init
    }
    
    /**
     * @dev returns time left.  dont spam this, you'll ddos yourself from your node 
     * provider
     * -functionhash- 0xc7e284b8
     * @return time left in seconds
     */
    function getTimeLeft()
        external
        view
        returns(uint256)
    {
        // setup local rID
        uint256 _RID = rID_;
        
        // grab time
        uint256 _now = now;
        
        if (_now < round_[_RID].end)
            if (_now > round_[_RID].strt + RNDGAP_)
                return( (round_[_RID].end).sub(_now) );
            else
                return( (round_[_RID].strt + RNDGAP_).sub(_now) );
        else
            return(0);
    }
    
    /**
     * @dev returns player earnings per vaults 
     * -functionhash- 0x63066434
     * @return winnings vault
     * @return general vault
     * @return affiliate vault
     */
    function getPlayerVaults(uint256 _PID)
        external
        view
        returns(uint256 ,uint256, uint256)
    {
        // setup local rID
        uint256 _RID = rID_;
        
        // if round has ended.  but round end has not been run (so contract has not distributed winnings)
        if (now > round_[_RID].end && round_[_RID].ended == false && round_[_RID].plyr != 0)
        {
            // if player is winner 
            if (round_[_RID].plyr == _PID)
            {
                return
                (
                    (plyr_[_PID].win).add( ((round_[_RID].pot).mul(48)) / 100 ),
                    (plyr_[_PID].gen).add(  getPlayerVaultsHelper(_PID, _RID).sub(plyrRnds_[_PID][_RID].mask)   ),
                    plyr_[_PID].aff
                );
            // if player is not the winner
            } else {
                return
                (
                    plyr_[_PID].win,
                    (plyr_[_PID].gen).add(  getPlayerVaultsHelper(_PID, _RID).sub(plyrRnds_[_PID][_RID].mask)  ),
                    plyr_[_PID].aff
                );
            }
            
        // if round is still going on, or round has ended and round end has been ran
        } else {
            return
            (
                plyr_[_PID].win,
                (plyr_[_PID].gen).add(calcUnMaskedEarnings(_PID, plyr_[_PID].lrnd)),
                plyr_[_PID].aff
            );
        }
    }
    
    /**
     * solidity hates stack limits.  this lets us avoid that hate 
     */
    function getPlayerVaultsHelper(uint256 _PID, uint256 _RID)
        private
        view
        returns(uint256)
    {
        return(  ((((round_[_RID].mask).add(((((round_[_RID].pot).mul(potSplit_[round_[_RID].team].gen)) / 100).mul(1000000000000000000)) / (round_[_RID].keys))).mul(plyrRnds_[_PID][_RID].keys)) / 1000000000000000000)  );
    }
    
    /**
     * @dev returns all current round info needed for front end
     * -functionhash- 0x747dff42
     * @return eth invested during ICO phase
     * @return round id 
     * @return total keys for round 
     * @return time round ends
     * @return time round started
     * @return current pot 
     * @return current team ID & player ID in lead 
     * @return current player in leads address 
     * @return current player in leads name
     * @return whales eth in for round
     * @return bears eth in for round
     * @return sneks eth in for round
     * @return bulls eth in for round
     * @return airdrop tracker # & airdrop pot
     */
    function getCurrentRoundInfo()
        external
        view
        returns(uint256, uint256, uint256, uint256, uint256, uint256, uint256, address, bytes32, uint256, uint256, uint256, uint256, uint256)
    {
        // setup local rID
        uint256 _RID = rID_;
        
        return
        (
            round_[_RID].ico,               //0
            _RID,                           //1
            round_[_RID].keys,              //2
            round_[_RID].end,               //3
            round_[_RID].strt,              //4
            round_[_RID].pot,               //5
            (round_[_RID].team + (round_[_RID].plyr * 10)),     //6
            plyr_[round_[_RID].plyr].addr,  //7
            plyr_[round_[_RID].plyr].name,  //8
            rndTmEth_[_RID][0],             //9
            rndTmEth_[_RID][1],             //10
            rndTmEth_[_RID][2],             //11
            rndTmEth_[_RID][3],             //12
            airDropTracker_ + (airDropPot_ * 1000)              //13
        );
    }

    /**
     * @dev returns player info based on address.  if no address is given, it will 
     * use msg.sender 
     * -functionhash- 0xee0b5d8b
     *  _Addr address of the player you want to lookup 
     * @return player ID 
     * @return player name
     * @return keys owned (current round)
     * @return winnings vault
     * @return general vault 
     * @return affiliate vault 
	 * @return player round eth
     */
    function getPlayerInfoByAddress(address _Addr)
        external 
        view 
        returns(uint256, bytes32, uint256, uint256, uint256, uint256, uint256)
    {
        // setup local rID
        uint256 _RID = rID_;
        
        if (_Addr == address(0))
        {
            _Addr == msg.sender;
        }
        uint256 _PID = pIDxAddr_[_Addr];
        
        return
        (
            _PID,                               //0
            plyr_[_PID].name,                   //1
            plyrRnds_[_PID][_RID].keys,         //2
            plyr_[_PID].win,                    //3
            (plyr_[_PID].gen).add(calcUnMaskedEarnings(_PID, plyr_[_PID].lrnd)),       //4
            plyr_[_PID].aff,                    //5
            plyrRnds_[_PID][_RID].eth           //6
        );
    }

//==============================================================================
//     _ _  _ _   | _  _ . _  .
//    (_(_)| (/_  |(_)(_||(_  . (this + tools + calcs + modules = our softwares engine)
//=====================_|=======================================================
    /**
     * @dev logic runs whenever a buy order is executed.  determines how to handle 
     * incoming eth depending on if we are in an active round or not
     */
    function buyCore(uint256 _PID, uint256 _AffID, uint256 _Team, F3Ddatasets.EventReturns memory _EventData_)
        private
    {
        // setup local rID
        uint256 _RID = rID_;
        
        // grab time
        uint256 _now = now;
        
        // if round is active
        if (_now > round_[_RID].strt + RNDGAP_ && (_now <= round_[_RID].end || (_now > round_[_RID].end && round_[_RID].plyr == 0))) 
        {
            // call core 
            core(_RID, _PID, msg.value, _AffID, _Team, _EventData_);
        
        // if round is not active     
        } else {
            // check to see if end round needs to be ran
            if (_now > round_[_RID].end && round_[_RID].ended == false) 
            {
                // end the round (distributes pot) & start new round
			    round_[_RID].ended = true;
                _EventData_ = endRound(_EventData_);
                
                // build event data
                _EventData_.compressedData = _EventData_.compressedData + (_now * 1000000000000000000);
                _EventData_.compressedIDs = _EventData_.compressedIDs + _PID;
                
                // fire buy and distribute event 
                emit F3Devents.OnBuyAndDistribute
                (
                    msg.sender, 
                    plyr_[_PID].name, 
                    msg.value, 
                    _EventData_.compressedData, 
                    _EventData_.compressedIDs, 
                    _EventData_.winnerAddr, 
                    _EventData_.winnerName, 
                    _EventData_.amountWon, 
                    _EventData_.newPot, 
                    _EventData_.P3DAmount, 
                    _EventData_.genAmount
                );
            }
            
            // put eth in players vault 
            plyr_[_PID].gen = plyr_[_PID].gen.add(msg.value);
        }
    }
    
    /**
     * @dev logic runs whenever a reload order is executed.  determines how to handle 
     * incoming eth depending on if we are in an active round or not 
     */
    function reLoadCore(uint256 _PID, uint256 _AffID, uint256 _Team, uint256 _Eth, F3Ddatasets.EventReturns memory _EventData_)
        private
    {
        // setup local rID
        uint256 _RID = rID_;
        
        // grab time
        uint256 _now = now;
        
        // if round is active
        if (_now > round_[_RID].strt + RNDGAP_ && (_now <= round_[_RID].end || (_now > round_[_RID].end && round_[_RID].plyr == 0))) 
        {
            // get earnings from all vaults and return unused to gen vault
            // because we use a custom safemath library.  this will throw if player 
            // tried to spend more eth than they have.
            plyr_[_PID].gen = withdrawEarnings(_PID).sub(_Eth);
            
            // call core 
            core(_RID, _PID, _Eth, _AffID, _Team, _EventData_);
        
        // if round is not active and end round needs to be ran   
        } else if (_now > round_[_RID].end && round_[_RID].ended == false) {
            // end the round (distributes pot) & start new round
            round_[_RID].ended = true;
            _EventData_ = endRound(_EventData_);
                
            // build event data
            _EventData_.compressedData = _EventData_.compressedData + (_now * 1000000000000000000);
            _EventData_.compressedIDs = _EventData_.compressedIDs + _PID;
                
            // fire buy and distribute event 
            emit F3Devents.OnReLoadAndDistribute
            (
                msg.sender, 
                plyr_[_PID].name, 
                _EventData_.compressedData, 
                _EventData_.compressedIDs, 
                _EventData_.winnerAddr, 
                _EventData_.winnerName, 
                _EventData_.amountWon, 
                _EventData_.newPot, 
                _EventData_.P3DAmount, 
                _EventData_.genAmount
            );
        }
    }
    
    /**
     * @dev this is the core logic for any buy/reload that happens while a round 
     * is live.
     */
    function core(uint256 _RID, uint256 _PID, uint256 _Eth, uint256 _AffID, uint256 _Team, F3Ddatasets.EventReturns memory _EventData_)
        private
    {
        // if player is new to round
        if (plyrRnds_[_PID][_RID].keys == 0)
            _EventData_ = managePlayer(_PID, _EventData_);
        
        // early round eth limiter 
        if (round_[_RID].eth < 100000000000000000000 && plyrRnds_[_PID][_RID].eth.add(_Eth) > 1000000000000000000)
        {
            uint256 _availableLimit = (1000000000000000000).sub(plyrRnds_[_PID][_RID].eth);
            uint256 _refund = _Eth.sub(_availableLimit);
            plyr_[_PID].gen = plyr_[_PID].gen.add(_refund);
            _Eth = _availableLimit;
        }
        
        // if eth left is greater than min eth allowed (sorry no pocket lint)
        if (_Eth > 1000000000) 
        {
            
            // mint the new keys
            uint256 _keys = (round_[_RID].eth).keysRec(_Eth);
            
            // if they bought at least 1 whole key
            if (_keys >= 1000000000000000000)
            {
            updateTimer(_keys, _RID);

            // set new leaders
            if (round_[_RID].plyr != _PID)
                round_[_RID].plyr = _PID;  
            if (round_[_RID].team != _Team)
                round_[_RID].team = _Team; 
            
            // set the new leader bool to true
            _EventData_.compressedData = _EventData_.compressedData + 100;
        }
            
            // manage airdrops
            if (_Eth >= 100000000000000000)
            {
            airDropTracker_++;
            if (airdrop() == true)
            {
                // gib muni
                uint256 _prize;
                if (_Eth >= 10000000000000000000)
                {
                    // calculate prize and give it to winner
                    _prize = ((airDropPot_).mul(75)) / 100;
                    plyr_[_PID].win = (plyr_[_PID].win).add(_prize);
                    
                    // adjust airDropPot 
                    airDropPot_ = (airDropPot_).sub(_prize);
                    
                    // let event know a tier 3 prize was won 
                    _EventData_.compressedData += 300000000000000000000000000000000;
                } else if (_Eth >= 1000000000000000000 && _Eth < 10000000000000000000) {
                    // calculate prize and give it to winner
                    _prize = ((airDropPot_).mul(50)) / 100;
                    plyr_[_PID].win = (plyr_[_PID].win).add(_prize);
                    
                    // adjust airDropPot 
                    airDropPot_ = (airDropPot_).sub(_prize);
                    
                    // let event know a tier 2 prize was won 
                    _EventData_.compressedData += 200000000000000000000000000000000;
                } else if (_Eth >= 100000000000000000 && _Eth < 1000000000000000000) {
                    // calculate prize and give it to winner
                    _prize = ((airDropPot_).mul(25)) / 100;
                    plyr_[_PID].win = (plyr_[_PID].win).add(_prize);
                    
                    // adjust airDropPot 
                    airDropPot_ = (airDropPot_).sub(_prize);
                    
                    // let event know a tier 3 prize was won 
                    _EventData_.compressedData += 300000000000000000000000000000000;
                }
                // set airdrop happened bool to true
                _EventData_.compressedData += 10000000000000000000000000000000;
                // let event know how much was won 
                _EventData_.compressedData += _prize * 1000000000000000000000000000000000;
                
                // reset air drop tracker
                airDropTracker_ = 0;
            }
        }
    
            // store the air drop tracker number (number of buys since last airdrop)
            _EventData_.compressedData = _EventData_.compressedData + (airDropTracker_ * 1000);
            
            // update player 
            plyrRnds_[_PID][_RID].keys = _keys.add(plyrRnds_[_PID][_RID].keys);
            plyrRnds_[_PID][_RID].eth = _Eth.add(plyrRnds_[_PID][_RID].eth);
            
            // update round
            round_[_RID].keys = _keys.add(round_[_RID].keys);
            round_[_RID].eth = _Eth.add(round_[_RID].eth);
            rndTmEth_[_RID][_Team] = _Eth.add(rndTmEth_[_RID][_Team]);
    
            // distribute eth
            _EventData_ = distributeExternal(_RID, _PID, _Eth, _AffID, _Team, _EventData_);
            _EventData_ = distributeInternal(_RID, _PID, _Eth, _Team, _keys, _EventData_);
            
            // call end tx function to fire end tx event.
		    endTx(_PID, _Team, _Eth, _keys, _EventData_);
        }
    }
//==============================================================================
//     _ _ | _   | _ _|_ _  _ _  .
//    (_(_||(_|_||(_| | (_)| _\  .
//==============================================================================
    /**
     * @dev calculates unmasked earnings (just calculates, does not update mask)
     * @return earnings in wei format
     */
    function calcUnMaskedEarnings(uint256 _PID, uint256 _RIDlast)
        private
        view
        returns(uint256)
    {
        return(  (((round_[_RIDlast].mask).mul(plyrRnds_[_PID][_RIDlast].keys)) / (1000000000000000000)).sub(plyrRnds_[_PID][_RIDlast].mask)  );
    }
    
    /** 
     * @dev returns the amount of keys you would get given an amount of eth. 
     * -functionhash- 0xce89c80c
     *  _RID round ID you want price for
     *  _eth amount of eth sent in 
     * @return keys received 
     */
    function calcKeysReceived(uint256 _RID, uint256 _Eth)
        external
        view
        returns(uint256)
    {
        // grab time
        uint256 _now = now;
        
        // are we in a round?
        if (_now > round_[_RID].strt + RNDGAP_ && (_now <= round_[_RID].end || (_now > round_[_RID].end && round_[_RID].plyr == 0)))
            return ( (round_[_RID].eth).keysRec(_Eth) );
        else // rounds over.  need keys for new round
            return ( (_Eth).keys() );
    }
    
    /** 
     * @dev returns current eth price for X keys.  
     * -functionhash- 0xcf808000
     *  _keys number of keys desired (in 18 decimal format)
     * @return amount of eth needed to send
     */
    function iWantXKeys(uint256 _Keys)
        external
        view
        returns(uint256)
    {
        // setup local rID
        uint256 _RID = rID_;
        
        // grab time
        uint256 _now = now;
        
        // are we in a round?
        if (_now > round_[_RID].strt + RNDGAP_ && (_now <= round_[_RID].end || (_now > round_[_RID].end && round_[_RID].plyr == 0)))
            return ( (round_[_RID].keys.add(_Keys)).ethRec(_Keys) );
        else // rounds over.  need price for new round
            return ( (_Keys).eth() );
    }
//==============================================================================
//    _|_ _  _ | _  .
//     | (_)(_)|_\  .
//==============================================================================
    /**
	 * @dev receives name/player info from names contract 
     */
    function receivePlayerInfo(uint256 _PID, address _Addr, bytes32 _Name, uint256 _Laff)
        external
    {
        require (msg.sender == address(PlayerBook), "your not playerNames contract... hmmm..");
        if (pIDxAddr_[_Addr] != _PID)
            pIDxAddr_[_Addr] = _PID;
        if (pIDxName_[_Name] != _PID)
            pIDxName_[_Name] = _PID;
        if (plyr_[_PID].addr != _Addr)
            plyr_[_PID].addr = _Addr;
        if (plyr_[_PID].name != _Name)
            plyr_[_PID].name = _Name;
        if (plyr_[_PID].laff != _Laff)
            plyr_[_PID].laff = _Laff;
        if (plyrNames_[_PID][_Name] == false)
            plyrNames_[_PID][_Name] = true;
    }
    
    /**
     * @dev receives entire player name list 
     */
    function receivePlayerNameList(uint256 _PID, bytes32 _Name)
        external
    {
        require (msg.sender == address(PlayerBook), "your not playerNames contract... hmmm..");
        if(plyrNames_[_PID][_Name] == false)
            plyrNames_[_PID][_Name] = true;
    }   
        
    /**
     * @dev gets existing or registers new pID.  use this when a player may be new
     * @return pID 
     */
    function determinePID(F3Ddatasets.EventReturns memory _EventData_)
        private
        returns (F3Ddatasets.EventReturns)
    {
        uint256 _PID = pIDxAddr_[msg.sender];
        // if player is new to this version of fomo3d
        if (_PID == 0)
        {
            // grab their player ID, name and last aff ID, from player names contract 
            _PID = PlayerBook.getPlayerID(msg.sender);
            bytes32 _Name = PlayerBook.getPlayerName(_PID);
            uint256 _laff = PlayerBook.getPlayerLAff(_PID);
            
            // set up player account 
            pIDxAddr_[msg.sender] = _PID;
            plyr_[_PID].addr = msg.sender;
            
            if (_Name != "")
            {
                pIDxName_[_Name] = _PID;
                plyr_[_PID].name = _Name;
                plyrNames_[_PID][_Name] = true;
            }
            
            if (_laff != 0 && _laff != _PID)
                plyr_[_PID].laff = _laff;
            
            // set the new player bool to true
            _EventData_.compressedData = _EventData_.compressedData + 1;
        } 
        return (_EventData_);
    }
    
    /**
     * @dev checks to make sure user picked a valid team.  if not sets team 
     * to default (sneks)
     */
    function verifyTeam(uint256 _Team)
        private
        pure
        returns (uint256)
    {
        if (_Team < 0 || _Team > 3)
            return(2);
        else
            return(_Team);
    }
    
    /**
     * @dev decides if round end needs to be run & new round started.  and if 
     * player unmasked earnings from previously played rounds need to be moved.
     */
    function managePlayer(uint256 _PID, F3Ddatasets.EventReturns memory _EventData_)
        private
        returns (F3Ddatasets.EventReturns)
    {
        // if player has played a previous round, move their unmasked earnings
        // from that round to gen vault.
        if (plyr_[_PID].lrnd != 0)
            updateGenVault(_PID, plyr_[_PID].lrnd);
            
        // update player's last round played
        plyr_[_PID].lrnd = rID_;
            
        // set the joined round bool to true
        _EventData_.compressedData = _EventData_.compressedData + 10;
        
        return(_EventData_);
    }
    
    /**
     * @dev ends the round. manages paying out winner/splitting up pot
     */
    function endRound(F3Ddatasets.EventReturns memory _EventData_)
        private
        returns (F3Ddatasets.EventReturns)
    {
        // setup local rID
        uint256 _RID = rID_;
        
        // grab our winning player and team id's
        uint256 _winPID = round_[_RID].plyr;
        uint256 _winTID = round_[_RID].team;
        
        // grab our pot amount
        uint256 _pot = round_[_RID].pot;
        
        // calculate our winner share, community rewards, gen share, 
        // p3d share, and amount reserved for next pot 
        uint256 _win = (_pot.mul(48)) / 100;
        uint256 _com = (_pot / 20);
        uint256 _gen = (_pot.mul(potSplit_[_winTID].gen)) / 100;
        uint256 _p3d = (_pot.mul(potSplit_[_winTID].p3d)) / 100;
        uint256 _res = (((_pot.sub(_win)).sub(_com)).sub(_gen)).sub(_p3d);
        
        // calculate ppt for round mask
        uint256 _ppt = (_gen.mul(1000000000000000000)) / (round_[_RID].keys);
        uint256 _dust = _gen.sub((_ppt.mul(round_[_RID].keys)) / 1000000000000000000);
        if (_dust > 0)
        {
            _gen = _gen.sub(_dust);
            _res = _res.add(_dust);
        }
        
        // pay our winner
        plyr_[_winPID].win = _win.add(plyr_[_winPID].win);
        
        // community rewards
        
        TEAMWALLET.transfer(_com);
        
        // if (!address(Jekyll_Island_Inc).call.value(_com)(bytes4(keccak256("deposit()"))))
        // {
        //     // This ensures Team Just cannot influence the outcome of FoMo3D with
        //     // bank migrations by breaking outgoing transactions.
        //     // Something we would never do. But that's not the point.
        //     // We spent 2000$ in eth re-deploying just to patch this, we hold the 
        //     // highest belief that everything we create should be trustless.
        //     // Team JUST, The name you shouldn't have to trust.
        //     _p3d = _p3d.add(_com);
        //     _com = 0;
        // }
        
        // distribute gen portion to key holders
        round_[_RID].mask = _ppt.add(round_[_RID].mask);
        
        // send share for p3d to divies
        // if (_p3d > 0)
        //     Divies.deposit.value(_p3d)();
            
        // prepare event data
        _EventData_.compressedData = _EventData_.compressedData + (round_[_RID].end * 1000000);
        _EventData_.compressedIDs = _EventData_.compressedIDs + (_winPID * 100000000000000000000000000) + (_winTID * 100000000000000000);
        _EventData_.winnerAddr = plyr_[_winPID].addr;
        _EventData_.winnerName = plyr_[_winPID].name;
        _EventData_.amountWon = _win;
        _EventData_.genAmount = _gen;
        _EventData_.P3DAmount = _p3d;
        _EventData_.newPot = _res;
        
        // start next round
        rID_++;
        _RID++;
        round_[_RID].strt = now;
        round_[_RID].end = now.add(RNDINIT_).add(RNDGAP_);
        round_[_RID].pot = _res;
        
        return(_EventData_);
    }
    
    /**
     * @dev moves any unmasked earnings to gen vault.  updates earnings mask
     */
    function updateGenVault(uint256 _PID, uint256 _RIDlast)
        private 
    {
        uint256 _earnings = calcUnMaskedEarnings(_PID, _RIDlast);
        if (_earnings > 0)
        {
            // put in gen vault
            plyr_[_PID].gen = _earnings.add(plyr_[_PID].gen);
            // zero out their earnings by updating mask
            plyrRnds_[_PID][_RIDlast].mask = _earnings.add(plyrRnds_[_PID][_RIDlast].mask);
        }
    }
    
    /**
     * @dev updates round timer based on number of whole keys bought.
     */
    function updateTimer(uint256 _Keys, uint256 _RID)
        private
    {
        // grab time
        uint256 _now = now;
        
        // calculate time based on number of keys bought
        uint256 _newTime;
        if (_now > round_[_RID].end && round_[_RID].plyr == 0)
            _newTime = (((_Keys) / (1000000000000000000)).mul(RNDINC_)).add(_now);
        else
            _newTime = (((_Keys) / (1000000000000000000)).mul(RNDINC_)).add(round_[_RID].end);
        
        // compare to max and set new end time
        if (_newTime < (RNDMAX_).add(_now))
            round_[_RID].end = _newTime;
        else
            round_[_RID].end = RNDMAX_.add(_now);
    }
    
    /**
     * @dev generates a random number between 0-99 and checks to see if thats
     * resulted in an airdrop win
     * @return do we have a winner?
     */
    function airdrop()
        private 
        view 
        returns(bool)
    {
        uint256 seed = uint256(keccak256(abi.encodePacked(
            
            (block.timestamp).add
            (block.difficulty).add
            ((uint256(keccak256(abi.encodePacked(block.coinbase)))) / (now)).add
            (block.gaslimit).add
            ((uint256(keccak256(abi.encodePacked(msg.sender)))) / (now)).add
            (block.number)
            
        )));
        if((seed - ((seed / 1000) * 1000)) < airDropTracker_)
            return(true);
        else
            return(false);
    }

    /**
     * @dev distributes eth based on fees to com, aff, and p3d
     */
    function distributeExternal(uint256 _RID, uint256 _PID, uint256 _Eth, uint256 _AffID, uint256 _Team, F3Ddatasets.EventReturns memory _EventData_)
        private
        returns(F3Ddatasets.EventReturns)
    {
        // pay 10% out to community rewards
        uint256 _com = _Eth / 10;
        //uint256 _p3d;

        TEAMWALLET.transfer(_com);
        // if (!address(Jekyll_Island_Inc).call.value(_com)(bytes4(keccak256("deposit()"))))
        // {
        //     // This ensures Team Just cannot influence the outcome of FoMo3D with
        //     // bank migrations by breaking outgoing transactions.
        //     // Something we would never do. But that's not the point.
        //     // We spent 2000$ in eth re-deploying just to patch this, we hold the 
        //     // highest belief that everything we create should be trustless.
        //     // Team JUST, The name you shouldn't have to trust.
        //     _p3d = _com;
        //     _com = 0;
        // }
        
        // pay 1% out to FoMo3D short
        uint256 _leader = _Eth / 20;
        //otherF3D_.potSwap.value(_long)();
        
        // distribute share to affiliate
        uint256 _aff = _Eth / 10;
        
        // decide what to do with affiliate share of fees
        // affiliate must not be self, and must have a name registered
        if (_AffID != _PID && plyr_[_AffID].name != '') {
            plyr_[_AffID].aff = _aff.add(plyr_[_AffID].aff);
            emit F3Devents.OnAffiliatePayout(_AffID, plyr_[_AffID].addr, plyr_[_AffID].name, _RID, _PID, _aff, now);
        } else {
            _leader =_leader.add(_aff);
        }
        
        leaderWallets[_Team].transfer(_leader);

        // pay out p3d
        // _p3d = _p3d.add((_eth.mul(fees_[_Team].p3d)) / (100));
        // if (_p3d > 0)
        // {
        //     // deposit to divies contract
        //     Divies.deposit.value(_p3d)();
            
        //     // set up event data
        //     _eventData_.P3DAmount = _p3d.add(_eventData_.P3DAmount);
        // }
        
        return(_EventData_);
    }
    
    function potSwap()
        external
        payable
    {
        // setup local rID
        uint256 _RID = rID_ + 1;
        
        round_[_RID].pot = round_[_RID].pot.add(msg.value);
        emit F3Devents.OnPotSwapDeposit(_RID, msg.value);
    }
    
    /**
     * @dev distributes eth based on fees to gen and pot
     */
    function distributeInternal(uint256 _RID, uint256 _PID, uint256 _Eth, uint256 _Team, uint256 _Keys, F3Ddatasets.EventReturns memory _EventData_)
        private
        returns(F3Ddatasets.EventReturns)
    {
        // calculate gen share
        uint256 _gen = (_Eth.mul(fees_[_Team].gen)) / 100;
        
        // toss 1% into airdrop pot 
        uint256 _air = (_Eth / 100);
        airDropPot_ = airDropPot_.add(_air);
        
        // update eth balance (eth = eth - (com share + pot swap share + aff share + p3d share + airdrop pot share))
        _Eth = _Eth.sub(((_Eth.mul(26)) / 100).add((_Eth.mul(fees_[_Team].p3d)) / 100));
        
        // calculate pot 
        uint256 _pot = _Eth.sub(_gen);
        
        // distribute gen share (thats what updateMasks() does) and adjust
        // balances for dust.
        uint256 _dust = updateMasks(_RID, _PID, _gen, _Keys);
        if (_dust > 0)
            _gen = _gen.sub(_dust);
        
        // add eth to pot
        round_[_RID].pot = _pot.add(_dust).add(round_[_RID].pot);
        
        // set up event data
        _EventData_.genAmount = _gen.add(_EventData_.genAmount);
        _EventData_.potAmount = _pot;
        
        return(_EventData_);
    }

    /**
     * @dev updates masks for round and player when keys are bought
     * @return dust left over 
     */
    function updateMasks(uint256 _RID, uint256 _PID, uint256 _Gen, uint256 _Keys)
        private
        returns(uint256)
    {
        /* MASKING NOTES
            earnings masks are a tricky thing for people to wrap their minds around.
            the basic thing to understand here.  is were going to have a global
            tracker based on profit per share for each round, that increases in
            relevant proportion to the increase in share supply.
            
            the player will have an additional mask that basically says "based
            on the rounds mask, my shares, and how much i've already withdrawn,
            how much is still owed to me?"
        */
        
        // calc profit per key & round mask based on this buy:  (dust goes to pot)
        uint256 _ppt = (_Gen.mul(1000000000000000000)) / (round_[_RID].keys);
        round_[_RID].mask = _ppt.add(round_[_RID].mask);
            
        // calculate player earning from their own buy (only based on the keys
        // they just bought).  & update player earnings mask
        uint256 _pearn = (_ppt.mul(_Keys)) / (1000000000000000000);
        plyrRnds_[_PID][_RID].mask = (((round_[_RID].mask.mul(_Keys)) / (1000000000000000000)).sub(_pearn)).add(plyrRnds_[_PID][_RID].mask);
        
        // calculate & return dust
        return(_Gen.sub((_ppt.mul(round_[_RID].keys)) / (1000000000000000000)));
    }
    
    /**
     * @dev adds up unmasked earnings, & vault earnings, sets them all to 0
     * @return earnings in wei format
     */
    function withdrawEarnings(uint256 _PID)
        private
        returns(uint256)
    {
        // update gen vault
        updateGenVault(_PID, plyr_[_PID].lrnd);
        
        // from vaults 
        uint256 _earnings = (plyr_[_PID].win).add(plyr_[_PID].gen).add(plyr_[_PID].aff);
        if (_earnings > 0)
        {
            plyr_[_PID].win = 0;
            plyr_[_PID].gen = 0;
            plyr_[_PID].aff = 0;
        }

        return(_earnings);
    }
    
    /**
     * @dev prepares compression data and fires event for buy or reload tx's
     */
    function endTx(uint256 _PID, uint256 _Team, uint256 _Eth, uint256 _Keys, F3Ddatasets.EventReturns memory _EventData_)
        private
    {
        _EventData_.compressedData = _EventData_.compressedData + (now * 1000000000000000000) + (_Team * 100000000000000000000000000000);
        _EventData_.compressedIDs = _EventData_.compressedIDs + _PID + (rID_ * 10000000000000000000000000000000000000000000000000000);
        
        emit F3Devents.OnEndTx
        (
            _EventData_.compressedData,
            _EventData_.compressedIDs,
            plyr_[_PID].name,
            msg.sender,
            _Eth,
            _Keys,
            _EventData_.winnerAddr,
            _EventData_.winnerName,
            _EventData_.amountWon,
            _EventData_.newPot,
            _EventData_.P3DAmount,
            _EventData_.genAmount,
            _EventData_.potAmount,
            airDropPot_
        );
    }
//==============================================================================
//    (~ _  _    _._|_    .
//    _)(/_(_|_|| | | \/  .
//====================/=========================================================
    /** upon contract deploy, it will be deactivated.  this is a one time
     * use function that will activate the contract.  we do this so devs 
     * have time to set things up on the web end                            **/
    bool public activated_ = false;
    function activate()
        onlyDevs()
        external
    {
		// make sure that its been linked.
        // can only be ran once
        require(activated_ == false, "fomo3d already activated");
        
        // activate the contract 
        activated_ = true;
        
        // lets start first round
		rID_ = 1;
        round_[1].strt = now + RNDEXTRA_ - RNDGAP_;
        round_[1].end = now + RNDINIT_ + RNDEXTRA_;
    }
}
