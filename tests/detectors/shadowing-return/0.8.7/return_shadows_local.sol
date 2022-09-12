pragma solidity 0.8.7;

contract Shadowed {

    function shadowed0() external view returns(uint shadowed_var) {
        uint shadowed_var = 1;
    } //returns: 0 (instead of 1)

    function shadowed1() external view returns(uint shadowed_var1, uint shadowed_var2) {
        uint shadowed_var1 = 1;
        shadowed_var2 = 2;
    } //returns: 0, 2 (instead of 1, 2)

    function shadowed2() external view returns(uint shadowed_var1, uint shadowed_var2) {
        shadowed_var1 = 1;
        uint shadowed_var2 = 2;
    } //returns: 1, 0 (instead of 1, 2)

    function shadowed3() external view returns(uint shadowed_var1, uint shadowed_var2) {
        return this.shadowed2();
    } //returns: 1, 0 (instead of 1, 2)
}

contract Unnamed {

    function unnamed0() external view returns(uint) {
        uint unnamed_var = 1;
    } //returns: 0 (instead of 1)

    function unnamed1() external view returns(uint, uint unnamed_var2) {
        uint unnamed_var1 = 1;
        unnamed_var2 = 2;
    } //returns: 0, 2 (instead of 1, 2)

    function unnamed2() external view returns(uint unnamed_var1, uint) {
        unnamed_var1 = 1;
        uint unnamed_var2 = 2;
    } //returns: 1, 0 (instead of 1, 2)

    function unnamed3() external view returns(uint unnamed_var2, uint unnamed_var1) {
        return this.unnamed2();
    } //returns: 1, 0 (instead of 1, 2)
}

contract ReturnShadowsLocal is Shadowed, Unnamed {
}

/* !note Tested to not throw errors correct contracts on OpenZeppelin contracts */

// contract CaseExamples {
//     function correct0() external view returns(uint value) {
//         value = 1;
//     } //returns: 1

//     function correct1() external view returns(uint value1, uint value2) {
//         value1 = 1;
//         value2 = 2;
//     } //returns: 1, 2

//     function correct2() external view returns(uint value) {
//         uint value1;
//         value = 1;
//     } //returns: 1

//     function correct3() external view returns(uint value) {
//         value=1;
//         uint value1;
//     } //returns: 1

//     function correct4() external view returns(uint value) {
//         uint value1;
//         value=1;
//         uint value2;
//     } //returns: 1

//     function correct5() external view returns(uint) {
//         return 1;
//     } //returns: 1

//     function correct6() external view returns(uint) {
//         uint value;
//         value = 1;
//         return value;
//     }//returns: 1

//     function correct7() external view returns(uint, uint) {
//         return this.correct1();
//     }  //returns: 1, 2
// }