// Source: https://github.com/crytic/slither/blame/ab6939c2c851e4a0122f131df56d87d11f5df43f/tests/e2e/detectors/test_data/ecrecover/0.8.0/ecrecover.sol
// Author: tuturu-tech - https://github.com/tuturu-tech
// Added ECDSA check, reference: https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/ECDSA.sol

pragma solidity ^0.8.18;

contract A {
    struct Info {
        uint tokenId;
        address owner;
        
        // uint nonce
    }
    uint maxBreed = 5;
    uint chainId;
    mapping(uint => mapping(uint => address)) list;
    mapping(uint => uint) count;
    mapping(address => uint256) nonces;

    function mint(uint tokenId, address addr) internal {
        require(count[tokenId] < maxBreed, "");
        list[tokenId][count[tokenId]] = addr;
        count[tokenId]++;
    }

    //With Chain ID and No ECDSA singature validation
    function bad_withChainID_missingECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info,chainId));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash, chainId)
        );
        address receiver = ecrecover(data, v, r, s);
        mint(info.tokenId, receiver);
    }

    //Missing Chain ID or Nonce and valid ECDSA signature validation
    function bad_missingChainId_missingNonce_withECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 data = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(info))
            )
        );
        if((r>0 && 
        uint256(s) <= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0  
        && s>0 && (v==0 || v==1))){
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
        }
    }

    //Missing Chain ID and No ECDSA singature validation
    function bad_missingChainID_missingECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info,chainId));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
        );
        address receiver = ecrecover(data, v, r, s);
        mint(info.tokenId, receiver);
    }


    //Missing Chain ID or Nonce and invalid ECDSA singature validation
    function bad_missingChainId_missingNonce_invalidECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 data = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(info))
            )
        );
        if((r > bytes32(uint256(2)) && s>0 && (v == 0 || v == 1))){
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
        }
    }

    //Missing Chain ID or Nonce and no ECDSA singature validation
    function bad_missingChainId_missingNonce_missingECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 data = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(info))
            )
        );
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
       
    }

    //Valid with Chain Id and ECDSA singature validation
    function good_withChainId_withECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info,chainId));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash, chainId)
        );
        if((r > 0 && uint256(s) <= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0 && 
        s>0 && (v == 0 || v == 1))){
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
        }
    }
    //Valid with Nonce and ECDSA singature validation
    function good_withNonce_withECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info,nonces[msg.sender]++));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash, nonces[msg.sender]++)
        );
        if((r > 0 && s>0 && 
        uint256(s) <= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0 && 
        (v == 0 || v == 1))){
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
        }
    }

    //Valid Nonce and  missing ECDSA singature validation
    function bad_withNonce_missingECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 data = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(info,nonces[msg.sender]++))
            )
        );
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
       
    }

    //Valid Chain Id and  missing ECDSA singature validation
    function bad_withChainId_missingECDSACheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 data = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(info,chainId))
            )
        );
            address receiver = ecrecover(data, v, r, s);
            require(receiver != address(0), "ECDSA: invalid signature");
            mint(info.tokenId, receiver);
    
    }

    // function bad_noSignerCheck_withNonce(
    //     Info calldata info,
    //     uint8 v,
    //     bytes32 r,
    //     bytes32 s
    // ) external {
    //     bytes32 hash = keccak256(abi.encode(info, nonces[msg.sender]++));
    //     bytes32 data = keccak256(
    //         abi.encodePacked("\x19Ethereum Signed Message:\n32", hash, chainId)
    //     );
    //     address receiver = ecrecover(data, v, r, s);
    //     mint(info.tokenId, receiver);
    // }

    // function bad_withRequire_noNonce(
    //     Info calldata info,
    //     uint8 v,
    //     bytes32 r,
    //     bytes32 s
    // ) external {
    //     bytes32 hash = keccak256(abi.encode(info));
    //     bytes32 data = keccak256(
    //         abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
    //     );
    //     address receiver = ecrecover(data, v, r, s);
    //     require(receiver != address(0), "ECDSA: invalid signature");
    //     mint(info.tokenId, receiver);
    // }

    // function bad_withIF_noNonce(
    //     Info calldata info,
    //     uint8 v,
    //     bytes32 r,
    //     bytes32 s
    // ) external {
    //     bytes32 hash = keccak256(abi.encode(info));
    //     bytes32 data = keccak256(
    //         abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
    //     );
    //     address receiver = ecrecover(data, v, r, s);
    //     if (receiver == address(0)) revert();
    //     mint(info.tokenId, receiver);
    // }
}
