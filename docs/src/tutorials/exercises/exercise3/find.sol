contract Find {
    uint my_variable;

    function condition() public {
        if (my_variable == 0) {}
    }

    function call_require() public {
        require(my_variable == 0);
    }

    function read_and_write() public {
        my_variable = my_variable + 1;
    }
}
