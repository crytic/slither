// This tests against false-positives. This test should output no recommendations from the external-function detector.


abstract contract ContractWithBaseFunctionCalled {
    function getsCalledByBase() public virtual;
    function callsOverrideMe() external {
        getsCalledByBase();
    }
}


contract DerivingContractWithBaseCalled is ContractWithBaseFunctionCalled {
    function getsCalledByBase() public override {
        // This should not be recommended to be marked external because it is called by the base class.
    }
}


// All the contracts below should not recommend changing to external since inherited contracts have dynamic calls.
contract ContractWithDynamicCall {
    function() returns(uint) ptr;

    function test1() public returns(uint){
        return 1;
    }

    function test2() public returns(uint){
        return 2;
    }

    function setTest1() external{
        ptr = test1;
    }

    function setTest2() external{
        ptr = test2;
    }

    function exec() external returns(uint){
        return ptr();
    }
}

contract DerivesFromDynamicCall is ContractWithDynamicCall{
    function getsCalledDynamically() public returns (uint){
        // This should not be recommended because it is called dynamically.
        return 3;
    }
    function setTest3() public {
        // This should not be recommended because we inherit from a contract that calls dynamically, and we cannot be
        // sure it did not somehow call this function.

        ptr = getsCalledDynamically;
    }
}
