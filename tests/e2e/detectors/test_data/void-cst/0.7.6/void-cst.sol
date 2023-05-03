

contract C{


}

contract D is C{

    constructor() public C(){
        uint i = 1;
    }

}
