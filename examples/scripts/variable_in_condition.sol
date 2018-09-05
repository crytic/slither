contract Contract{

    uint a;

    function condition(){
        if(a==0){

        }
    }

    function call_require(){
        require(a==0);
    }
    
    function read_and_write(){
        a = a + 1;
    }

}
