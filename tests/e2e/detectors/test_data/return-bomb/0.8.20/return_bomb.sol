contract BadGuy {
    function llbad() external pure returns (bytes memory) {
        assembly{
            revert(0, 1000000)
        }
    }

    function fgood() external payable returns (uint){
        assembly{
            return(0, 1000000)
        }
    }

    function fbad() external payable returns (uint[] memory){
        assembly{
            return(0, 1000000)
        }
    }

    function fbad1() external payable returns (uint, string memory){
        assembly{
            return(0, 1000000)
        }
    }


}

contract Mark {

    function oops(address badGuy) public{
        bool success;
        string memory str;
        bytes memory ret;
        uint x;
        uint[] memory ret1;

	x = BadGuy(badGuy).fgood{gas:2000}();

	ret1 = BadGuy(badGuy).fbad(); //good (no gas specified)

	ret1 = BadGuy(badGuy).fbad{gas:2000}();

	(x, str) = BadGuy(badGuy).fbad1{gas:2000}();

        // Mark pays a lot of gas for this copy 😬😬😬
        (success, ret) = badGuy.call{gas:10000}(
            abi.encodeWithSelector(
                BadGuy.llbad.selector
            )
        );

        // Mark may OOG here, preventing local state changes
        //importantCleanup();
    }
}

