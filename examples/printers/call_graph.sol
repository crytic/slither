contract ContractA {
    function my_func_a() {
        keccak256(0);
    }
}

contract ContractB {
    ContractA a;

    constructor() {
        a = new ContractA();
    }

    function my_func_b() {
        a.my_func_a();
        my_second_func_b();
    }

    function my_func_a() {
        my_second_func_b();
    }

    function my_second_func_b(){
    }
}