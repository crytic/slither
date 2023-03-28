interface I{
    function external_call() external;
}

contract ReentrancyAndWrite{

    /// @custom:security non-reentrant
    /// @custom:security write-protection="onlyOwner()"
    I external_contract;

    modifier onlyOwner(){
        // lets assume there is an access control
        _;
    }

    mapping(address => uint) balances;

    function withdraw() public{
        uint balance = balances[msg.sender];

        external_contract.external_call();

        balances[msg.sender] = 0;
        payable(msg.sender).transfer(balance);
    }

    function set_protected() public onlyOwner(){
        external_contract = I(msg.sender);
    }

    function set_not_protected() public{
        external_contract = I(msg.sender);
    }
}

contract Internal {
    /// @custom:security write-protection="onlyOwner()"
    address owner;



    modifier onlyOwner(){
        // lets assume there is an access control
        _;
    }

    function buggy() public {
        internal_write();
    }

    function internal_write() internal {
        owner = msg.sender;
    }
}