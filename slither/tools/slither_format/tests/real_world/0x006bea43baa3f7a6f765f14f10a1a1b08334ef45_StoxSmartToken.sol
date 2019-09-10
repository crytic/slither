pragma solidity ^0.4.11;

/*
    Owned contract interface
*/
contract IOwned {
    // this function isn't abstract since the compiler emits automatically generated getter functions as external
    function owner() public constant returns (address owner) { owner; }

    function transferOwnership(address _newOwner) public;
    function acceptOwnership() public;
}

/*
    ERC20 Standard Token interface
*/
contract IERC20Token {
    // these functions aren't abstract since the compiler emits automatically generated getter functions as external
    function name() public constant returns (string name) { name; }
    function symbol() public constant returns (string symbol) { symbol; }
    function decimals() public constant returns (uint8 decimals) { decimals; }
    function totalSupply() public constant returns (uint256 totalSupply) { totalSupply; }
    function balanceOf(address _owner) public constant returns (uint256 balance) { _owner; balance; }
    function allowance(address _owner, address _spender) public constant returns (uint256 remaining) { _owner; _spender; remaining; }

    function transfer(address _to, uint256 _value) public returns (bool success);
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success);
    function approve(address _spender, uint256 _value) public returns (bool success);
}

/*
    Token Holder interface
*/
contract ITokenHolder is IOwned {
    function withdrawTokens(IERC20Token _token, address _to, uint256 _amount) public;
}

/*
    Smart Token interface
*/
contract ISmartToken is ITokenHolder, IERC20Token {
    function disableTransfers(bool _disable) public;
    function issue(address _to, uint256 _amount) public;
    function destroy(address _from, uint256 _amount) public;
}

/*
    Overflow protected math functions
*/
contract SafeMath {
    /**
        constructor
    */
    function SafeMath() {
    }

    /**
        @dev returns the sum of _x and _y, asserts if the calculation overflows

        @param _x   value 1
        @param _y   value 2

        @return sum
    */
    function safeAdd(uint256 _x, uint256 _y) internal returns (uint256) {
        uint256 z = _x + _y;
        assert(z >= _x);
        return z;
    }

    /**
        @dev returns the difference of _x minus _y, asserts if the subtraction results in a negative number

        @param _x   minuend
        @param _y   subtrahend

        @return difference
    */
    function safeSub(uint256 _x, uint256 _y) internal returns (uint256) {
        assert(_x >= _y);
        return _x - _y;
    }

    /**
        @dev returns the product of multiplying _x by _y, asserts if the calculation overflows

        @param _x   factor 1
        @param _y   factor 2

        @return product
    */
    function safeMul(uint256 _x, uint256 _y) internal returns (uint256) {
        uint256 z = _x * _y;
        assert(_x == 0 || z / _x == _y);
        return z;
    }
}

/**
    ERC20 Standard Token implementation
*/
contract ERC20Token is IERC20Token, SafeMath {
    string public standard = 'Token 0.1';
    string public name = '';
    string public symbol = '';
    uint8 public decimals = 0;
    uint256 public totalSupply = 0;
    mapping (address => uint256) public balanceOf;
    mapping (address => mapping (address => uint256)) public allowance;

    event Transfer(address indexed _from, address indexed _to, uint256 _value);
    event Approval(address indexed _owner, address indexed _spender, uint256 _value);

    /**
        @dev constructor

        @param _name        token name
        @param _symbol      token symbol
        @param _decimals    decimal points, for display purposes
    */
    function ERC20Token(string _name, string _symbol, uint8 _decimals) {
        require(bytes(_name).length > 0 && bytes(_symbol).length > 0); // validate input

        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }

    // validates an address - currently only checks that it isn't null
    modifier validAddress(address _address) {
        require(_address != 0x0);
        _;
    }

    /**
        @dev send coins
        throws on any error rather then return a false flag to minimize user errors

        @param _to      target address
        @param _value   transfer amount

        @return true if the transfer was successful, false if it wasn't
    */
    function transfer(address _to, uint256 _value)
        public
        validAddress(_to)
        returns (bool success)
    {
        balanceOf[msg.sender] = safeSub(balanceOf[msg.sender], _value);
        balanceOf[_to] = safeAdd(balanceOf[_to], _value);
        Transfer(msg.sender, _to, _value);
        return true;
    }

    /**
        @dev an account/contract attempts to get the coins
        throws on any error rather then return a false flag to minimize user errors

        @param _from    source address
        @param _to      target address
        @param _value   transfer amount

        @return true if the transfer was successful, false if it wasn't
    */
    function transferFrom(address _from, address _to, uint256 _value)
        public
        validAddress(_from)
        validAddress(_to)
        returns (bool success)
    {
        allowance[_from][msg.sender] = safeSub(allowance[_from][msg.sender], _value);
        balanceOf[_from] = safeSub(balanceOf[_from], _value);
        balanceOf[_to] = safeAdd(balanceOf[_to], _value);
        Transfer(_from, _to, _value);
        return true;
    }

    /**
        @dev allow another account/contract to spend some tokens on your behalf
        throws on any error rather then return a false flag to minimize user errors

        also, to minimize the risk of the approve/transferFrom attack vector
        (see https://docs.google.com/document/d/1YLPtQxZu1UAvO9cZ1O2RPXBbT0mooh4DYKjA_jp-RLM/), approve has to be called twice
        in 2 separate transactions - once to change the allowance to 0 and secondly to change it to the new allowance value

        @param _spender approved address
        @param _value   allowance amount

        @return true if the approval was successful, false if it wasn't
    */
    function approve(address _spender, uint256 _value)
        public
        validAddress(_spender)
        returns (bool success)
    {
        // if the allowance isn't 0, it can only be updated to 0 to prevent an allowance change immediately after withdrawal
        require(_value == 0 || allowance[msg.sender][_spender] == 0);

        allowance[msg.sender][_spender] = _value;
        Approval(msg.sender, _spender, _value);
        return true;
    }
}

/*
    Provides support and utilities for contract ownership
*/
contract Owned is IOwned {
    address public owner;
    address public newOwner;

    event OwnerUpdate(address _prevOwner, address _newOwner);

    /**
        @dev constructor
    */
    function Owned() {
        owner = msg.sender;
    }

    // allows execution by the owner only
    modifier ownerOnly {
        assert(msg.sender == owner);
        _;
    }

    /**
        @dev allows transferring the contract ownership
        the new owner still need to accept the transfer
        can only be called by the contract owner

        @param _newOwner    new contract owner
    */
    function transferOwnership(address _newOwner) public ownerOnly {
        require(_newOwner != owner);
        newOwner = _newOwner;
    }

    /**
        @dev used by a new owner to accept an ownership transfer
    */
    function acceptOwnership() public {
        require(msg.sender == newOwner);
        OwnerUpdate(owner, newOwner);
        owner = newOwner;
        newOwner = 0x0;
    }
}

/*
    We consider every contract to be a 'token holder' since it's currently not possible
    for a contract to deny receiving tokens.

    The TokenHolder's contract sole purpose is to provide a safety mechanism that allows
    the owner to send tokens that were sent to the contract by mistake back to their sender.
*/
contract TokenHolder is ITokenHolder, Owned {
    /**
        @dev constructor
    */
    function TokenHolder() {
    }

    // validates an address - currently only checks that it isn't null
    modifier validAddress(address _address) {
        require(_address != 0x0);
        _;
    }

    // verifies that the address is different than this contract address
    modifier notThis(address _address) {
        require(_address != address(this));
        _;
    }

    /**
        @dev withdraws tokens held by the contract and sends them to an account
        can only be called by the owner

        @param _token   ERC20 token contract address
        @param _to      account to receive the new amount
        @param _amount  amount to withdraw
    */
    function withdrawTokens(IERC20Token _token, address _to, uint256 _amount)
        public
        ownerOnly
        validAddress(_token)
        validAddress(_to)
        notThis(_to)
    {
        assert(_token.transfer(_to, _amount));
    }
}

/*
    Smart Token v0.2

    'Owned' is specified here for readability reasons
*/
contract SmartToken is ISmartToken, ERC20Token, Owned, TokenHolder {
    string public version = '0.2';

    bool public transfersEnabled = true;    // true if transfer/transferFrom are enabled, false if not

    // triggered when a smart token is deployed - the _token address is defined for forward compatibility, in case we want to trigger the event from a factory
    event NewSmartToken(address _token);
    // triggered when the total supply is increased
    event Issuance(uint256 _amount);
    // triggered when the total supply is decreased
    event Destruction(uint256 _amount);

    /**
        @dev constructor

        @param _name       token name
        @param _symbol     token short symbol, 1-6 characters
        @param _decimals   for display purposes only
    */
    function SmartToken(string _name, string _symbol, uint8 _decimals)
        ERC20Token(_name, _symbol, _decimals)
    {
        require(bytes(_symbol).length <= 6); // validate input
        NewSmartToken(address(this));
    }

    // allows execution only when transfers aren't disabled
    modifier transfersAllowed {
        assert(transfersEnabled);
        _;
    }

    /**
        @dev disables/enables transfers
        can only be called by the contract owner

        @param _disable    true to disable transfers, false to enable them
    */
    function disableTransfers(bool _disable) public ownerOnly {
        transfersEnabled = !_disable;
    }

    /**
        @dev increases the token supply and sends the new tokens to an account
        can only be called by the contract owner

        @param _to         account to receive the new amount
        @param _amount     amount to increase the supply by
    */
    function issue(address _to, uint256 _amount)
        public
        ownerOnly
        validAddress(_to)
        notThis(_to)
    {
        totalSupply = safeAdd(totalSupply, _amount);
        balanceOf[_to] = safeAdd(balanceOf[_to], _amount);

        Issuance(_amount);
        Transfer(this, _to, _amount);
    }

    /**
        @dev removes tokens from an account and decreases the token supply
        can only be called by the contract owner

        @param _from       account to remove the amount from
        @param _amount     amount to decrease the supply by
    */
    function destroy(address _from, uint256 _amount)
        public
        ownerOnly
    {
        balanceOf[_from] = safeSub(balanceOf[_from], _amount);
        totalSupply = safeSub(totalSupply, _amount);

        Transfer(_from, this, _amount);
        Destruction(_amount);
    }

    // ERC20 standard method overrides with some extra functionality

    /**
        @dev send coins
        throws on any error rather then return a false flag to minimize user errors
        note that when transferring to the smart token's address, the coins are actually destroyed

        @param _to      target address
        @param _value   transfer amount

        @return true if the transfer was successful, false if it wasn't
    */
    function transfer(address _to, uint256 _value) public transfersAllowed returns (bool success) {
        assert(super.transfer(_to, _value));

        // transferring to the contract address destroys tokens
        if (_to == address(this)) {
            balanceOf[_to] -= _value;
            totalSupply -= _value;
            Destruction(_value);
        }

        return true;
    }

    /**
        @dev an account/contract attempts to get the coins
        throws on any error rather then return a false flag to minimize user errors
        note that when transferring to the smart token's address, the coins are actually destroyed

        @param _from    source address
        @param _to      target address
        @param _value   transfer amount

        @return true if the transfer was successful, false if it wasn't
    */
    function transferFrom(address _from, address _to, uint256 _value) public transfersAllowed returns (bool success) {
        assert(super.transferFrom(_from, _to, _value));

        // transferring to the contract address destroys tokens
        if (_to == address(this)) {
            balanceOf[_to] -= _value;
            totalSupply -= _value;
            Destruction(_value);
        }

        return true;
    }
}

/// @title Ownable
/// @dev The Ownable contract has an owner address, and provides basic authorization control functions, this simplifies
/// & the implementation of "user permissions".
contract Ownable {
    address public owner;
    address public newOwnerCandidate;

    event OwnershipRequested(address indexed _by, address indexed _to);
    event OwnershipTransferred(address indexed _from, address indexed _to);

    /// @dev The Ownable constructor sets the original `owner` of the contract to the sender account.
    function Ownable() {
        owner = msg.sender;
    }

    /// @dev Throws if called by any account other than the owner.
    modifier onlyOwner() {
        if (msg.sender != owner) {
            throw;
        }

        _;
    }

    /// @dev Proposes to transfer control of the contract to a newOwnerCandidate.
    /// @param _newOwnerCandidate address The address to transfer ownership to.
    function transferOwnership(address _newOwnerCandidate) onlyOwner {
        require(_newOwnerCandidate != address(0));

        newOwnerCandidate = _newOwnerCandidate;

        OwnershipRequested(msg.sender, newOwnerCandidate);
    }

    /// @dev Accept ownership transfer. This method needs to be called by the perviously proposed owner.
    function acceptOwnership() {
        if (msg.sender == newOwnerCandidate) {
            owner = newOwnerCandidate;
            newOwnerCandidate = address(0);

            OwnershipTransferred(owner, newOwnerCandidate);
        }
    }
}

/// @title Math operations with safety checks
library SaferMath {
    function mul(uint256 a, uint256 b) internal returns (uint256) {
        uint256 c = a * b;
        assert(a == 0 || c / a == b);
        return c;
    }

    function div(uint256 a, uint256 b) internal returns (uint256) {
        // assert(b > 0); // Solidity automatically throws when dividing by 0
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold
        return c;
    }

    function sub(uint256 a, uint256 b) internal returns (uint256) {
        assert(b <= a);
        return a - b;
    }

    function add(uint256 a, uint256 b) internal returns (uint256) {
        uint256 c = a + b;
        assert(c >= a);
        return c;
    }

    function max64(uint64 a, uint64 b) internal constant returns (uint64) {
        return a >= b ? a : b;
    }

    function min64(uint64 a, uint64 b) internal constant returns (uint64) {
        return a < b ? a : b;
    }

    function max256(uint256 a, uint256 b) internal constant returns (uint256) {
        return a >= b ? a : b;
    }

    function min256(uint256 a, uint256 b) internal constant returns (uint256) {
        return a < b ? a : b;
    }
}


/// @title Stox Smart Token
contract StoxSmartToken is SmartToken {
    function StoxSmartToken() SmartToken('Stox', 'STX', 18) {
        disableTransfers(true);
    }
}


/// @title Vesting trustee
contract Trustee is Ownable {
    using SaferMath for uint256;

    // The address of the STX ERC20 token.
    StoxSmartToken public stox;

    struct Grant {
        uint256 value;
        uint256 start;
        uint256 cliff;
        uint256 end;
        uint256 transferred;
        bool revokable;
    }

    // Grants holder.
    mapping (address => Grant) public grants;

    // Total tokens available for vesting.
    uint256 public totalVesting;

    event NewGrant(address indexed _from, address indexed _to, uint256 _value);
    event UnlockGrant(address indexed _holder, uint256 _value);
    event RevokeGrant(address indexed _holder, uint256 _refund);

    /// @dev Constructor that initializes the address of the StoxSmartToken contract.
    /// @param _stox StoxSmartToken The address of the previously deployed StoxSmartToken smart contract.
    function Trustee(StoxSmartToken _stox) {
        require(_stox != address(0));

        stox = _stox;
    }

    /// @dev Grant tokens to a specified address.
    /// @param _to address The address to grant tokens to.
    /// @param _value uint256 The amount of tokens to be granted.
    /// @param _start uint256 The beginning of the vesting period.
    /// @param _cliff uint256 Duration of the cliff period.
    /// @param _end uint256 The end of the vesting period.
    /// @param _revokable bool Whether the grant is revokable or not.
    function grant(address _to, uint256 _value, uint256 _start, uint256 _cliff, uint256 _end, bool _revokable)
        public onlyOwner {
        require(_to != address(0));
        require(_value > 0);

        // Make sure that a single address can be granted tokens only once.
        require(grants[_to].value == 0);

        // Check for date inconsistencies that may cause unexpected behavior.
        require(_start <= _cliff && _cliff <= _end);

        // Check that this grant doesn't exceed the total amount of tokens currently available for vesting.
        require(totalVesting.add(_value) <= stox.balanceOf(address(this)));

        // Assign a new grant.
        grants[_to] = Grant({
            value: _value,
            start: _start,
            cliff: _cliff,
            end: _end,
            transferred: 0,
            revokable: _revokable
        });

        // Tokens granted, reduce the total amount available for vesting.
        totalVesting = totalVesting.add(_value);

        NewGrant(msg.sender, _to, _value);
    }

    /// @dev Revoke the grant of tokens of a specifed address.
    /// @param _holder The address which will have its tokens revoked.
    function revoke(address _holder) public onlyOwner {
        Grant grant = grants[_holder];

        require(grant.revokable);

        // Send the remaining STX back to the owner.
        uint256 refund = grant.value.sub(grant.transferred);

        // Remove the grant.
        delete grants[_holder];

        totalVesting = totalVesting.sub(refund);
        stox.transfer(msg.sender, refund);

        RevokeGrant(_holder, refund);
    }

    /// @dev Calculate the total amount of vested tokens of a holder at a given time.
    /// @param _holder address The address of the holder.
    /// @param _time uint256 The specific time.
    /// @return a uint256 representing a holder's total amount of vested tokens.
    function vestedTokens(address _holder, uint256 _time) public constant returns (uint256) {
        Grant grant = grants[_holder];
        if (grant.value == 0) {
            return 0;
        }

        return calculateVestedTokens(grant, _time);
    }

    /// @dev Calculate amount of vested tokens at a specifc time.
    /// @param _grant Grant The vesting grant.
    /// @param _time uint256 The time to be checked
    /// @return An uint256 representing the amount of vested tokens of a specific grant.
    ///   |                         _/--------   vestedTokens rect
    ///   |                       _/
    ///   |                     _/
    ///   |                   _/
    ///   |                 _/
    ///   |                /
    ///   |              .|
    ///   |            .  |
    ///   |          .    |
    ///   |        .      |
    ///   |      .        |
    ///   |    .          |
    ///   +===+===========+---------+----------> time
    ///     Start       Cliff      End
    function calculateVestedTokens(Grant _grant, uint256 _time) private constant returns (uint256) {
        // If we're before the cliff, then nothing is vested.
        if (_time < _grant.cliff) {
            return 0;
        }

        // If we're after the end of the vesting period - everything is vested;
        if (_time >= _grant.end) {
            return _grant.value;
        }

        // Interpolate all vested tokens: vestedTokens = tokens/// (time - start) / (end - start)
         return _grant.value.mul(_time.sub(_grant.start)).div(_grant.end.sub(_grant.start));
    }

    /// @dev Unlock vested tokens and transfer them to their holder.
    /// @return a uint256 representing the amount of vested tokens transferred to their holder.
    function unlockVestedTokens() public {
        Grant grant = grants[msg.sender];
        require(grant.value != 0);

        // Get the total amount of vested tokens, acccording to grant.
        uint256 vested = calculateVestedTokens(grant, now);
        if (vested == 0) {
            return;
        }

        // Make sure the holder doesn't transfer more than what he already has.
        uint256 transferable = vested.sub(grant.transferred);
        if (transferable == 0) {
            return;
        }

        grant.transferred = grant.transferred.add(transferable);
        totalVesting = totalVesting.sub(transferable);
        stox.transfer(msg.sender, transferable);

        UnlockGrant(msg.sender, transferable);
    }
}


/// @title Stox Smart Token sale
contract StoxSmartTokenSale is Ownable {
    using SaferMath for uint256;

    uint256 public constant DURATION = 14 days;

    bool public isFinalized = false;
    bool public isDistributed = false;

    // The address of the STX ERC20 token.
    StoxSmartToken public stox;

    // The address of the token allocation trustee;
    Trustee public trustee;

    uint256 public startTime = 0;
    uint256 public endTime = 0;
    address public fundingRecipient;

    uint256 public tokensSold = 0;

    // TODO: update to the correct values.
    uint256 public constant ETH_CAP = 148000;
    uint256 public constant EXCHANGE_RATE = 200; // 200 STX for ETH
    uint256 public constant TOKEN_SALE_CAP = ETH_CAP * EXCHANGE_RATE * 10 ** 18;

    event TokensIssued(address indexed _to, uint256 _tokens);

    /// @dev Throws if called when not during sale.
    modifier onlyDuringSale() {
        if (tokensSold >= TOKEN_SALE_CAP || now < startTime || now >= endTime) {
            throw;
        }

        _;
    }

    /// @dev Throws if called before sale ends.
    modifier onlyAfterSale() {
        if (!(tokensSold >= TOKEN_SALE_CAP || now >= endTime)) {
            throw;
        }

        _;
    }

    /// @dev Constructor that initializes the sale conditions.
    /// @param _fundingRecipient address The address of the funding recipient.
    /// @param _startTime uint256 The start time of the token sale.
    function StoxSmartTokenSale(address _stox, address _fundingRecipient, uint256 _startTime) {
        require(_stox != address(0));
        require(_fundingRecipient != address(0));
        require(_startTime > now);

        stox = StoxSmartToken(_stox);

        fundingRecipient = _fundingRecipient;
        startTime = _startTime;
        endTime = startTime + DURATION;
    }

    /// @dev Distributed tokens to the partners who have participated during the pre-sale.
    function distributePartnerTokens() external onlyOwner {
        require(!isDistributed);

        assert(tokensSold == 0);
        assert(stox.totalSupply() == 0);

        // Distribute strategic tokens to partners. Please note, that this address doesn't represent a single entity or
        // person and will be only used to distribute tokens to 30~ partners.
        //
        // Please expect to see token transfers from this address in the first 24 hours after the token sale ends.
        issueTokens(0x9065260ef6830f6372F1Bde408DeC57Fe3150530, 14800000 * 10 ** 18);

        isDistributed = true;
    }

    /// @dev Finalizes the token sale event.
    function finalize() external onlyAfterSale {
        if (isFinalized) {
            throw;
        }

        // Grant vesting grants.
        //
        // TODO: use real addresses.
        trustee = new Trustee(stox);

        // Since only 50% of the tokens will be sold, we will automatically issue the same amount of sold STX to the
        // trustee.
        uint256 unsoldTokens = tokensSold;

        // Issue 55% of the remaining tokens (== 27.5%) go to strategic parternships.
        uint256 strategicPartnershipTokens = unsoldTokens.mul(55).div(100);

        // Note: we will substract the bonus tokens from this grant, since they were already issued for the pre-sale
        // strategic partners and should've been taken from this allocation.
        stox.issue(0xbC14105ccDdeAadB96Ba8dCE18b40C45b6bACf58, strategicPartnershipTokens);

        // Issue the remaining tokens as vesting grants:
        stox.issue(trustee, unsoldTokens.sub(strategicPartnershipTokens));

        // 25% of the remaining tokens (== 12.5%) go to Invest.com, at uniform 12 months vesting schedule.
        trustee.grant(0xb54c6a870d4aD65e23d471Fb7941aD271D323f5E, unsoldTokens.mul(25).div(100), now, now,
            now.add(1 years), true);

        // 20% of the remaining tokens (== 10%) go to Stox team, at uniform 24 months vesting schedule.
        trustee.grant(0x4eB4Cd1D125d9d281709Ff38d65b99a6927b46c1, unsoldTokens.mul(20).div(100), now, now,
            now.add(2 years), true);

        // Re-enable transfers after the token sale.
        stox.disableTransfers(false);

        isFinalized = true;
    }

    /// @dev Create and sell tokens to the caller.
    /// @param _recipient address The address of the recipient.
    function create(address _recipient) public payable onlyDuringSale {
        require(_recipient != address(0));
        require(msg.value > 0);

        assert(isDistributed);

        uint256 tokens = SaferMath.min256(msg.value.mul(EXCHANGE_RATE), TOKEN_SALE_CAP.sub(tokensSold));
        uint256 contribution = tokens.div(EXCHANGE_RATE);

        issueTokens(_recipient, tokens);

        // Transfer the funds to the funding recipient.
        fundingRecipient.transfer(contribution);

        // Refund the msg.sender, in the case that not all of its ETH was used. This can happen only when selling the
        // last chunk of STX.
        uint256 refund = msg.value.sub(contribution);
        if (refund > 0) {
            msg.sender.transfer(refund);
        }
    }

    /// @dev Issues tokens for the recipient.
    /// @param _recipient address The address of the recipient.
    /// @param _tokens uint256 The amount of tokens to issue.
    function issueTokens(address _recipient, uint256 _tokens) private {
        // Update total sold tokens.
        tokensSold = tokensSold.add(_tokens);

        stox.issue(_recipient, _tokens);

        TokensIssued(_recipient, _tokens);
    }

    /// @dev Fallback function that will delegate the request to create.
    function () external payable onlyDuringSale {
        create(msg.sender);
    }

    /// @dev Proposes to transfer control of the StoxSmartToken contract to a new owner.
    /// @param _newOwnerCandidate address The address to transfer ownership to.
    ///
    /// Note that:
    ///   1. The new owner will need to call StoxSmartToken's acceptOwnership directly in order to accept the ownership.
    ///   2. Calling this method during the token sale will prevent the token sale to continue, since only the owner of
    ///      the StoxSmartToken contract can issue new tokens.
    function transferSmartTokenOwnership(address _newOwnerCandidate) external onlyOwner {
        stox.transferOwnership(_newOwnerCandidate);
    }

    /// @dev Accepts new ownership on behalf of the StoxSmartToken contract. This can be used, by the token sale
    /// contract itself to claim back ownership of the StoxSmartToken contract.
    function acceptSmartTokenOwnership() external onlyOwner {
        stox.acceptOwnership();
    }

    /// @dev Proposes to transfer control of the Trustee contract to a new owner.
    /// @param _newOwnerCandidate address The address to transfer ownership to.
    ///
    /// Note that:
    ///   1. The new owner will need to call Trustee's acceptOwnership directly in order to accept the ownership.
    ///   2. Calling this method during the token sale won't be possible, as the Trustee is only created after its
    ///      finalization.
    function transferTrusteeOwnership(address _newOwnerCandidate) external onlyOwner {
        trustee.transferOwnership(_newOwnerCandidate);
    }

    /// @dev Accepts new ownership on behalf of the Trustee contract. This can be used, by the token sale
    /// contract itself to claim back ownership of the Trustee contract.
    function acceptTrusteeOwnership() external onlyOwner {
        trustee.acceptOwnership();
    }
}