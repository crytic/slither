import "./l1.sol" as R;
pragma abicoder v2;
contract Tp {

    function re(R.SS calldata param1, R.MyEnum param2) public {
        R.MyEnum a = R.MyEnum.A;
        R.SS memory b = R.SS(R.qwe);
        R.MyC.callme();
        R.tpf(2, param1);
        R.tpf(param2);
        R.L2.l();
    }



} 