pragma solidity ^0.8.0;
contract my_contract {
    function empty_func() external pure
    {
        // The string below contains 3 RLO and 3 PDF unicode characters
        // RLO is U+202E and changes the print direction to right-to-left
        // PDF is U+202C and restores the print direction to what it was before RLO
        /*ok ‮aaa‮bbb‮ccc‬ddd‬eee‬*/
    }
}
// ----