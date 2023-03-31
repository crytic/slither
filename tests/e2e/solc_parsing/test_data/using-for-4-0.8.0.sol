using {f} for St;
struct St { uint field; }


function f(St storage self, uint8 v) view returns(uint){
    return 0;
}


library Lib {
    function f(St storage self, uint256 v) public view returns (uint) {
        return 1;
    }

}

contract C {
    using Lib for St;
    St st;

    function libCall(uint16 v) public view returns(uint){
        return st.f(v); // return 1
    }

}