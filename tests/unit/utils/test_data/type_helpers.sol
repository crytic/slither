contract A{

    struct St{
        St[] a;
        uint b;
    }

    function f(St memory s) internal{
	f(s);
    }

}
