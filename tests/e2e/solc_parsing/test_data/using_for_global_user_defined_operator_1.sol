
import {BalanceDelta} from "./using_for_global_user_defined_operator.sol";
contract X {

   function get(BalanceDelta delta) external {
        int128 amount0 = delta.amount0();
        int128 amount1 = delta.amount1();
    }
}   