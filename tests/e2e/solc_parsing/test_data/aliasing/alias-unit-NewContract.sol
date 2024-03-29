
import "./MyContract.sol" as MyAliasedContract;

contract Test {
MyAliasedContract.MyContract c;
    constructor() {
        c = new MyAliasedContract.MyContract();
    }
} 