contract ERC20 {
    function balanceOf(address) public view returns (uint) {
        return 0;
    }
}

contract C {
    function tryCatchFunctionCall() public {
        uint actualBalance;

        try ERC20(msg.sender).balanceOf(address(this)) returns (uint balance) {
            actualBalance = balance;
        } catch Error(string memory err) {
            revert(err);
        }

        try ERC20(msg.sender).balanceOf(address(this)) returns (uint balance) {
            actualBalance = balance;
        } catch (bytes memory err) {
            revert(string(err));
        }

        try ERC20(msg.sender).balanceOf(address(this)) returns (uint balance) {
            actualBalance = balance;
        } catch Error(string memory err) {
            revert(err);
        } catch (bytes memory err) {
            revert(string(err));
        }

        try ERC20(msg.sender).balanceOf(address(this)) returns (uint) {
        } catch {
            actualBalance = 0;
        }

        try ERC20(msg.sender).balanceOf(address(this)) returns (uint balance) {
            uint c;
            for (uint i; i < balance; i++) {
                c++;
            }
        } catch {
        }
    }

    function tryCatchContractDeployment() public {
        try new ERC20() returns (ERC20 deployed) {
            try deployed.balanceOf(address(this)) returns (uint) {

            } catch {

            }
        } catch {

        }
    }
}