import "./l1.sol" as R;

contract Tp {

    function re(R.SS calldata param1, R.MyEnum param2) public {
        R.MyEnum a = R.MyEnum.A;
        R.SS memory b = R.SS(R.qwe);
        R.MyC.callme();
        R.tpf(2, param1);
        R.tpf(param2);
        R.tpf(R.fd.wrap(4));
        R.L2.l();
        revert R.MyImportError();
    }

    function re2() public {
        revert R.MyError();
    }

} 