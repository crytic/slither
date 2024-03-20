import {MyContract as MyAliasedContract} from "./MyContract.sol";

contract Test {
MyAliasedContract c;
    constructor() {
        c = new MyAliasedContract();
    }
} 
