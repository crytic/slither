contract Contract{

    uint a;

    function write(){
        a++;
    }

    // shadowing of a
    function dont_write(uint a){
        a = a +1;
    }

}
