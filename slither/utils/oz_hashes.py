from typing import NamedTuple, List


class LibraryInfo(NamedTuple):
    name: str
    versons: List[str]


# pylint: disable=too-many-lines
oz_hashes = {
    "16ad4eed535bc7e7ea4d1096618d68ffe5a02287": LibraryInfo("Bounty", ["v1.3.0"]),
    "896a88e86ba21fe176d5e3de434af62ee531b1d5": LibraryInfo(
        "Target", ["v1.3.0", "v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "ab36e566a3daf2aa0a8e129c150ed868a4902891": LibraryInfo("DayLimit", ["v1.3.0"]),
    "07684a10bdf44d974020a0370e5ed7afbe1f9e44": LibraryInfo("ECRecovery", ["v1.3.0"]),
    "0df8b61d53724353dff7ceb4948f99f4d5d0a558": LibraryInfo("LimitBalance", ["v1.3.0"]),
    "a034f5999f05402616da9a54ed665d6196c6adee": LibraryInfo("MerkleProof", ["v1.3.0"]),
    "7e2f3e9543ef140fb05e6cd5b67ee85f9e5c89e8": LibraryInfo("ReentrancyGuard", ["v1.3.0"]),
    "1b983aa0e808ccb541f22f643011ee24e9eddc1e": LibraryInfo("CappedCrowdsale", ["v1.3.0"]),
    "f48c976b3a18769596a181adc072c3266a232166": LibraryInfo("Crowdsale", ["v1.3.0"]),
    "fc085749b4f49f6999c5cccd50c6a8b567b0ed5d": LibraryInfo("FinalizableCrowdsale", ["v1.3.0"]),
    "2190fe74b4df2a58266ce573a1c09a047fec8b68": LibraryInfo("RefundVault", ["v1.3.0"]),
    "06c26f4535dea69cdec2cf94d31f3a542430f692": LibraryInfo("RefundableCrowdsale", ["v1.3.0"]),
    "e2e8a667511fa076aa2f4721a7b0476ded68f179": LibraryInfo(
        "SampleCrowdsaleToken", ["v1.3.0", "v1.12.0"]
    ),
    "618409ffc0166d51eae7474a0e65db339c1a1a48": LibraryInfo("SampleCrowdsale", ["v1.3.0"]),
    "4893616c2a59bcc5b391a85598145327f6c9b481": LibraryInfo("SimpleToken", ["v1.3.0"]),
    "78d8f11bc1dd500ef6aa3bf95b516facd34ae97f": LibraryInfo("Destructible", ["v1.3.0"]),
    "7c2320f840fb8175ef0338f82488b437bccb3a2d": LibraryInfo("Migrations", ["v1.3.0"]),
    "20954e05e6a84d9d349f36b720d20057a5849126": LibraryInfo("Pausable", ["v1.3.0"]),
    "98656c8719e36d1e018b5e7d907f84531d0cde71": LibraryInfo("TokenDestructible", ["v1.3.0"]),
    "77c201c932c5fd7a11e30bb970afda5a5c1a0e6c": LibraryInfo("Math", ["v1.3.0"]),
    "dcd94e653605571a4adaef30328837552088af90": LibraryInfo("SafeMath", ["v1.3.0"]),
    "e102f7570918afe9b8a712ec7b8cf2ce2d7ccf06": LibraryInfo(
        "CanReclaimToken", ["v1.3.0", "v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "18816a398c07b658ed4f84871d8afa1132ff2ea9": LibraryInfo("Claimable", ["v1.3.0"]),
    "a51d83ec668c67ee7e3cb6744f207d7fba110ad8": LibraryInfo("Contactable", ["v1.3.0"]),
    "ef49ebbffe424c8b829cf8d8fe07b0bdd4b6a32a": LibraryInfo("DelayedClaimable", ["v1.3.0"]),
    "295a28a0cc845f398fd3f73fe7d7ebd3f217efb5": LibraryInfo(
        "HasNoContracts", ["v1.3.0", "v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "0695e926e394b778337e14f8bbbdce3aee6756c9": LibraryInfo("HasNoEther", ["v1.3.0"]),
    "e0d144a37d99136b64edec4bc0a7d5f003ca4eb5": LibraryInfo("HasNoTokens", ["v1.3.0"]),
    "70334d1b91d44591475891c4a1462711d37a8990": LibraryInfo(
        "NoOwner", ["v1.3.0", "v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "4bafe87e87f2f7924cebc0f210ffc504f62479ea": LibraryInfo("Ownable", ["v1.3.0"]),
    "9f8caf856608726e48ee86370d866088590bf374": LibraryInfo("PullPayment", ["v1.3.0"]),
    "a586769701d35125a8281597f0187c12eebf45d8": LibraryInfo("BasicToken", ["v1.3.0"]),
    "1938eb4e2cdedd786c42fbace059fbe4591a3c11": LibraryInfo("BurnableToken", ["v1.3.0"]),
    "7d6c8036444ef12c4293c12f6dac7ea09b009ccd": LibraryInfo("ERC20", ["v1.3.0"]),
    "26cac836b179301d90c2fb814eda7f46c0a185ef": LibraryInfo("ERC20Basic", ["v1.3.0"]),
    "9414672a30d64bb82b495245b0dd47ef4f9f626c": LibraryInfo("LimitedTransferToken", ["v1.3.0"]),
    "0774060a7337641beb9a43a8c0bdcb1c3ae145bc": LibraryInfo("MintableToken", ["v1.3.0"]),
    "b3ce90caedd7821ec2a6f1bcbcda81637501d52b": LibraryInfo("PausableToken", ["v1.3.0", "v1.9.0"]),
    "3af6c4bebea1014a2a35abccc63a5fcba9be70ab": LibraryInfo("SafeERC20", ["v1.3.0"]),
    "cc3aea9e2f2110e02913b2ce811c9ed4beecf465": LibraryInfo("StandardToken", ["v1.3.0"]),
    "fa1616bdd4888c5d16500a3e407fa001ddd75df0": LibraryInfo("TokenTimelock", ["v1.3.0"]),
    "09c671cd62433379e237d2fc5dc311af49cf1f5c": LibraryInfo("VestedToken", ["v1.3.0"]),
    "7762232a812e8fa5f4cc1f41d0e8c647839bcf3f": LibraryInfo("AddressUtils", ["v1.9.0", "v1.9.1"]),
    "9adc4ade8a73cef7a0494e49b3195491f2567630": LibraryInfo("Bounty", ["v1.9.0", "v1.10.0"]),
    "dc527f7040995e42e07446f383fd40b293814e4c": LibraryInfo("DayLimit", ["v1.9.0"]),
    "91c4da8fd04d8dc4678a741b7a553a7fc47bfc0c": LibraryInfo(
        "ECRecovery", ["v1.9.0", "v1.9.1", "v1.10.0"]
    ),
    "e362496576b5ef824429b2aa0634a04e5e13864d": LibraryInfo("LimitBalance", ["v1.9.0"]),
    "d2ad47f4ddb62fb8bcb3f4add161aeb0f3f5a4be": LibraryInfo("MerkleProof", ["v1.9.0", "v1.9.1"]),
    "abe9489ed9de21737a43ab9698d131e7407620f6": LibraryInfo(
        "ReentrancyGuard", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "76fae86d089153d66e6e8402d43da9485c2113a8": LibraryInfo(
        "SignatureBouncer", ["v1.9.0", "v1.10.0"]
    ),
    "20c12a01e1c64fa836c2569bb44eb852d44c7c5c": LibraryInfo("Crowdsale", ["v1.9.0"]),
    "22465351d15ee5cd18d91ae8ab159129d4dcfb4d": LibraryInfo(
        "FinalizableCrowdsale", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "9774a38be6323299d069a8756b44179c880e7c1e": LibraryInfo("PostDeliveryCrowdsale", ["v1.9.0"]),
    "e933560cd155790112d5685ed76df0e235c780ea": LibraryInfo("RefundableCrowdsale", ["v1.9.0"]),
    "d7910b2369b470f77e0e14605a8b061d6e2bd46d": LibraryInfo("RefundVault", ["v1.9.0"]),
    "2661d9bc3203d658e7ed5d29a47fa66e0fdac5ba": LibraryInfo("AllowanceCrowdsale", ["v1.9.0"]),
    "eb321ffdfe7be1efaefc8bdd9e6acb46eca221f4": LibraryInfo("MintedCrowdsale", ["v1.9.0"]),
    "09016aac11d32d3fda430c154c180afb2fb7732d": LibraryInfo("IncreasingPriceCrowdsale", ["v1.9.0"]),
    "1ff28b511dec3f0515c96d659e10f6ef7c47ce0b": LibraryInfo("CappedCrowdsale", ["v1.9.0"]),
    "e789d95184e0adabe7b5b79510d3f32c9d882cd3": LibraryInfo(
        "IndividuallyCappedCrowdsale", ["v1.9.0"]
    ),
    "d062ebe0b22232bb1d8ac84cf09f10c3cbea5618": LibraryInfo("TimedCrowdsale", ["v1.9.0"]),
    "7d396a8c6ff432ad5e51697af40baa20dbe97603": LibraryInfo("WhitelistedCrowdsale", ["v1.9.0"]),
    "9e1ceee37e77060c7b13a87909cac0902e2ad81e": LibraryInfo("SampleCrowdsaleToken", ["v1.9.0"]),
    "b1a63d12b5f88f0b4d8d0283aabcb052b03b9a6f": LibraryInfo("SampleCrowdsale", ["v1.9.0"]),
    "4ffdf78526d08ef08faa67476631359f1f34d39c": LibraryInfo("SimpleSavingsWallet", ["v1.9.0"]),
    "848e77f0c272c709d7df601a0a7dff1be871aa47": LibraryInfo("SimpleToken", ["v1.9.0"]),
    "149e2bf2bf05ac0417a92de826b691e605375f87": LibraryInfo("Destructible", ["v1.9.0"]),
    "9ec21dbeba82d8ffbb547ec3efc63e946e403433": LibraryInfo(
        "Pausable", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "0636e347e26d51691bbe203f326ed3a81c14893b": LibraryInfo("TokenDestructible", ["v1.9.0"]),
    "8c43814c5d4144e7241ad3acf036831f72626f53": LibraryInfo(
        "Math", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0"]
    ),
    "dcb0461fc135342c8335ec971c0fce948749fcad": LibraryInfo("SafeMath", ["v1.9.0", "v1.9.1"]),
    "3c84335582613c4f61db5e2dba4a5bdf9a32647e": LibraryInfo("AllowanceCrowdsaleImpl", ["v1.9.0"]),
    "f27124a3561a89f719110813c710df74b8852455": LibraryInfo("BasicTokenMock", ["v1.9.0", "v1.9.1"]),
    "882c0e313871f9bdb3ade123cd21a06e80b9687b": LibraryInfo(
        "SignatureBouncerMock", ["v1.9.0", "v1.10.0"]
    ),
    "767d1b9bea360813c53f074339dab44dba2be3e1": LibraryInfo(
        "BurnableTokenMock", ["v1.9.0", "v1.9.1"]
    ),
    "c06b8492aa76d2b3e863e9cc21e56ea9220b6725": LibraryInfo("CappedCrowdsaleImpl", ["v1.9.0"]),
    "5e4b5478ed4656e3e83cae78eeddca3ffdc77ce7": LibraryInfo("DayLimitMock", ["v1.9.0"]),
    "c07480985ff1aef7516290b6e1c6eb0f5f428379": LibraryInfo("DetailedERC20Mock", ["v1.9.0"]),
    "01478e8bf733ffd6b1f847f5406b6225c8b02f1c": LibraryInfo(
        "ECRecoveryMock", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0"]
    ),
    "17b3d5a66300e613b33d994b29afae7826d66b15": LibraryInfo(
        "ERC223ContractInterface", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "02100ab471369f65ef7a811c4979da275426f021": LibraryInfo("ERC223TokenMock", ["v1.9.0"]),
    "ed7ae160a58372fd8f7fd58b4138ff029dd27df1": LibraryInfo(
        "ERC721BasicTokenMock", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "c6c6e961e36c39df202768b8fd18f1f76cefd1ff": LibraryInfo(
        "ERC721ReceiverMock", ["v1.9.0", "v1.9.1"]
    ),
    "400593f520c28ce9b68fb12bd4dd3f869f570f39": LibraryInfo("ERC721TokenMock", ["v1.9.0"]),
    "2442a363e65369915bcde718b986a2143220fbfd": LibraryInfo("ERC827TokenMock", ["v1.9.0"]),
    "59841830db8f308b717f22514cbc406dff101d0f": LibraryInfo("FinalizableCrowdsaleImpl", ["v1.9.0"]),
    "2022504c8205da3c77517ffbc24ec595065050e0": LibraryInfo("ForceEther", ["v1.9.0"]),
    "f0aac4a39cf1687f94c084250f2aadb75f9474b2": LibraryInfo("HasNoEtherTest", ["v1.9.0"]),
    "aba043594e0651956d0ae8be33625f29883a0503": LibraryInfo(
        "IncreasingPriceCrowdsaleImpl", ["v1.9.0"]
    ),
    "e04e7327bfe0b1c52d1c6ff340837d7752c6a1ef": LibraryInfo(
        "IndividuallyCappedCrowdsaleImpl", ["v1.9.0"]
    ),
    "3860cb9cc1bcc675eabfc3fc498c012f97956f89": LibraryInfo(
        "InsecureTargetMock", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "0ae95f3ba71966844f02df90764349726fa5faa3": LibraryInfo(
        "InsecureTargetBounty", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "056f7fb47b260ca924e77d4bf345dcf67e62b732": LibraryInfo(
        "LimitBalanceMock", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "3c0eb7e3a1376c180c4afc060e6b02ff2dc0a12a": LibraryInfo(
        "MathMock", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0"]
    ),
    "dc1cbbcf7506800281d7264f137d2d20e30c980a": LibraryInfo(
        "MerkleProofWrapper", ["v1.9.0", "v1.9.1"]
    ),
    "bba58d62208bcee8307170a5dc002d5f0c0c1d2d": LibraryInfo("MessageHelper", ["v1.9.0"]),
    "f5c9e9e324b4d6f1ef41008850e5dbb0e525c234": LibraryInfo("MintedCrowdsaleImpl", ["v1.9.0"]),
    "8d93ca1addadb71893e2016bfa26db40fc2f4a2f": LibraryInfo("PausableMock", ["v1.9.0"]),
    "36659de8c778859e75e98389e40f86261ca0becf": LibraryInfo("PausableTokenMock", ["v1.9.0"]),
    "a297f3f1391501f49a3d8bb132e158faaa7249b6": LibraryInfo(
        "PostDeliveryCrowdsaleImpl", ["v1.9.0"]
    ),
    "2695bb63d6fc96d972146f159cb17d2bdb7f1cd7": LibraryInfo(
        "PullPaymentMock", ["v1.9.0", "v1.9.1"]
    ),
    "b087e928c74ce7d5adc14e9b484bb7de22f268d4": LibraryInfo("RBACMock", ["v1.9.0"]),
    "0bddfeb265ff29d4c3d6ca38852747a1e21318ad": LibraryInfo(
        "ReentrancyAttack", ["v1.9.0", "v1.10.0"]
    ),
    "a9a47c2b37110ab4c5a96948b848e823abb391b9": LibraryInfo("ReentrancyMock", ["v1.9.0"]),
    "585bffaaba0b7bb6fd37817b94d373ec54c4d2c7": LibraryInfo("RefundableCrowdsaleImpl", ["v1.9.0"]),
    "30d70d64a1416b8cead631c93b84ed113b5e18d7": LibraryInfo("ERC20FailingMock", ["v1.9.0"]),
    "ae5f3e2f0996d8b0445e4890701f35389fd565c5": LibraryInfo("ERC20SucceedingMock", ["v1.9.0"]),
    "b5703426566223d0c7e0079a8aded144192c330d": LibraryInfo(
        "SafeERC20Helper", ["v1.9.0", "v1.9.1"]
    ),
    "378b31ac238e143f5f752834203492dd3980522f": LibraryInfo(
        "SafeMathMock", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0"]
    ),
    "2f487c8b59cc0cb91ea2ee7aa7a2b7b9bbe22a02": LibraryInfo(
        "SecureTargetMock", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "78c3a5e7b0d5b58efe770c54a73b42bf1d242d9b": LibraryInfo(
        "SecureTargetBounty", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "c4cfaf59a49f506e31c3acd8d3ae8624613c2044": LibraryInfo(
        "StandardBurnableTokenMock", ["v1.9.0", "v1.9.1"]
    ),
    "5a3481b0e8029747c9bf839d7a12b7f831513ba7": LibraryInfo(
        "StandardTokenMock", ["v1.9.0", "v1.9.1"]
    ),
    "eded4e7da3e73140ba6fd5a80217c562c5922c47": LibraryInfo("TimedCrowdsaleImpl", ["v1.9.0"]),
    "b8eaff3a88d6c9b87a050ae4e3caf8eb39c508f3": LibraryInfo("WhitelistMock", ["v1.9.0", "v1.10.0"]),
    "2e295e4571f9f017638cd4b9e013ce502d4f2759": LibraryInfo("WhitelistedCrowdsaleImpl", ["v1.9.0"]),
    "dd349689f6d497b6d60d18af598981c0c5ea5c43": LibraryInfo(
        "Claimable", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "b4c914658062b263ddd7bbad7a303f9aadb8edda": LibraryInfo(
        "Contactable", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "379f3940245b3bf07e3da0ba8bacb31a7b71837a": LibraryInfo(
        "DelayedClaimable", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "04a144226212c8093a72edac65132dfebf5cbc34": LibraryInfo("HasNoEther", ["v1.9.0"]),
    "e581fe4461bda93a810cf8f56e985d7b17e5c57c": LibraryInfo(
        "HasNoTokens", ["v1.9.0", "v1.10.0", "v1.11.0"]
    ),
    "adca50311c8c516281fae62e7bf8711b247dd1fe": LibraryInfo("Heritable", ["v1.9.0"]),
    "bff7a458838d22f59d77dcb1e4c8f71ad9e6c6ad": LibraryInfo("Ownable", ["v1.9.0"]),
    "b92612ef15ec3b9d6df30a8f7becdc945bde3d4b": LibraryInfo("Whitelist", ["v1.9.0"]),
    "c9ee90b58cfe7db8fb2093a5dc6ac901e3560376": LibraryInfo(
        "RBAC", ["v1.9.0", "v1.9.1", "v1.10.0"]
    ),
    "d07bdfe9e5c1197eaaeb8db19a60b2d7c8b08a88": LibraryInfo("RBACWithAdmin", ["v1.9.0"]),
    "3bf165712333a39e76e159a3406fa49517afe215": LibraryInfo(
        "Roles", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0"]
    ),
    "7e998f3b5ecb8820313c1bb24dfb0d6d99ace954": LibraryInfo(
        "PullPayment", ["v1.9.0", "v1.9.1", "v1.10.0"]
    ),
    "74d3dda7f213a09504a9a9291a40a3dcd8365fbd": LibraryInfo("SplitPayment", ["v1.9.0"]),
    "819441e9e704135b09b0b1f72db902159a737913": LibraryInfo(
        "BasicToken", ["v1.9.0", "v1.9.1", "v1.10.0"]
    ),
    "27dea92802e715fa1863d34fdd4d5c9c07f2447a": LibraryInfo(
        "BurnableToken", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "cddbea62966149d6c6e6709ab8568b3c4f0ad494": LibraryInfo("CappedToken", ["v1.9.0"]),
    "cf6e58a034f1418d57a0f1952afb136e82102f94": LibraryInfo("DetailedERC20", ["v1.9.0"]),
    "8d2f3828797c3e84f29d2c8cdb6ed25ee69511f6": LibraryInfo("ERC20", ["v1.9.0", "v1.9.1"]),
    "953db1b3480bf572e44ad6fa898f6c6bf2eee57c": LibraryInfo(
        "ERC20Basic", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0"]
    ),
    "241b903da1f922131be0e2bdf10c4306082848ea": LibraryInfo("MintableToken", ["v1.9.0"]),
    "b34956dcce7a77bd57b4fad7545ab5988bf8dbf1": LibraryInfo("SafeERC20", ["v1.9.0", "v1.9.1"]),
    "de2af31e6fa1013b6f867fa12ccaa7696d9442d7": LibraryInfo(
        "StandardBurnableToken", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "50589279d9b57e6c0ad23388176dda20dc4c491e": LibraryInfo("StandardToken", ["v1.9.0", "v1.9.1"]),
    "be03e255bc582a956bff757a7e1a8bad8bdc3361": LibraryInfo("TokenTimelock", ["v1.9.0"]),
    "59d01319278f7765dd0e242d02c1ca82e6ba091a": LibraryInfo("TokenVesting", ["v1.9.0"]),
    "012926dd9f55e8dfe9776b9f1df62546bca5ecc1": LibraryInfo(
        "DeprecatedERC721", ["v1.9.0", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "30067e830dea40199578d0debf1d3d2c85b310df": LibraryInfo(
        "ERC721Enumerable", ["v1.9.0", "v1.9.1"]
    ),
    "4a83cf38bff15fc12b16638f7844fc0f8980f9f3": LibraryInfo(
        "ERC721Metadata", ["v1.9.0", "v1.9.1", "v1.10.0"]
    ),
    "2e8afdc67c556a384622e8f1518264a445a92b57": LibraryInfo(
        "ERC721", ["v1.9.0", "v1.9.1", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "bb0256dd101e575fe0c2371482723f8e2c32c087": LibraryInfo("ERC721Basic", ["v1.9.0", "v1.9.1"]),
    "a8eecb22ae520032234d75016dfcf803ba6fba82": LibraryInfo(
        "ERC721BasicToken", ["v1.9.0", "v1.9.1"]
    ),
    "5ce55c0eca12e6589b4ccef66917574890fdf1af": LibraryInfo(
        "ERC721Holder", ["v1.9.0", "v1.9.1", "v1.10.0"]
    ),
    "4646738364802bb2215ef7f4062cdc03bc33bc33": LibraryInfo("ERC721Receiver", ["v1.9.0", "v1.9.1"]),
    "24749e32f3f9f241cbf61755cd27c4e1c33ec6ef": LibraryInfo("ERC721Token", ["v1.9.0"]),
    "34e294455d0b633a92c85294e33391da976dfff2": LibraryInfo("ERC827", ["v1.9.0"]),
    "5646047a82bc6b598f782b9ecfbe0ef37b1bde4b": LibraryInfo("ERC827Token", ["v1.9.0"]),
    "ba598a71f86f1d7453d8d921680d7bd75d34a15d": LibraryInfo("SignatureBouncer", ["v1.9.1"]),
    "af99a0bc53580c8d654923048cec891e61e24a6b": LibraryInfo("Pausable", ["v1.9.1"]),
    "eaf939ca050feaf102dbd9835b6a67eb4b51e0b9": LibraryInfo("SignatureBouncerMock", ["v1.9.1"]),
    "c998cfc7431ac0d0c66f70f0982b3e8659c6bfb9": LibraryInfo("DetailedERC20Mock", ["v1.9.1"]),
    "a364bd1d78dd9528eb357f93c190db2652cbbd5c": LibraryInfo("ERC721TokenMock", ["v1.9.1"]),
    "8b07a36751ac1e354baf93be047c852143a57119": LibraryInfo("PausableMock", ["v1.9.1"]),
    "70b936df444e167029f22e8ef48b007bbe37d544": LibraryInfo("PausableTokenMock", ["v1.9.1"]),
    "dc38f5ba7ca5eb5a8a85b7b0e9d8288a1e70e41d": LibraryInfo("RBACMock", ["v1.9.1"]),
    "d1f6822833daab2b5c6521ee6aacc6303b946095": LibraryInfo(
        "ERC20FailingMock", ["v1.9.1", "v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "87310193da0df53c2be5ff230d2704011a0806a5": LibraryInfo("ERC20SucceedingMock", ["v1.9.1"]),
    "d1dd6a62116d8605377f70bb5de6f2c70ced3d81": LibraryInfo("Ownable", ["v1.9.1"]),
    "be72653e125b02bb575d00a9a8db2b40aaa6bc9f": LibraryInfo("RBACWithAdmin", ["v1.9.1"]),
    "7c353bddb33d9c15e9aebfb843a1e5d63645f267": LibraryInfo("SplitPayment", ["v1.9.1"]),
    "a0b88b77efc2a12f98310d83fa335fa5564cca08": LibraryInfo("DetailedERC20", ["v1.9.1"]),
    "feb56e7c42453ae5639cbbcae4b8d8e5c59447c2": LibraryInfo("DetailedMintableToken", ["v1.9.1"]),
    "cea5d86a5cdca1d9dd226d199d740a3d3cd32d07": LibraryInfo("DetailedPremintedToken", ["v1.9.1"]),
    "6bed3b69e3391bded476aabdd2c5f861819e73f8": LibraryInfo("MintableToken", ["v1.9.1"]),
    "46ebd57a637d411818418140d0aa63dbf1cc2246": LibraryInfo("PausableToken", ["v1.9.1"]),
    "5cc2a3e344df53e317dbe38e76ac94695a38e9e0": LibraryInfo("TokenTimelock", ["v1.9.1"]),
    "3e7d8f34659881bc3b2ca951668372a47f79193d": LibraryInfo("TokenVesting", ["v1.9.1"]),
    "e197b8a76f56af18f47f67a89005390e3bd55694": LibraryInfo("ERC721Token", ["v1.9.1"]),
    "1b53bd5e5472c4a818e266b64d0f9e6fd49857cb": LibraryInfo("MintableERC721Token", ["v1.9.1"]),
    "ec78d7ca528901ef6910c0f44ab705b870742c90": LibraryInfo("Migratable", ["v1.9.1"]),
    "fc413be3907db5515f084a8fff63bcc8c5635400": LibraryInfo("AddressUtils", ["v1.10.0"]),
    "31c153b4c6b900b16219cae11feef97ce4076143": LibraryInfo(
        "LimitBalance", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "962b05e5b0824201f5aedc58501637db05b154a3": LibraryInfo("MerkleProof", ["v1.10.0"]),
    "b08f9ebec900e55ba7b20624dad0097bc243c12a": LibraryInfo("Crowdsale", ["v1.10.0"]),
    "5124365778e24aa55c9e06bdf26149d4310d95d0": LibraryInfo(
        "PostDeliveryCrowdsale", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "57737cab20c3fada86461ebe4df4b14d7d515b7a": LibraryInfo("RefundableCrowdsale", ["v1.10.0"]),
    "1fdb50fd86681dfa181c490bcdef28171be6e6f3": LibraryInfo("RefundVault", ["v1.10.0"]),
    "cde035237ef2f07d69f3756cd9d1305cda39f749": LibraryInfo("AllowanceCrowdsale", ["v1.10.0"]),
    "e7b6247a1c2be98eb8a1c56486c3f17dc60b98ed": LibraryInfo(
        "MintedCrowdsale", ["v1.10.0", "v1.11.0"]
    ),
    "e318ca5d228fcbbd844491efd5fee829e32c53ac": LibraryInfo(
        "IncreasingPriceCrowdsale", ["v1.10.0", "v1.11.0"]
    ),
    "e9b16e3a549af2c8cd56090702d269b432a80283": LibraryInfo(
        "CappedCrowdsale", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "bdaaf0e469b346ce4d51c3fe15d14a4b02bc990e": LibraryInfo(
        "IndividuallyCappedCrowdsale", ["v1.10.0", "v1.11.0"]
    ),
    "eff0fd34b36c459c2d98f5a04a7b04fff08674e0": LibraryInfo(
        "TimedCrowdsale", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "8a1c7e2eda5d6444d767db6e960beb998e94e523": LibraryInfo("WhitelistedCrowdsale", ["v1.10.0"]),
    "35690875b56b9ef06dc5c82640a067bd9132901c": LibraryInfo(
        "RBACWithAdmin", ["v1.10.0", "v1.11.0"]
    ),
    "c5dfbb1d2f9641afa4f031f2f600f697e9a77b05": LibraryInfo(
        "SampleCrowdsaleToken", ["v1.10.0", "v1.11.0"]
    ),
    "9f752a8cbc435f39d6c36760d3fff29d99d079c4": LibraryInfo(
        "SampleCrowdsale", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "edca9f3d7957cef23f6f3209af3eee94ea523194": LibraryInfo("SimpleSavingsWallet", ["v1.10.0"]),
    "f844de78dd748876a43a33fa9a6caccbe3fb511a": LibraryInfo("SimpleToken", ["v1.10.0"]),
    "0c02b9e264482b9501239880d508d2fc45a921c7": LibraryInfo("Destructible", ["v1.10.0", "v1.11.0"]),
    "d66ff49a491298f7d0aadc302cce5b80e20397c1": LibraryInfo(
        "TokenDestructible", ["v1.10.0", "v1.11.0"]
    ),
    "ee4d3ec37306122ceeec79f60680a632176509b0": LibraryInfo("SafeMath", ["v1.10.0", "v1.11.0"]),
    "1e3619093d26ad06a7fd448a3e4db543de00d219": LibraryInfo(
        "AllowanceCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "565c175208220601b83adfeaca95bb41efe016c3": LibraryInfo(
        "BasicTokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "635c6422d4af70e8ffe48d54148f457329870eaa": LibraryInfo(
        "BurnableTokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "e7177cb6bde32587072093fece1269add34133cc": LibraryInfo(
        "CappedCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "63f108c805f519b16c8db619e7274d4937aad376": LibraryInfo(
        "DetailedERC20Mock", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "fb554453f065e88a35f0d412de76fe4e83686366": LibraryInfo(
        "ERC223TokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "e288225fc414795b7697952164f0e2a02fb89e97": LibraryInfo("ERC721ReceiverMock", ["v1.10.0"]),
    "774d1a89a0f8fbb420f6a6586b9328e6853d5f7e": LibraryInfo(
        "ERC721TokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "8d29283dd9ef9bde0001ebf6a7c765a6af12bc68": LibraryInfo("ERC827TokenMock", ["v1.10.0"]),
    "7449c745206ac15d5192ba7a16bed39819a50113": LibraryInfo(
        "FinalizableCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "60704a7554b0ad4ee9d0626bcbbadbac87d8d270": LibraryInfo(
        "ForceEther", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "b339de538541166e1bf3390a1b07fef171e03b00": LibraryInfo(
        "HasNoEtherTest", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "80198840976a3fdcdcf2fa5a8d9454b1e39004de": LibraryInfo(
        "IncreasingPriceCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "9628906154701c6e5306e6da622b4db92cc6f6ec": LibraryInfo(
        "IndividuallyCappedCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "cd5924adb9ef87e99bcd94ae9ae57b7a6897b1e0": LibraryInfo(
        "MerkleProofWrapper", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "1f6d4d30c38abd953fca5a89b5193e10df9d1751": LibraryInfo(
        "MessageHelper", ["v1.10.0", "v1.11.0"]
    ),
    "0a1706f232f69f32bf2954b566c7c2c14d69392d": LibraryInfo(
        "MintedCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "c684d5ce1dd245aa8c912952594a373f977c76e7": LibraryInfo(
        "PausableMock", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "3be1ec9b4f338c96d86b894ba8ceb846fb647c23": LibraryInfo(
        "PausableTokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "b28308433da65d22476951196f1caeb41f26cf33": LibraryInfo(
        "PostDeliveryCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "559fa0817335651783601a27dde5faf21fc686b0": LibraryInfo("PullPaymentMock", ["v1.10.0"]),
    "8107d16875287a7046493571b10dd5eab0d97976": LibraryInfo("RBACMock", ["v1.10.0", "v1.11.0"]),
    "07e16eeb1ec64a6995695ed1816a95243000f8a8": LibraryInfo("ReentrancyMock", ["v1.10.0"]),
    "f0bd68476f483619630828a8419d39ac57d0f49b": LibraryInfo(
        "RefundableCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "2b40af803f1243f59805beb75d2afadf5fdb84a7": LibraryInfo(
        "ERC20SucceedingMock", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "3c6b59e930edaae5e84ee9338017b301d7fc12b4": LibraryInfo("SafeERC20Helper", ["v1.10.0"]),
    "695a35876abcaf66f60903ec69331e522a9001f8": LibraryInfo(
        "StandardBurnableTokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "07eb9f220d92b3b0a026d03abe31782e18b8a3aa": LibraryInfo(
        "StandardTokenMock", ["v1.10.0", "v1.11.0"]
    ),
    "13a503e0871b386c82691937b1cdca7542f35bbd": LibraryInfo(
        "TimedCrowdsaleImpl", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "f401c66a3d208ecf85040784b4eb8bb14e20d0e7": LibraryInfo(
        "WhitelistedCrowdsaleImpl", ["v1.10.0"]
    ),
    "93407117e15d8a7a63deaf473df32c73518a30ea": LibraryInfo("HasNoEther", ["v1.10.0"]),
    "baa2d89bbdb2edb622a4c9c1fdc23a6642d899c4": LibraryInfo("Heritable", ["v1.10.0"]),
    "211a4479365db5f0eaa4377da409e42db4a25b52": LibraryInfo("Ownable", ["v1.10.0"]),
    "ff57312417ac31bd0332308e65ef44f4d4062111": LibraryInfo(
        "Superuser", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "2db796d1517717fca1dd3983832f3a45f390ab55": LibraryInfo("Whitelist", ["v1.10.0"]),
    "2ee8d28f85d2697054414783e221260b9a7f6c97": LibraryInfo("SplitPayment", ["v1.10.0", "v1.11.0"]),
    "cd31a5ef466eeb34195d244e35a3c87b253e9788": LibraryInfo("CappedToken", ["v1.10.0"]),
    "405f965e67819b1bd2a94f8c121e66fccb198b8d": LibraryInfo(
        "DetailedERC20", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "1fafc8de20663f8ceaa7386a89b7c9e5dce82a3f": LibraryInfo("ERC20", ["v1.10.0", "v1.11.0"]),
    "dfac014d93a70a21a3b8b97e3d1b57efd14fe545": LibraryInfo(
        "MintableToken", ["v1.10.0", "v1.11.0"]
    ),
    "c9027d7b556e7e687bec0304ffaecf1d474eabfa": LibraryInfo(
        "PausableToken", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "968207fdc2ce386ab24cac2101d8d0e7f9eb7417": LibraryInfo(
        "RBACMintableToken", ["v1.10.0", "v1.11.0"]
    ),
    "87f48da5d43ba18ca15d7347a5626cc37cf01dac": LibraryInfo("SafeERC20", ["v1.10.0", "v1.11.0"]),
    "ab442d8dd4ecf1d472d9dce47ea1157c27d0a44e": LibraryInfo("StandardToken", ["v1.10.0"]),
    "075e8adaeaed593aad3e14ca9820df4e55e364e2": LibraryInfo(
        "TokenTimelock", ["v1.10.0", "v1.11.0"]
    ),
    "1fcb0b4c52970b0f395e2da5bc6595daa71daff2": LibraryInfo("TokenVesting", ["v1.10.0", "v1.11.0"]),
    "ef375977e93dc6aeae3256bc5a0c0ed23a734df8": LibraryInfo(
        "ERC721Enumerable", ["v1.10.0", "v1.11.0", "v1.12.0"]
    ),
    "15405a8487b11120873f75247b1ab5461f1ed8c7": LibraryInfo("ERC721Basic", ["v1.10.0"]),
    "4a3380e9127e514a0630ea0656facdebfe716acc": LibraryInfo("ERC721BasicToken", ["v1.10.0"]),
    "1c47823ad3c15275bfd34a4c1a66525fca5454bd": LibraryInfo("ERC721Receiver", ["v1.10.0"]),
    "95a8f9396ea8cbc14f6cca9a8b6492fbf2437f18": LibraryInfo("ERC721Token", ["v1.10.0"]),
    "9fcc86aa8a8ae5217bd10cce1a954c5cb7caac82": LibraryInfo("ERC827", ["v1.10.0"]),
    "68b878162744df8ddb16479dd790341cafce251f": LibraryInfo("ERC827Token", ["v1.10.0"]),
    "9c4ab3267a3dc0ce51b3baee28fae5006a3be725": LibraryInfo("AddressUtils", ["v1.11.0"]),
    "452fe8fdaa7d15bbe79e9ab641f3307b1bece216": LibraryInfo("Bounty", ["v1.11.0"]),
    "4b73fc34d4fe601e4c4065e08ec11fc8c3a1ad18": LibraryInfo("ECRecovery", ["v1.11.0"]),
    "19ced19ab2d8edf9fe46282e242d8b52a09f7bd6": LibraryInfo("MerkleProof", ["v1.11.0"]),
    "4e1211d90f62f0b3d59bb318ac744ac95e6f6317": LibraryInfo("SignatureBouncer", ["v1.11.0"]),
    "48d836f14524ef04eccac96647887425545781c0": LibraryInfo("Whitelist", ["v1.11.0"]),
    "ee718ffb3fe3609d882556704f41c62311effe27": LibraryInfo("Crowdsale", ["v1.11.0"]),
    "6bea0f0c1a89ad2622afba8f47a0af62c2799629": LibraryInfo(
        "RefundableCrowdsale", ["v1.11.0", "v1.12.0"]
    ),
    "8da34d0e919bf9d1a2b1da81e797a6c2c1ed60b4": LibraryInfo(
        "AllowanceCrowdsale", ["v1.11.0", "v1.12.0"]
    ),
    "8bf8cb311ea7d15c8ddaf54454e60ce44a60bdf4": LibraryInfo("WhitelistedCrowdsale", ["v1.11.0"]),
    "a1419a713627dbb2ffea8a68c616e0a051f1b606": LibraryInfo("SimpleSavingsWallet", ["v1.11.0"]),
    "0b8d54f5efc4de837b7dd93996db086849cb14da": LibraryInfo("SimpleToken", ["v1.11.0"]),
    "a7e1df3805ef75dc41a754ae5546f06fec8cb03f": LibraryInfo("ERC165", ["v1.11.0", "v1.12.0"]),
    "5e7625321628749b31d4c4cc45e2d90b556d6409": LibraryInfo(
        "SupportsInterfaceWithLookup", ["v1.11.0"]
    ),
    "c1351bcccd9852179bfd81b241caaa056de4be3b": LibraryInfo("SignatureBouncerMock", ["v1.11.0"]),
    "cd6add9c23aeffa94971107e162281b260df91dd": LibraryInfo(
        "ConditionalEscrowMock", ["v1.11.0", "v1.12.0"]
    ),
    "5b43908bda2ed2a2abd97bdc0c726f4e0a994686": LibraryInfo("ERC20WithMetadataMock", ["v1.11.0"]),
    "afd20cd7880b7afcab66a1177bea6b85ba76ae80": LibraryInfo(
        "ERC721ReceiverMock", ["v1.11.0", "v1.12.0"]
    ),
    "a53e6a8705e545971a03677411de3e3e2fa21104": LibraryInfo("PullPaymentMock", ["v1.11.0"]),
    "66ac45d59afe1d96a3512f788c9f1742c8d6948e": LibraryInfo("RBACCappedTokenMock", ["v1.11.0"]),
    "65022b9fefebb8d6c04e9d7c6869843a504cb607": LibraryInfo(
        "ReentrancyAttack", ["v1.11.0", "v2.0.0", "v2.0.1"]
    ),
    "429c0d0af89af3652ab701919da11ce73a98d37d": LibraryInfo(
        "ReentrancyMock", ["v1.11.0", "v2.0.0", "v2.0.1"]
    ),
    "b956eb0e6216174795f2ee06204c7da650e845b8": LibraryInfo(
        "SafeERC20Helper", ["v1.11.0", "v1.12.0"]
    ),
    "c2ef9875134777ad5fb22ebdc123e383caafbd19": LibraryInfo(
        "SupportsInterfaceWithLookupMock", ["v1.11.0", "v1.12.0"]
    ),
    "aaeffe18854cb829f1a400a2d89f0b625a5b345d": LibraryInfo("WhitelistMock", ["v1.11.0"]),
    "ed2e1b404135b09fe5f0d79f95dbe33b78b587f0": LibraryInfo(
        "WhitelistedCrowdsaleImpl", ["v1.11.0", "v1.12.0"]
    ),
    "319335756a88f45e8684a029ca1c8bc0a311da2a": LibraryInfo("HasNoEther", ["v1.11.0"]),
    "5527c4a0bee8b4bb21e2b8f3aef283d724dc62f6": LibraryInfo("Heritable", ["v1.11.0"]),
    "d2e619214bc724aeb273d48e420db453b3ffe31d": LibraryInfo("Ownable", ["v1.11.0", "v1.12.0"]),
    "4ace23c2264121b28731efcf28cd3552e6fca588": LibraryInfo("RBAC", ["v1.11.0"]),
    "2bfe51db8ee661f769d98f9ae45361a9b8f6e0ec": LibraryInfo(
        "ConditionalEscrow", ["v1.11.0", "v1.12.0"]
    ),
    "627f53ee54bf4c94d1cad825b7ae55998a65bc9d": LibraryInfo("Escrow", ["v1.11.0", "v1.12.0"]),
    "78f1f3f29386d9b09253ca23087eae02c2efedcd": LibraryInfo("PullPayment", ["v1.11.0", "v1.12.0"]),
    "142c5a368e011d0578205a2fb5f776b4937605df": LibraryInfo("RefundEscrow", ["v1.11.0", "v1.12.0"]),
    "392ccebdf4b62992e7460dc3f65064cb5d042a45": LibraryInfo(
        "ERC20TokenMetadata", ["v1.11.0", "v1.12.0"]
    ),
    "4a35664713c0831432f0f44b72df33f7eed2248a": LibraryInfo("ERC20WithMetadata", ["v1.11.0"]),
    "38c60461bba3a6795a0459e3de0c035ee1d1a53e": LibraryInfo("BasicToken", ["v1.11.0"]),
    "917071f9daeb837c90acc2222568398b048b95f6": LibraryInfo("CappedToken", ["v1.11.0", "v1.12.0"]),
    "2b6593f6ad447e65d848bc4bfec26e9a8b34557e": LibraryInfo("StandardToken", ["v1.11.0"]),
    "3e6344b21675b204f35c12801cea0dfe18d4d298": LibraryInfo(
        "ERC721Metadata", ["v1.11.0", "v1.12.0"]
    ),
    "ed3cce364a25058da857c468423935a1b5fde50d": LibraryInfo("ERC721Basic", ["v1.11.0"]),
    "1a45edece56696e721cddc98e8f6703a1d8bbf9b": LibraryInfo("ERC721BasicToken", ["v1.11.0"]),
    "cb15d8841ffa1b27b982e31901772957f6123aad": LibraryInfo("ERC721Holder", ["v1.11.0"]),
    "715d07f7f060007413defdb6fd5c6934486f34f7": LibraryInfo("ERC721Receiver", ["v1.11.0"]),
    "0144a17b7f1ed3cd662df4069296e2e1c32c8dd8": LibraryInfo("ERC721Token", ["v1.11.0"]),
    "0450b83815a1e26a02b54c4233ac7aa4cf053ea9": LibraryInfo("AddressUtils", ["v1.12.0"]),
    "d583f3e45f2c243e55ee47a107a29bb9e972fe68": LibraryInfo("AutoIncrementing", ["v1.12.0"]),
    "a8144e43cf0c0c8b0bb54dcedb0531639e4d00d8": LibraryInfo("Bounty", ["v1.12.0"]),
    "d3f87956fa5f05f54106216a9c4a8079ba8d086a": LibraryInfo("ECRecovery", ["v1.12.0"]),
    "094905728bfb1ba7462642ae7ce245c709717531": LibraryInfo("MerkleProof", ["v1.12.0"]),
    "3cb4bc1e9a9a34a46858922cba2f0af59d767054": LibraryInfo("ReentrancyGuard", ["v1.12.0"]),
    "c00a7c93b18d897e6ebf868e0b093ed6ace719dd": LibraryInfo("SignatureBouncer", ["v1.12.0"]),
    "a1b464a6a3a1bbbd2fe33b5c231eba11236fa92e": LibraryInfo("Whitelist", ["v1.12.0"]),
    "12a2f840294d267c6950a1347b726222b416ed46": LibraryInfo("RBAC", ["v1.12.0"]),
    "50dd834b3d24a0bab1361fb858cbc51cf67ccbcf": LibraryInfo("Roles", ["v1.12.0"]),
    "e11c891ecfb38b3bc7f4cf1363aae79feb99cf12": LibraryInfo("Crowdsale", ["v1.12.0"]),
    "8b5f8bc529ee24fd54869c1d3dcfc18990a59548": LibraryInfo("FinalizableCrowdsale", ["v1.12.0"]),
    "2b6997bc5d0b3be1d0e2c1869353383a2fbd4993": LibraryInfo("MintedCrowdsale", ["v1.12.0"]),
    "59ed05ce0be380f62d4a3999c32428497594e327": LibraryInfo(
        "IncreasingPriceCrowdsale", ["v1.12.0"]
    ),
    "8a8a532f2e3ea4c08ff27af946fe20298a1e45ae": LibraryInfo(
        "IndividuallyCappedCrowdsale", ["v1.12.0"]
    ),
    "8a9c055e3d1349a664caa802eb204cd198a0f539": LibraryInfo("WhitelistedCrowdsale", ["v1.12.0"]),
    "230848a3836ccef1f4430b0bf203cd21f8052291": LibraryInfo("RBACWithAdmin", ["v1.12.0"]),
    "0ce489b153032a7ee90ed0eddca2c52daef1abf3": LibraryInfo("SimpleSavingsWallet", ["v1.12.0"]),
    "1a2d42f20aef6df99897db234b801340a423450c": LibraryInfo("SimpleToken", ["v1.12.0"]),
    "90d9d40b3412f59732a2bb622a88a4bc36f6b821": LibraryInfo(
        "SupportsInterfaceWithLookup", ["v1.12.0"]
    ),
    "2321441ae68a4e14b2306c7575958449a3c29b98": LibraryInfo("Destructible", ["v1.12.0"]),
    "ad31f71ee52649c94cb438200fd1c1ed08094bf5": LibraryInfo("Pausable", ["v1.12.0"]),
    "53f24a0ac15b157dbbc3f61d5c1408998c1db0ef": LibraryInfo("TokenDestructible", ["v1.12.0"]),
    "2ff3848281b684d98af5b73bd62d933ad9795e1b": LibraryInfo("Math", ["v1.12.0"]),
    "5b9701e018c1d6a97bc507e5c00433246ac7f025": LibraryInfo("SafeMath", ["v1.12.0"]),
    "a03dbbc1c4f0ae5e64d672d84690dc48152e2650": LibraryInfo("AutoIncrementingImpl", ["v1.12.0"]),
    "977f8bdafbecf36f639f00746a506a0665e14ee8": LibraryInfo("BasicTokenMock", ["v1.12.0"]),
    "68cd257584aa39dab35cc08947cb4aabe9ce852f": LibraryInfo("SignatureBouncerMock", ["v1.12.0"]),
    "f08f0cd0d441234b1b15fa1cc1aeed01d651523c": LibraryInfo("BurnableTokenMock", ["v1.12.0"]),
    "482f4acdd6c3523e078f68f3905f8e9c0bd96f85": LibraryInfo("DestructibleMock", ["v1.12.0"]),
    "e5b1031669b3bfd06fb12626a47888243c07c469": LibraryInfo("ECRecoveryMock", ["v1.12.0"]),
    "d439e3f9b056d304aba764b34c2623b4600c55fb": LibraryInfo("ERC20WithMetadataMock", ["v1.12.0"]),
    "22f1d1e0932e3558eef115f3e867619c135b5a26": LibraryInfo("ERC223TokenMock", ["v1.12.0"]),
    "c37afaa6e4b7ab6775e3c9b3b2c1b848ee3e0548": LibraryInfo("ERC721TokenMock", ["v1.12.0"]),
    "fa28e9b84c25de3655f8068c07f5ae030f00705c": LibraryInfo("MathMock", ["v1.12.0"]),
    "41437f07fa0866525684129c46b107cf2a28d9dc": LibraryInfo("MessageHelper", ["v1.12.0"]),
    "e781977728414ecb0dc389712cbaea2f3c1b2401": LibraryInfo("PausableTokenMock", ["v1.12.0"]),
    "c5cbc9122a21b464aec57faf3e8b783f455f3175": LibraryInfo("PullPaymentMock", ["v1.12.0"]),
    "10618dab995da34a38ef8e7d53b069a7b0bda621": LibraryInfo("RBACCappedTokenMock", ["v1.12.0"]),
    "9fae112623b416c1c3a847d6de92967854f4e3ba": LibraryInfo("RBACMock", ["v1.12.0"]),
    "84992bb16c0aa52e586c7ce43af9f8ef80d71382": LibraryInfo("ReentrancyAttack", ["v1.12.0"]),
    "ec8922620cd3664ea34d9295aa85c64b77b61c0c": LibraryInfo("ReentrancyMock", ["v1.12.0"]),
    "2cddebeab16c4e11f6457eae79615514d0467224": LibraryInfo("SafeMathMock", ["v1.12.0"]),
    "ed5496d88df044b594a28d8b4e2b02aa8c5c98a9": LibraryInfo(
        "StandardBurnableTokenMock", ["v1.12.0"]
    ),
    "4b79de8b6a7b868ac3db16c36c7caf1511dc4e9c": LibraryInfo("StandardTokenMock", ["v1.12.0"]),
    "207467653a042b1e3f796be82daa00deae4be4e0": LibraryInfo("WhitelistMock", ["v1.12.0"]),
    "3b64fac09338834e7f31e4a94857c405644ad27a": LibraryInfo("CanReclaimToken", ["v1.12.0"]),
    "39458b20c5ba02b89578bdb4d0569fdedbb89449": LibraryInfo("Claimable", ["v1.12.0"]),
    "30b2eb1b65dfd72e93c6370eec1b66cbc77514b6": LibraryInfo("Contactable", ["v1.12.0"]),
    "d08d45bef636d729b4781cee2671f02dfc65cd46": LibraryInfo("DelayedClaimable", ["v1.12.0"]),
    "733f7047e97a7426847cbc4176463ee020cf48d6": LibraryInfo("HasNoContracts", ["v1.12.0"]),
    "4a4e894cd3cd3cfa4dcbcbd9568f81d20cd4e307": LibraryInfo("HasNoEther", ["v1.12.0"]),
    "b025cfaf6f8e5da5efafe9883f25f18bab015a1f": LibraryInfo("HasNoTokens", ["v1.12.0"]),
    "98a5d657fe6eb93bcdb660880496f6c163e654c1": LibraryInfo("Heritable", ["v1.12.0"]),
    "8d77727ba855420961ee128de2676fec22402a03": LibraryInfo("SplitPayment", ["v1.12.0"]),
    "55799f56ada0b8e0bcc75ecce38851eeb1332d8a": LibraryInfo("ERC20WithMetadata", ["v1.12.0"]),
    "3c34d6a7f6c127303531d7e54e94a47fe0e30e82": LibraryInfo("BasicToken", ["v1.12.0"]),
    "c784fa49f4c22ac28509c8b0d54381eabcc00a99": LibraryInfo("ERC20", ["v1.12.0"]),
    "d89b847b33cf7f9529f426c6ed57e4b12cadda40": LibraryInfo("ERC20Basic", ["v1.12.0"]),
    "c992e0acf64fafaea8a3158d8d80b84e22b3aaca": LibraryInfo("MintableToken", ["v1.12.0"]),
    "bec3d2b20fa3b24ef5ac434c4a01b47b1e64a134": LibraryInfo("RBACMintableToken", ["v1.12.0"]),
    "60e42b733ad56c03b8addc0df215791b1338c01e": LibraryInfo("SafeERC20", ["v1.12.0"]),
    "ee8d24c22c925406ad22c22adab9654866eafdf3": LibraryInfo("StandardToken", ["v1.12.0"]),
    "28a8c7bb0a04847910d3f9eead16d6d449620534": LibraryInfo("TokenTimelock", ["v1.12.0"]),
    "1d8a3c508c18473083cb5db9961a36ba1a7f796e": LibraryInfo("TokenVesting", ["v1.12.0"]),
    "c29ab0fd5418aa6c45a6e82f4d5a4f1477241875": LibraryInfo("ERC721Basic", ["v1.12.0"]),
    "40d61fc659d2cba425f99f5b2656eb37b35731a4": LibraryInfo("ERC721BasicToken", ["v1.12.0"]),
    "bb10ec6ee3cdd5386ecfd6de333f1eeb6a377689": LibraryInfo("ERC721Holder", ["v1.12.0"]),
    "950c07b39c3ca854d94e48357f5d453e4c9c1965": LibraryInfo("ERC721Receiver", ["v1.12.0"]),
    "6a9692e0a456886959918a48694dcd3dcb8baf5f": LibraryInfo("ERC721Token", ["v1.12.0"]),
    "f0a61efe61df17f5559adaead1964139182d7dbf": LibraryInfo("Roles", ["v2.0.0", "v2.0.1"]),
    "0d6fbe8089bfed5e4961f8bc56d5c8fb7be2dbda": LibraryInfo("CapperRole", ["v2.0.0", "v2.0.1"]),
    "c7189a4af9a64378f15e69b14fc8e8b9cf99779a": LibraryInfo("MinterRole", ["v2.0.0", "v2.0.1"]),
    "61a08e1edc53903eaeda23582b34825c0a67d23c": LibraryInfo("PauserRole", ["v2.0.0", "v2.0.1"]),
    "d775bbc48440cc258eaa96091fcb81fa08bad123": LibraryInfo("SignerRole", ["v2.0.0", "v2.0.1"]),
    "de16a5f2763080c0e057578a3cca2c570af9d066": LibraryInfo("Crowdsale", ["v2.0.0", "v2.0.1"]),
    "567baa80771bce105326a8b76f150738e6a10db3": LibraryInfo(
        "FinalizableCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "ffd73415ed9b47f97e48f5b42212bb055b4d21ed": LibraryInfo(
        "PostDeliveryCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "ab93b46587fb58c1adb6cbd580ca17412917b74e": LibraryInfo(
        "RefundableCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "a3a1fa663a64dda4b8c95f50c518bad87f75541e": LibraryInfo(
        "AllowanceCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "656d0767acf97048298609648350fd1b019442a7": LibraryInfo(
        "MintedCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "9ab95e8d5b012575e490704b512ce4928dbee629": LibraryInfo(
        "IncreasingPriceCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "41f26f62f9f5227b1b6dbf65a6196c226e0939c8": LibraryInfo(
        "CappedCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "b8bd1ce8e8a33223abedb3548de7c2f989969ebc": LibraryInfo(
        "IndividuallyCappedCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "7b2a6e8e9aa71fb6a5d28b20399b0f5dccbd5463": LibraryInfo("TimedCrowdsale", ["v2.0.0", "v2.0.1"]),
    "e6060cd66b2d3908f948ae9b850e85c3464ea305": LibraryInfo("ECDSA", ["v2.0.0", "v2.0.1"]),
    "0260526f527ee9224774358021b9859015296518": LibraryInfo("MerkleProof", ["v2.0.0", "v2.0.1"]),
    "1b7e98ea211e7445e5f678fa148ea775af49b6e1": LibraryInfo("Counter", ["v2.0.0", "v2.0.1"]),
    "5be5fa4c91b2869c02f52a199e21be5806044560": LibraryInfo(
        "ERC20TokenMetadata", ["v2.0.0", "v2.0.1"]
    ),
    "d769c77787738e2e01649f5b5b943fb06ed9b8a9": LibraryInfo(
        "ERC20WithMetadata", ["v2.0.0", "v2.0.1"]
    ),
    "423800580427804d9eca8b706c43dc0297e37614": LibraryInfo("ERC20Migrator", ["v2.0.0", "v2.0.1"]),
    "8d7f569e100340e8ba17eaedc939ff68b406b05e": LibraryInfo(
        "SignatureBouncer", ["v2.0.0", "v2.0.1"]
    ),
    "b66a976d5f147079fb9c7f0a12415e008f585598": LibraryInfo("TokenVesting", ["v2.0.0", "v2.0.1"]),
    "3f9165306b2f53880ed5096af1b4e74db56da9bf": LibraryInfo(
        "SampleCrowdsaleToken", ["v2.0.0", "v2.0.1"]
    ),
    "1265d4f6bf6767e10033e733858ee6fa32a9073c": LibraryInfo(
        "SampleCrowdsale", ["v2.0.0", "v2.0.1"]
    ),
    "3c7f94391a02d5dc6f8f262ec96b3bc2a4b25640": LibraryInfo("SimpleToken", ["v2.0.0", "v2.0.1"]),
    "713380dc6ccc9d47f8d31a25eb0e446ebc4b4863": LibraryInfo("ERC165", ["v2.0.0", "v2.0.1"]),
    "c281f8016ab3d891630a35bd07f11dff97431234": LibraryInfo("ERC165Checker", ["v2.0.0", "v2.0.1"]),
    "1d4d0241d585c68fb08c1599437a4eea11eeab02": LibraryInfo("IERC165", ["v2.0.0", "v2.0.1"]),
    "313e8327db21cc8aa166fe5721eb99a46e4fa19c": LibraryInfo("Pausable", ["v2.0.0", "v2.0.1"]),
    "3d6ac03389ed6c835e26b7ebd8cd6f5bbc37934a": LibraryInfo("Math", ["v2.0.0", "v2.0.1"]),
    "8580d3e0df2d45ed48cbd99d42c0934038129cf7": LibraryInfo("SafeMath", ["v2.0.0", "v2.0.1"]),
    "113210a137c1be5187dcb3918a2a521d63f540cf": LibraryInfo("AddressImpl", ["v2.0.0", "v2.0.1"]),
    "e09a6efec62a3a1d426fcf5bf0a6ef150cadb36d": LibraryInfo(
        "AllowanceCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "34f5dc1d6acd84e2efeba46c180527f251dadcca": LibraryInfo("ArraysImpl", ["v2.0.0", "v2.0.1"]),
    "5fe750839b60d2691dfc55d926090028b5003043": LibraryInfo(
        "CappedCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "39412da7b5fdc81977acbda550e8dc71f6dba41b": LibraryInfo("CapperRoleMock", ["v2.0.0", "v2.0.1"]),
    "717e4d2b812a14a6c4d5658cb94dcc835a0af6f9": LibraryInfo(
        "ConditionalEscrowMock", ["v2.0.0", "v2.0.1"]
    ),
    "85e956ec45ece826f1c53505c1f035f3329fe0ad": LibraryInfo("CounterImpl", ["v2.0.0", "v2.0.1"]),
    "7ab9fe5373ce944504f2893349ea086b216b71a8": LibraryInfo("CrowdsaleMock", ["v2.0.0", "v2.0.1"]),
    "c321c20499e195867282851da42f2ccbbdb96167": LibraryInfo(
        "ERC20DetailedMock", ["v2.0.0", "v2.0.1"]
    ),
    "5e0bcabbb2cfd18eb2d43ff6fd8d8e20dbeeb019": LibraryInfo("ECDSAMock", ["v2.0.0", "v2.0.1"]),
    "a5da195613c182f94167d833dec5c7d4da0b5ba7": LibraryInfo(
        "SupportsInterfaceWithLookupMock", ["v2.0.0", "v2.0.1"]
    ),
    "bc1a4e4cfd066ef11bc6e2465ddec0f3fd4d51c4": LibraryInfo(
        "ERC165InterfacesSupported", ["v2.0.0", "v2.0.1"]
    ),
    "29cd8653e4b4504f0999a2454d9abf1f945de8f9": LibraryInfo(
        "ERC165NotSupported", ["v2.0.0", "v2.0.1"]
    ),
    "ae16304dfc91c51729a425eaf772ae8d08593dae": LibraryInfo(
        "ERC165CheckerMock", ["v2.0.0", "v2.0.1"]
    ),
    "aea815c696fff49c7fc52185b0523a33f7371b49": LibraryInfo("ERC165Mock", ["v2.0.0", "v2.0.1"]),
    "b7b9d98b25d14185d4e3c2986c7a5a39b1f0781d": LibraryInfo(
        "ERC20BurnableMock", ["v2.0.0", "v2.0.1"]
    ),
    "2399138dd71e45eaa2b5496aa7c751e39304ff91": LibraryInfo(
        "ERC20MintableMock", ["v2.0.0", "v2.0.1"]
    ),
    "069f9a6dfd87e2586b4fab42ca29e826310646ea": LibraryInfo("ERC20Mock", ["v2.0.0", "v2.0.1"]),
    "a5c6bf38e0fa04c8d470478a4bb8a3076e00e6e0": LibraryInfo(
        "ERC20PausableMock", ["v2.0.0", "v2.0.1"]
    ),
    "9a8f6b3985ad17fe0cadbda553573df4e4731e7e": LibraryInfo(
        "ERC20WithMetadataMock", ["v2.0.0", "v2.0.1"]
    ),
    "947e9e69d2016cebb10ee296f0f6495090671a21": LibraryInfo("ERC721FullMock", ["v2.0.0", "v2.0.1"]),
    "3ca707c71f9022105f61b352c598c256703178f2": LibraryInfo(
        "ERC721MintableBurnableImpl", ["v2.0.0", "v2.0.1"]
    ),
    "7c3cb25da3236a7c5738e31d410df75d16af096c": LibraryInfo("ERC721Mock", ["v2.0.0", "v2.0.1"]),
    "cb9a0e0a90469cd5b4e5aca0a818330f486bc3f9": LibraryInfo(
        "ERC721PausableMock", ["v2.0.0", "v2.0.1"]
    ),
    "13b19933bdd88840f5a617e14c9d736546ea8839": LibraryInfo(
        "ERC721ReceiverMock", ["v2.0.0", "v2.0.1"]
    ),
    "53bfe5d6b4368228e985c1fe3f02b8534416b3a0": LibraryInfo("EventEmitter", ["v2.0.0", "v2.0.1"]),
    "7057eb7b10d45a631cb5f442fc76bb7d5407a901": LibraryInfo(
        "FinalizableCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "2c959d10bff6c2909017efd20dc0e347da94e219": LibraryInfo(
        "IncreasingPriceCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "4a383b44bd773fe5ed6e84ff12070f60603c1eca": LibraryInfo(
        "IndividuallyCappedCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "15f79f51354210f3bf40a1555bd9e0f479292474": LibraryInfo("MathMock", ["v2.0.0", "v2.0.1"]),
    "f1291dc03b8c8f52ebc9ebda49c5ec933f050fa2": LibraryInfo(
        "MerkleProofWrapper", ["v2.0.0", "v2.0.1"]
    ),
    "f1cfdc773653bf69f5c277a60d81abd46029bebd": LibraryInfo(
        "MintedCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "cedf354f18ea2894c41fb93c79a08d07051846c4": LibraryInfo("MinterRoleMock", ["v2.0.0", "v2.0.1"]),
    "43a5ef129162556fd38e9c4175c7dcbcf3213d22": LibraryInfo("OwnableMock", ["v2.0.0", "v2.0.1"]),
    "59b3c7740b08088fb10e47d0d86fb6b7312e269a": LibraryInfo("PausableMock", ["v2.0.0", "v2.0.1"]),
    "d2b11cbf3fca7f65ac31170f6e1533b639486478": LibraryInfo("PauserRoleMock", ["v2.0.0", "v2.0.1"]),
    "4c25587eb2479ee3623ae6e168e3edf3f51914b7": LibraryInfo(
        "PostDeliveryCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "dc38502622bd92737566c51aba07ec48ed2c02ac": LibraryInfo(
        "PullPaymentMock", ["v2.0.0", "v2.0.1"]
    ),
    "1c605d2812687edd646a5fde7d2fe7ccda137edb": LibraryInfo(
        "RefundableCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "03dfbef44fe5a4a75c99a3e995675f027f15b2d6": LibraryInfo("RolesMock", ["v2.0.0", "v2.0.1"]),
    "938a3b0db268f2cefb5b7eb3ed792308f5865027": LibraryInfo(
        "ERC20FailingMock", ["v2.0.0", "v2.0.1"]
    ),
    "45d60ab40be79c18dcb7a111ab02614c3e47db37": LibraryInfo("ERC20SucceedingMock", ["v2.0.0"]),
    "2e88c135c98b395714739991d9072bdaf48b7cf0": LibraryInfo(
        "SafeERC20Helper", ["v2.0.0", "v2.0.1"]
    ),
    "0dc70ec0c9017ae55f65d3473d5a44f0c093dcab": LibraryInfo("SafeMathMock", ["v2.0.0", "v2.0.1"]),
    "337c1f8e999806aed78498d4372754b2344ccb2d": LibraryInfo("SecondaryMock", ["v2.0.0", "v2.0.1"]),
    "3f228f7bf41c099970f6748488b9cd7d00afe7f6": LibraryInfo(
        "SignatureBouncerMock", ["v2.0.0", "v2.0.1"]
    ),
    "caf3459749bb0264fa5a5d0a07f413f6991e0c41": LibraryInfo("SignerRoleMock", ["v2.0.0", "v2.0.1"]),
    "a2df662c3e2a73f196b5067859545a352db2bdac": LibraryInfo(
        "TimedCrowdsaleImpl", ["v2.0.0", "v2.0.1"]
    ),
    "e2ca5cd4923928c9f46de8e2e7df82ba01585738": LibraryInfo("Ownable", ["v2.0.0", "v2.0.1"]),
    "a6c503a46f2f91f5fb01793e96c7cb9c5363069e": LibraryInfo("Secondary", ["v2.0.0", "v2.0.1"]),
    "bb8f25ed8686742450daf6ba9b7cf99a2d20dacd": LibraryInfo(
        "PaymentSplitter", ["v2.0.0", "v2.0.1"]
    ),
    "52b717d273b5bfb68c8630175990354fc172b4e6": LibraryInfo("PullPayment", ["v2.0.0", "v2.0.1"]),
    "186ae2534c331ef59b6a86efc4a02d3b41cf1c8d": LibraryInfo(
        "ConditionalEscrow", ["v2.0.0", "v2.0.1"]
    ),
    "e2af959beebe03963562c8e06b5eddbfe4e8b750": LibraryInfo("Escrow", ["v2.0.0", "v2.0.1"]),
    "284f716f2501cfb02bee9357adc4c1eb840b0ac0": LibraryInfo("RefundEscrow", ["v2.0.0", "v2.0.1"]),
    "8235160a08bafe5bcafad41567e3229bbc331839": LibraryInfo("ERC20", ["v2.0.0", "v2.0.1"]),
    "4a97e9cbe78ad401ec19e46d114c71ea6f6f3d14": LibraryInfo("ERC20Burnable", ["v2.0.0", "v2.0.1"]),
    "c098a863a8b795e46bd3c055ebf944190443f2be": LibraryInfo("ERC20Capped", ["v2.0.0", "v2.0.1"]),
    "9dc5cc5b708cd1822f27baee4bc9c7d5f1b15d15": LibraryInfo("ERC20Detailed", ["v2.0.0", "v2.0.1"]),
    "0222ab47eca4f760dd21963f230a5fb803c0b4db": LibraryInfo("ERC20Mintable", ["v2.0.0", "v2.0.1"]),
    "23c0bd7b456d222b9d9625220eff56887fcff2ff": LibraryInfo("ERC20Pausable", ["v2.0.0", "v2.0.1"]),
    "fc05cf3f16e6ed0739b635d0b79e115d53ab4d76": LibraryInfo("IERC20", ["v2.0.0", "v2.0.1"]),
    "f05d94772232c941ce0bba7c06a494b3a0b0a217": LibraryInfo("SafeERC20", ["v2.0.0"]),
    "5eba5fb2bcd1248ec673a99ce57e788601326cdb": LibraryInfo("TokenTimelock", ["v2.0.0", "v2.0.1"]),
    "18adf8251b9db34a725031820ac989d18b6823f7": LibraryInfo("ERC721", ["v2.0.0", "v2.0.1"]),
    "10c5c3d991ca543dc5cc61d85664c797a01dd473": LibraryInfo("ERC721Burnable", ["v2.0.0", "v2.0.1"]),
    "beb061075916c16204b16cc18d4a3804df2aaeeb": LibraryInfo(
        "ERC721Enumerable", ["v2.0.0", "v2.0.1"]
    ),
    "8c15a90797b67219f50776315045bdad8ebe7a87": LibraryInfo("ERC721Full", ["v2.0.0", "v2.0.1"]),
    "f0ab234347570e7a9fc23f9d740b6784f31f2a58": LibraryInfo("ERC721Holder", ["v2.0.0", "v2.0.1"]),
    "5769b699617659dc63abace9efab19a6bb17a22e": LibraryInfo("ERC721Metadata", ["v2.0.0", "v2.0.1"]),
    "1f3d7d62ddc8d3c2b2a20255a4c40ee86432049e": LibraryInfo(
        "ERC721MetadataMintable", ["v2.0.0", "v2.0.1"]
    ),
    "e9ea73c83db4303fb0a6556f2b37eee4441b73df": LibraryInfo("ERC721Mintable", ["v2.0.0", "v2.0.1"]),
    "f82126eaeab8efc10723ee81a2f039d1baa7f6df": LibraryInfo("ERC721Pausable", ["v2.0.0", "v2.0.1"]),
    "560f515efb7ed83cf9c09d5b79693343104260d4": LibraryInfo("IERC721", ["v2.0.0", "v2.0.1"]),
    "67ad40b09e6d653e19421f7014f3e350d5cdd9ac": LibraryInfo(
        "IERC721Enumerable", ["v2.0.0", "v2.0.1"]
    ),
    "90d70ae5ca5809d733d2e9fb28f817532cf2f0fb": LibraryInfo("IERC721Full", ["v2.0.0", "v2.0.1"]),
    "51959c2d6c447821dd8897bda07dcb6c633282ba": LibraryInfo(
        "IERC721Metadata", ["v2.0.0", "v2.0.1"]
    ),
    "e14b06d2c5031542140ef8bc33fd56fd99c2ecc6": LibraryInfo(
        "IERC721Receiver", ["v2.0.0", "v2.0.1"]
    ),
    "03d71a566ea9225b43c66ae51dceebcd0da7e323": LibraryInfo("Address", ["v2.0.0", "v2.0.1"]),
    "a41c0e26a104eac14adff7bfb2fbaa3e223883e5": LibraryInfo("Arrays", ["v2.0.0", "v2.0.1"]),
    "d3ed07597d18babbd7344381e4e6d7b727795ca8": LibraryInfo(
        "ReentrancyGuard", ["v2.0.0", "v2.0.1"]
    ),
    "8b179f92ca6c1e439bb544b4798c389b5c78687b": LibraryInfo("ERC20SucceedingMock", ["v2.0.1"]),
    "ef0d299d4c858659f2b78e2ede4e089067ef911b": LibraryInfo("SafeERC20", ["v2.0.1"]),
    "49d0b746a287d74cc714cbf2c174c231093fbf72": LibraryInfo(
        "Roles", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "e58c83075e53473844ccb571dde2cd30a4b82912": LibraryInfo(
        "CapperRole", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "da35a3d6d7d9d825fbb987d916b68fd32e348f47": LibraryInfo(
        "MinterRole", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "69fa5a584acfdc5b9a6d8e76882308aad31a31e4": LibraryInfo(
        "PauserRole", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "a81e3a3364183cd787d8e461c6df7daaf55586f2": LibraryInfo(
        "SignerRole", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "581f46692dcd9692ca67f5cc61a7bb1b3e712290": LibraryInfo(
        "WhitelistAdminRole", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "42d70f9fafd3ff7a27bedd0976b0905416bb0a4f": LibraryInfo(
        "WhitelistedRole", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "780a9ae4d9266ce7ec373260ffce87614258ca2f": LibraryInfo(
        "Crowdsale", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "0dbefc37cfbfcfe26099c488dadba4a66d6e9512": LibraryInfo(
        "FinalizableCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "60ff213d27e3d08e39d78629af2e0f57119d93e2": LibraryInfo(
        "PostDeliveryCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "487942e4eb8721d19908196bd30f897dc2c6db3e": LibraryInfo(
        "RefundableCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "fb65273ef381e17d86e898541acd1fba51e304a7": LibraryInfo(
        "RefundablePostDeliveryCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "961682e22bd8ffe0ffcc8111fd7e2ad1003d2189": LibraryInfo(
        "AllowanceCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "ebaedbafbdaa1cde24c257781d36ba931a2dd830": LibraryInfo(
        "MintedCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "e2c4d52950ae64e9f7a4f551972df02e1b099de5": LibraryInfo(
        "IncreasingPriceCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "f62969face2bdc7724d99bcd5046883288ecea52": LibraryInfo(
        "CappedCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "43b1d8a5e54c23dc212c7f199511a965a4fec5b7": LibraryInfo(
        "IndividuallyCappedCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "fb880cb8c46f68da6b53afca6fa8429b5bab3ade": LibraryInfo(
        "PausableCrowdsale",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "dd7b8f3a631856e81a5fd24beb58fa56417cd0fc": LibraryInfo(
        "TimedCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "3bf3e3bb72048132bff0717ef5dd2dd25d61f229": LibraryInfo(
        "WhitelistCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "8eac263edf76d56c747feb9a5a4e5529d920aa11": LibraryInfo(
        "ECDSA", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "d86f0bd36ed54800fbf5d094c0cd61680bd7fe22": LibraryInfo(
        "MerkleProof", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "d86f0434c7e803fa4e355f6bb78c5847d8e828e6": LibraryInfo(
        "Counter", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "3063a8a855ab9d8e1d31ac38179c32bd475a2aa1": LibraryInfo(
        "ERC20TokenMetadata", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "40b61fcc362b84b7b8f5b45403faaac2ded0048c": LibraryInfo(
        "ERC20WithMetadata", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "6f5320de16c71dbf2d08b478bcae89a7c8cfe0e0": LibraryInfo(
        "ERC20Migrator", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "163a9d74ebf7a2cc7f910697d513585918f276e7": LibraryInfo(
        "SignatureBouncer", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "bc64e7383ee9e61b613c0aa77c38e4173b727986": LibraryInfo(
        "SignedSafeMath", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "5bc207b44f8ed1bf37ed702d8785882f6eb3277a": LibraryInfo(
        "TokenVesting", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "63f538b47a22324fed11f97b993e48a18d32b522": LibraryInfo(
        "SampleCrowdsaleToken",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "18ac17a25a4dfe3748f013b5e1acd2e638495cd8": LibraryInfo(
        "SampleCrowdsale", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "858f334ed2c08da2e605ab04db4d526ede537cd9": LibraryInfo(
        "SimpleToken", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0"]
    ),
    "b511b2fa36bea37c2840edc1be130612d949daed": LibraryInfo(
        "ERC165", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "ef087ed4bf42cc143bba6361e99f5d965c5209a3": LibraryInfo(
        "ERC165Checker", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "89b41dcad369ddf9289dd5bb640703e5e19805bf": LibraryInfo(
        "IERC165", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "8f78aa0fbc5f33696eba1aa5999f0367ccbe4b29": LibraryInfo(
        "Pausable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "294fd705d0a1c8e94cce6774f9f0275538787670": LibraryInfo("Math", ["v2.1.1", "v2.1.2", "v2.1.3"]),
    "ff5489b53ba0a4f650a926519ed6745ff910f7a8": LibraryInfo(
        "SafeMath", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "397b543dc2df14ccc410e0e472228aef1279e096": LibraryInfo(
        "Acknowledger", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "85458728ded749f7a0cb0417b4e6608c6fc04ca7": LibraryInfo(
        "AddressImpl", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0"]
    ),
    "8b9f37cdbcfeb15a883ad849d9868379469b94b4": LibraryInfo(
        "AllowanceCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "65eb147c8b702f4742f2325c5774f1f87bca413d": LibraryInfo(
        "ArraysImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "352bf73276ce2e422b715010bbb26a7dea1c060c": LibraryInfo(
        "CappedCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "2f63c91f090d3cf53ce96db8800692c34c53ba41": LibraryInfo(
        "CapperRoleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "e43d3f784551e1eca9b046aff7dd1746ca1e53eb": LibraryInfo(
        "ConditionalEscrowMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "249d26fc0d08c342aedec0b9d92cc74e31d97db7": LibraryInfo(
        "CounterImpl", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "e063b808e89ecc3de5c4bbc9c919ffa7d7301b8b": LibraryInfo(
        "CrowdsaleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "261bee63890ac92d183103eb06aa9e6468d00af7": LibraryInfo(
        "ERC20DetailedMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "a6d03a12f085621702ec2abe355799a5e60980fa": LibraryInfo(
        "ECDSAMock",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
        ],
    ),
    "97bcc379f499053394cb9b39baca0b5bd2c95f3b": LibraryInfo(
        "SupportsInterfaceWithLookupMock", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "e3f94dff17a0ddffe91cce083b0ab7da1ca407f8": LibraryInfo(
        "ERC165InterfacesSupported",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.2.0",
            "v3.3.0",
            "v3.4.0",
            "v3.4.1",
            "v3.4.2",
        ],
    ),
    "ce2f042f44149297411c63b1656a7aed7c351281": LibraryInfo(
        "ERC165NotSupported",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "c8c6b08e59408716543fdf833bfdd2a46d5e9042": LibraryInfo(
        "ERC165CheckerMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "cc59e5ee83e2ac3c54a9faf63f95c3c7db171e66": LibraryInfo(
        "ERC165Mock",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "d9b73968b741d5cd53aaa7ac879f736785c91141": LibraryInfo(
        "ERC20BurnableMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "03703594ba3bb7a29f8c457c8485de1f768c430c": LibraryInfo(
        "ERC20MintableMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "06a59988de5e175074dfd61846655d8ceb6aabb0": LibraryInfo(
        "ERC20Mock", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "7c599fc3da0043e6e8a27890071a64e581e9491c": LibraryInfo(
        "ERC20PausableMock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0"]
    ),
    "cdf48b32e8a2040fa1785ff4006015ae3621620b": LibraryInfo(
        "ERC20WithMetadataMock", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "d1d60fd9b13a8685ab6f8aa87048c6e0a67d1c27": LibraryInfo(
        "ERC721FullMock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0"]
    ),
    "6944978f728b1665abaf2da7ba86b5428e99dba2": LibraryInfo(
        "ERC721MintableBurnableImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "bb08f27cff0b19ef4adf183eb68d1e2ad2664ba7": LibraryInfo(
        "ERC721Mock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0"]
    ),
    "e51473b4de0d0cc41702f42d615f4d0e27789c60": LibraryInfo(
        "ERC721PausableMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "de3c52bb67df9b1e74f88dccf8ddacad748a91bc": LibraryInfo(
        "ERC721ReceiverMock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "b9f98976e3f3bb053a1d6ac241b4e13dce74244d": LibraryInfo(
        "EventEmitter", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "ebb254073b372b3a28ea94e56212bb41ff372386": LibraryInfo(
        "IndirectEventEmitter", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "9dcc5fe734a4d420457384896568ef817dda942f": LibraryInfo(
        "Failer", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "06096854e33cbf52e2704e3f87d107c58f52d145": LibraryInfo(
        "FinalizableCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "f7a220e190e202e59e7ed83e8d93ebb8f676d3a5": LibraryInfo(
        "IncreasingPriceCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "48221c607b28f7ff67eb496dccaac552e2e4b80c": LibraryInfo(
        "IndividuallyCappedCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "a1780e67e3aeed1cb9493ffe00e2840fd85e5b52": LibraryInfo(
        "MathMock",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "811b3f5f798d1bd67cb4351ede94b40a96251450": LibraryInfo(
        "MerkleProofWrapper",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "f19bf654847043124db5ee412a4926fd45ece93c": LibraryInfo(
        "MintedCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "80c381c593821fb47db89d55e26bc66eb3b9815b": LibraryInfo(
        "MinterRoleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "46c4d8c42833e483c06badecf3ef4870eeeef4c0": LibraryInfo(
        "OwnableInterfaceId",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "799e7db4e23a6cef4a8d9642ae4b5cd2d7eaa3c1": LibraryInfo(
        "OwnableMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "3f555df97ee448ff10299cb97da90b3f3b38a0d2": LibraryInfo(
        "PausableCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "351955623b3a5ba04402dc84132efe3bd36d81d6": LibraryInfo(
        "PausableMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "39f9b49623e98258a14b689f719e4c9e39960a58": LibraryInfo(
        "PauserRoleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "df64a5fc7bb156be6d151d1853a4717c501fe981": LibraryInfo(
        "PostDeliveryCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "f2bc5891107b19ad4a9e2bcc9eb78651c23d8536": LibraryInfo(
        "PullPaymentMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "4cc249e1ae70127d1438dd7e52e00c76a0714e7a": LibraryInfo(
        "ReentrancyAttack", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "f9a7437047cc110b3d7c7886c537e63c88d58f77": LibraryInfo(
        "ReentrancyMock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "9baeb425b432c40949ab0d772f3673356433e5fe": LibraryInfo(
        "RefundableCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "3a1327b39ea8686de5d4eae4488f464238196ba8": LibraryInfo(
        "RefundablePostDeliveryCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "7c102c2c0df13f6306a1491d1dab99216519efe4": LibraryInfo(
        "RolesMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "9172a3718949c08ec82487993301e25b4e988338": LibraryInfo(
        "ERC20FailingMock", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "05db7acd560f57643755be95bbbafe39db03db36": LibraryInfo(
        "ERC20SucceedingMock", ["v2.1.1", "v2.1.2"]
    ),
    "e0f626fb634ae0401a38f07d5562a7e66339e42e": LibraryInfo(
        "SafeERC20Helper", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "5cb3f28de3e654931732a980fd663fecc4a1081a": LibraryInfo(
        "SafeMathMock",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "f8da5f69fc930b78d4d5ea2eac5147aa2b6ea5d4": LibraryInfo(
        "SecondaryMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "991f87c81fa1c7f853b0d77766c2d897e6f0f084": LibraryInfo(
        "SignatureBouncerMock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0"]
    ),
    "8ce412c8cd9286e85b7c28e3c3ed644bacaf39d8": LibraryInfo(
        "SignedSafeMathMock",
        [
            "v2.1.1",
            "v2.1.2",
            "v2.1.3",
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "47eee6b2d10bb21084c63f29a263bbe01173cac4": LibraryInfo(
        "SignerRoleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "07b4e8cb7b3f12b92375f0a93c3eb2eb23aaaf60": LibraryInfo(
        "TimedCrowdsaleImpl", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "20f40b25fbd13c483becd042f5bf06e98b7bfe33": LibraryInfo(
        "WhitelistAdminRoleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "148d4321f050aa8ff5724607bf13e1d4b55ca33c": LibraryInfo(
        "WhitelistCrowdsaleImpl",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "9986f2f41f56c43eb27b92c0547ac10e02d052fc": LibraryInfo(
        "WhitelistedRoleMock",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "d918cc9ba3b27a39e2e0a05c8be5b5fb07117521": LibraryInfo(
        "Ownable", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "f682e6ff4e928c190146ce6abc350197ee6dd9b2": LibraryInfo(
        "Secondary", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "015f648298c32f15f9b2e3dbda148e05c9f29ec1": LibraryInfo(
        "PaymentSplitter", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "feb2a352c4a8597f50e0c7f7caec4787e8a04571": LibraryInfo(
        "PullPayment", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "1236e7cc69efcf915b7ce81450fa7c8f013d66e3": LibraryInfo(
        "ConditionalEscrow", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "a1b2c0241d1f22d1d32c71415293e2357ce9754c": LibraryInfo(
        "Escrow", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "6e2e6ee47de4500756716fbf8943f13b29b2771e": LibraryInfo(
        "RefundEscrow", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "a08504b8c3c127e9f3a15cdd588573058a60acca": LibraryInfo(
        "ERC20", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "3bcfc9705f5bcab4583eebcaefd66a89e28e23c7": LibraryInfo(
        "ERC20Burnable", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "566bcf581eb9ed38c8c2b2e90cace8b78e7e2acb": LibraryInfo(
        "ERC20Capped", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "77ba7d78c25254fb6a22f0a92fa04b95a8ba4ef0": LibraryInfo(
        "ERC20Detailed", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "d602a9c5786af67ef6bb2d431651081d76dcdd89": LibraryInfo(
        "ERC20Mintable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "563404ae3ad9decba0f1f12d78aff9234a84bab5": LibraryInfo(
        "ERC20Pausable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "b3e5be0b3f985e92fe1f9146d8133f70c7370c9c": LibraryInfo(
        "IERC20", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "bdd10fc95fdb3e43dcb6f50c5a790526eb2339a5": LibraryInfo("SafeERC20", ["v2.1.1", "v2.1.2"]),
    "1bc7268e369e6f66cae9a346a3be4200fb9ab2a2": LibraryInfo(
        "TokenTimelock", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "f5495923e256fc4aa541fe592c69f9c6a49d09b1": LibraryInfo(
        "ERC721", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "bff0ac152d4f9d6016939cc8a2f0abd3952a5cff": LibraryInfo(
        "ERC721Burnable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "14d60ce0ee22fe6cc17a67f827f2d6405fde45fb": LibraryInfo(
        "ERC721Enumerable", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "1c5e388a06c8bc5e4ebbd264403d229c79cb538b": LibraryInfo(
        "ERC721Full",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "dc6488481efeb3f0a3fe4012e44cc9630de20454": LibraryInfo(
        "ERC721Holder",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "57d6282eac3ccb6f9934d1d2341098cd94888d34": LibraryInfo(
        "ERC721Metadata", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "bf266ddbcc0c703ec528a3589125187209ecfa0b": LibraryInfo(
        "ERC721MetadataMintable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "feb0e24e8119875a567c7f63ae626229e989ba6b": LibraryInfo(
        "ERC721Mintable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "4e7a7464f14927dcd4ac1c4c80c1416a532a1762": LibraryInfo(
        "ERC721Pausable", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0"]
    ),
    "181645ad9bfe9ec844972ef6c3335fd0ea4a350e": LibraryInfo(
        "IERC721", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "5eeb659e05046a4f4fc1b998fca1960305af320d": LibraryInfo(
        "IERC721Enumerable",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "49a0645eb5f2c78e85729f78b6e46b5daba24d94": LibraryInfo(
        "IERC721Full",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "80912b3e9ab6eb4d3fc3d42d7a49810811a8067d": LibraryInfo(
        "IERC721Metadata",
        ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"],
    ),
    "54be7bd4bad6dd7473376057523b9d49cb448688": LibraryInfo(
        "IERC721Receiver", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "7a16711320090635c8beb50e1328a501c188f888": LibraryInfo(
        "Address", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "5176d91de61a03d02be10f24b2a03fdbc6683a68": LibraryInfo(
        "Arrays", ["v2.1.1", "v2.1.2", "v2.1.3"]
    ),
    "2b1f3555fce0551e87ee87794b27941844b305ed": LibraryInfo(
        "ReentrancyGuard", ["v2.1.1", "v2.1.2", "v2.1.3", "v2.2.0"]
    ),
    "8bf62064d4d5f310f90c3b0260f35ed98a945899": LibraryInfo("ERC20SucceedingMock", ["v2.1.3"]),
    "7fc61c5c87173431d88d59b7645b20b7a5a30a13": LibraryInfo("SafeERC20", ["v2.1.3"]),
    "26d3b2bc6fb00cba01f3fc93926107bb8547dfca": LibraryInfo("Crowdsale", ["v2.2.0"]),
    "dbbddfca9a9d822603879d0b26c9a87f896185e7": LibraryInfo("IncreasingPriceCrowdsale", ["v2.2.0"]),
    "0b1275c2973bc9904a4719496518db986e75f0d9": LibraryInfo("TimedCrowdsale", ["v2.2.0"]),
    "3181a686cc87d9773617f11e6e744a8ef4cd1485": LibraryInfo("WhitelistCrowdsale", ["v2.2.0"]),
    "b44caa5b9a40b460428ea5145c3b516263196f9c": LibraryInfo("ECDSA", ["v2.2.0"]),
    "a49a652a900af135636686be65e24c59b562f1f2": LibraryInfo(
        "Counters", ["v2.2.0", "v2.3.0", "v2.4.0"]
    ),
    "24b08de6151fdf941a10bb1dec241f27958feee3": LibraryInfo(
        "ERC20Metadata", ["v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "ced0258d0b0d50383252c1a10e11e72c54d8f854": LibraryInfo("ERC20Migrator", ["v2.2.0"]),
    "d6493fab55286955839b4d6d279bda02b11c3644": LibraryInfo("ERC20Snapshot", ["v2.2.0"]),
    "83dc70f4ffa7ca8b4bb744aafe520ca5813e5df5": LibraryInfo("SignatureBouncer", ["v2.2.0"]),
    "df185ebc2fa12c378e5015bd475332756504f60d": LibraryInfo("SignedSafeMath", ["v2.2.0"]),
    "4fb66323fe71536c1796582d32bfcabf6716ff65": LibraryInfo("TokenVesting", ["v2.2.0"]),
    "bdfbcc3f8bc59328aa6ab0d4a20d24270492f9a2": LibraryInfo("ERC165", ["v2.2.0"]),
    "2d2ca1d7fb9b959879a30f3a36a6ff381be7a50b": LibraryInfo("ERC165Checker", ["v2.2.0"]),
    "d0b3500ec510385e5f14da45b3f72cbecf2d0e1a": LibraryInfo("Math", ["v2.2.0"]),
    "a38f7d36cea19217092f7ee679308e368ec9a9bc": LibraryInfo("SafeMath", ["v2.2.0"]),
    "b65922943e3104021a6f39825a9ad792d6c06202": LibraryInfo(
        "CountersImpl",
        [
            "v2.2.0",
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "0568279ce96d91ad7a4dbba12201003893a914a0": LibraryInfo(
        "SupportsInterfaceWithLookupMock", ["v2.2.0"]
    ),
    "191327eebe6456d41be46d29262f424cb14cdaa4": LibraryInfo(
        "ERC20MetadataMock", ["v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "ec24556da2b236f33be4263e76835c6f7b07c579": LibraryInfo("ERC20Mock", ["v2.2.0"]),
    "b1f5209f1503fb7b95c1e274a4605961263658d6": LibraryInfo(
        "ERC20SnapshotMock", ["v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "600c8541c63ee789fdef9c5c2901eabfcefc40c1": LibraryInfo("ERC20ReturnFalseMock", ["v2.2.0"]),
    "375ddc80a306ac6fd622911e87a929e4317bc498": LibraryInfo(
        "ERC20ReturnTrueMock", ["v2.2.0", "v2.3.0"]
    ),
    "5ff30663aecee0ab6ec3bc9342d9a21cb64e1ad3": LibraryInfo(
        "ERC20NoReturnMock", ["v2.2.0", "v2.3.0"]
    ),
    "c6eeb63f9350a6293d3cd162768c72f84899efac": LibraryInfo(
        "SafeERC20Wrapper", ["v2.2.0", "v2.3.0"]
    ),
    "5ec72a2da405c23f8b5610b9e7b0e4bb586a904c": LibraryInfo(
        "TimedCrowdsaleImpl", ["v2.2.0", "v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "3086bc6470bdddb0bccf23d803130a76067fee7a": LibraryInfo("Ownable", ["v2.2.0"]),
    "b83b3645b9107f5cbc95e2afbb57f6002e3e72d7": LibraryInfo("PullPayment", ["v2.2.0", "v2.3.0"]),
    "9ab9c8709262c8ac99601051ce5c5d1ddd2950a6": LibraryInfo("ConditionalEscrow", ["v2.2.0"]),
    "61dd244ce7b91aab023abcd5e64e90a7c2d363dd": LibraryInfo("Escrow", ["v2.2.0", "v2.3.0"]),
    "4a5447519ca8bb2d82a79bd5b0b9b0792bba23a8": LibraryInfo("RefundEscrow", ["v2.2.0"]),
    "c8df889cca25546f32a258b75f263fff3be529e9": LibraryInfo("ERC20", ["v2.2.0"]),
    "21b260d15766f58e0590ea216fb5db31db4788e9": LibraryInfo("ERC20Burnable", ["v2.2.0"]),
    "490f2847cf60a16df023549e03e6ff6a16f01f9e": LibraryInfo("SafeERC20", ["v2.2.0"]),
    "67ec2c098cb4626d76ee8762f555edadeaf863c8": LibraryInfo("ERC721", ["v2.2.0"]),
    "84f02d651f97b0225a3ad08eda8e51c73fca5eda": LibraryInfo("ERC721Enumerable", ["v2.2.0"]),
    "b3f7f407fd76e2dc2ee39174a1f483e5864bb7b7": LibraryInfo("ERC721Metadata", ["v2.2.0"]),
    "4e241f646d96f095386eae6a7a5f13e6dac682f1": LibraryInfo(
        "IERC721Receiver", ["v2.2.0", "v2.3.0"]
    ),
    "5d932009fc8f204b32e2ff3b795b5a4016ba8856": LibraryInfo("Arrays", ["v2.2.0"]),
    "97ad171eccfd6d686444cb1a096ca32c1e081173": LibraryInfo(
        "Roles", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "12d3a805c82a503a32584116eaa679c58663182e": LibraryInfo("CapperRole", ["v2.3.0"]),
    "920fb014fdab17d9962e4a051ecb05e0346803c4": LibraryInfo("MinterRole", ["v2.3.0"]),
    "0755ddb27f6aeb4095c5fa52223c6c321f634f37": LibraryInfo("PauserRole", ["v2.3.0"]),
    "f2fdc6353650ca2a99350d5668fec6460865baf0": LibraryInfo("SignerRole", ["v2.3.0"]),
    "a7420e74fc819c039143c4fc4060b3f8233aed23": LibraryInfo("WhitelistAdminRole", ["v2.3.0"]),
    "7731004a855c8698643498ec733dfc528ab5e9af": LibraryInfo("WhitelistedRole", ["v2.3.0"]),
    "362c8c4f6c21345efab16b43ac7a6dda826ef8bb": LibraryInfo("Crowdsale", ["v2.3.0"]),
    "3a548446ff8b86dd7fc634446568f9549949d0aa": LibraryInfo(
        "FinalizableCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "4109c79f50836cd29d813afbeeed549745e579c9": LibraryInfo(
        "PostDeliveryCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "8d80a124fdfc163f1856b30d54475338d1995fa2": LibraryInfo(
        "__unstable__TokenVault", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "9dc3b6cc96b6bcf6dcdeb91ba4c732a8f7da0336": LibraryInfo("RefundableCrowdsale", ["v2.3.0"]),
    "b123691e7215b1777026a26b72965372b355fc71": LibraryInfo(
        "RefundablePostDeliveryCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "18869bdf9d3a93150d1e0edcb1db4a85ee23e28c": LibraryInfo(
        "AllowanceCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "6e75e6262faa2337d43ec1066f50e2fd71409199": LibraryInfo(
        "MintedCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "33eb8c2e2ae6b95c6cf58d3c9c06587e7ca2bf3f": LibraryInfo(
        "IncreasingPriceCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "e8bfd676822015708c097b2064fc5d898f45c5fd": LibraryInfo(
        "CappedCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "8c2f617d1f49cb4fbef87748d2cf71aed74d515a": LibraryInfo(
        "IndividuallyCappedCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "9d143c684d3650ae76ef4cc89c043eb8c3680445": LibraryInfo(
        "TimedCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "6080c9c622f05b4a6439d1c98b67333b5edb9bb9": LibraryInfo(
        "WhitelistCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "791cc5d0ccd96d4d7cea297d4dd4282a2e03e30e": LibraryInfo("ECDSA", ["v2.3.0"]),
    "4737e887fd1bc839b8b8cf2f10f02eaacda8294d": LibraryInfo("MerkleProof", ["v2.3.0", "v2.4.0"]),
    "b7ed70197dc7c1b670f34cf2e3b4e58865383cd9": LibraryInfo(
        "ERC20Migrator", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "1b898dc4c40ad6e77b5e7600958f0675d6182077": LibraryInfo(
        "ERC20Snapshot", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "13b02c8c4a18591bc141c84d4f390a470699efee": LibraryInfo("SignatureBouncer", ["v2.3.0"]),
    "e121f6ee965082a37437175f7f7de7327fc7f6ec": LibraryInfo("SignedSafeMath", ["v2.3.0"]),
    "34333c9d9d0dd9cad48ced9b7ec9f16499d9e51f": LibraryInfo(
        "TokenVesting", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1", "v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "0006db197a30a83123ae42b1412b9eb36e42a28a": LibraryInfo(
        "SampleCrowdsale", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "c09017218a635de03a5da5e72c0ca29453a3f119": LibraryInfo("ERC165", ["v2.3.0"]),
    "65df18d3f80dc6e25c7b9261139254c041565eaa": LibraryInfo("ERC165Checker", ["v2.3.0"]),
    "82aff27a106fe353c21f329d0884dba69a89e5f8": LibraryInfo("ERC1820Implementer", ["v2.3.0"]),
    "7b1e6947bc70edd40153bcea559844c17eb80236": LibraryInfo("IERC165", ["v2.3.0"]),
    "a4a4c4e1884a9ecff9a3be99eacc783c290bf7e5": LibraryInfo("IERC1820Implementer", ["v2.3.0"]),
    "6fe4d6ebe9da8d97a48c7be4cb30aaabb3ff405c": LibraryInfo("IERC1820Registry", ["v2.3.0"]),
    "ae0db82d81525d22cdc433cef124addd50430fc5": LibraryInfo("Pausable", ["v2.3.0"]),
    "6b96a25ebec0776be5318fbff49d141d73f4f5de": LibraryInfo(
        "Math",
        [
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "2a829cf20030b8d3de8ac9873f0beaca3cad1f4e": LibraryInfo("SafeMath", ["v2.3.0"]),
    "7c044669d66a8d69734c5f828a50d2ebd53f6bbd": LibraryInfo(
        "SupportsInterfaceWithLookupMock", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "7b97383d271f6b4cf1373d76ee256ba3028f24ea": LibraryInfo(
        "ERC1820ImplementerMock",
        [
            "v2.3.0",
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "95998f85eb3757d7b010f9d7c1480a92d9016d92": LibraryInfo(
        "ERC20Mock", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "30b598e64b3ea2b9915acaf629b2d0e4a2eb66ac": LibraryInfo(
        "ERC721ReceiverMock", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "e092e16bb0e17e23ca9e1b8c1521cfb386697e2a": LibraryInfo("ERC777Mock", ["v2.3.0"]),
    "53a0001a2ebd03b5203549fa6c6c80cc9697187e": LibraryInfo(
        "ERC777SenderRecipientMock", ["v2.3.0"]
    ),
    "ca4b8cacced7f06ec8ac865f7be0d5bf1b1957ff": LibraryInfo("ReentrancyAttack", ["v2.3.0"]),
    "068676df02968b7b9e9b4d3b7f69155a9f70a13e": LibraryInfo(
        "ReentrancyMock", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "9124b8c0668411c9dfee424d0bb9ae6e8f7706e2": LibraryInfo("ERC20ReturnFalseMock", ["v2.3.0"]),
    "257829241097f5fd720b48aa5025a7e972b0bb30": LibraryInfo("Ownable", ["v2.3.0"]),
    "eefbd0e574c1afa621b60d5c0060ad123e094988": LibraryInfo("Secondary", ["v2.3.0"]),
    "cf6cc9c70bb5ee318b5ba3588e9f2c4f34cca72d": LibraryInfo("PaymentSplitter", ["v2.3.0"]),
    "f8d97ab19910043c2be57dfa599cd98b2e79c0e8": LibraryInfo(
        "ConditionalEscrow", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "cef9149e1ef5098f9600007ec477b01ea5f41140": LibraryInfo(
        "RefundEscrow", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "5e3eabc1f7f46c3375a3d8eb4ab618ea528254c4": LibraryInfo("ERC20", ["v2.3.0"]),
    "9f0cfbf4cf9505829c19bf3698aa3a87660ce1d4": LibraryInfo("ERC20Burnable", ["v2.3.0"]),
    "f6d6fbf05185ca026c9ccf4eab910054069c3f8f": LibraryInfo("ERC20Capped", ["v2.3.0"]),
    "a9ef7428ed0d036ab79ddd21ae9b95da666634fb": LibraryInfo("ERC20Detailed", ["v2.3.0"]),
    "cb12ca8d883bb3ad8317c61b2e7251221def665f": LibraryInfo("ERC20Mintable", ["v2.3.0"]),
    "0f194824b2052c308c52ec5cae790adea7c64c57": LibraryInfo("ERC20Pausable", ["v2.3.0"]),
    "3efeef33c00f8c7513b55015ee54e6235bb0b668": LibraryInfo("IERC20", ["v2.3.0"]),
    "7f3606ceb7a5ca3d169607f28d825b7844d8f6ed": LibraryInfo("SafeERC20", ["v2.3.0"]),
    "54bbee45e99d6502f0c9b5be1b80d4bbe3786d94": LibraryInfo(
        "TokenTimelock", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "11fc4d574650f2b1c58366124832c3409c78413a": LibraryInfo("ERC721", ["v2.3.0"]),
    "205f8e867ab267c38e439b791c1e1bd1d8ca88c7": LibraryInfo("ERC721Burnable", ["v2.3.0"]),
    "9b8256d1597bccaec572a77db88f059f58df9345": LibraryInfo("ERC721Enumerable", ["v2.3.0"]),
    "66f22e50f77d448e975e59f871645e6abf6d1cf8": LibraryInfo("ERC721Metadata", ["v2.3.0"]),
    "743b6405c190d6966e1284622dc0bade6c9cb40f": LibraryInfo(
        "ERC721MetadataMintable", ["v2.3.0", "v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "628a4855f3a319fc3280111e4747b4faa9ac39a5": LibraryInfo("ERC721Mintable", ["v2.3.0"]),
    "d5e1935a6ff55517a209f36ed99d5998837c9e4f": LibraryInfo("IERC721", ["v2.3.0"]),
    "640289cb3557be343a7520230cd1c3d31961d3c2": LibraryInfo("ERC777", ["v2.3.0"]),
    "532858b09be39df731d0f660c1c8df677d90663e": LibraryInfo("IERC777", ["v2.3.0"]),
    "3c3e0a7eeab6fb60705ad74295fc20d947d4fd38": LibraryInfo("IERC777Recipient", ["v2.3.0"]),
    "7c644be4848da35aed4b1b1358c79d273c5eb2c3": LibraryInfo("IERC777Sender", ["v2.3.0"]),
    "862f5b1732442b00bc2bd40124ebbfc93e506b73": LibraryInfo("Address", ["v2.3.0"]),
    "ffe0c2e7651f57976a4875cd95580dfc0a012a2a": LibraryInfo("Arrays", ["v2.3.0"]),
    "00fd45355e275a2ed1c1eb0b3b2fc82786dcac5b": LibraryInfo("ReentrancyGuard", ["v2.3.0"]),
    "f5f947f1c918d8d1ece09da651c3248f66cf7e4d": LibraryInfo(
        "Context", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "2e44800ce075b20ea3c20d1e62300384dfe2c517": LibraryInfo(
        "GSNRecipient", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "c5aee0ebb7cd74d8527a5db5954b364b863603d1": LibraryInfo(
        "GSNRecipientERC20Fee", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "99159b6dfffe5ffb4c973a9645385542d26aeaa4": LibraryInfo(
        "__unstable__ERC20PrimaryAdmin", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "a4073980c6f85544223a230d9dc9391f1b0dc311": LibraryInfo(
        "GSNRecipientSignature", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "d914062eb6557699da04d907e2b70c24de94bd12": LibraryInfo("IRelayHub", ["v2.4.0"]),
    "3e206957fb817eb0ec41dc08053084c29a6a061b": LibraryInfo("IRelayRecipient", ["v2.4.0"]),
    "43710cb6060b92e5f845d7c76ed4ab1f85f7cc86": LibraryInfo(
        "CapperRole", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "4a5a3fca54b8b8b1997614b1dd3b408a964c538d": LibraryInfo(
        "MinterRole", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "76bbbe6b0782ad22a92c56058b01b89ae789b599": LibraryInfo(
        "PauserRole", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "d4e83a7891c65c3ed3670a978bb76b634584af20": LibraryInfo(
        "SignerRole", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "6cc6766baef98a700e8e38821ae2aa15cbc31062": LibraryInfo(
        "WhitelistAdminRole", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "71c272ca2459bd2e5648c31cf3342109274dc265": LibraryInfo(
        "WhitelistedRole", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "bb5bc67bb08af53d6db7d3c6bfca4dfd34e5e574": LibraryInfo(
        "Crowdsale", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "c73846163f45573292c9e7281471658d480d83ba": LibraryInfo(
        "RefundableCrowdsale", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "041e87ca76fd2207ef3cf4936ec0205204be6b96": LibraryInfo(
        "ECDSA", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "0000d7516560f14246e909e2efa04fab08aa639c": LibraryInfo(
        "SignedSafeMath", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "b002d3ff71af2317f8c44c7098c5e12814bba92c": LibraryInfo(
        "Strings", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "cef172a9650a72ad1bbc8aa71d6c5e755f0b49bf": LibraryInfo(
        "SimpleToken", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "150947d54d2a71dae3b56af334766eb70e6253a4": LibraryInfo(
        "ERC165", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "a7c76ea626e3f0e494df9149c8e40ac8fb90d240": LibraryInfo("ERC165Checker", ["v2.4.0"]),
    "0f2bb06c58e981260a4204795f24203a365c2737": LibraryInfo(
        "ERC1820Implementer", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "67b2092d07fad864c8fe808b9c3ca3e8749ef8a2": LibraryInfo(
        "IERC165",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "cf18bfd2ac9bb0e6f31e2e0169bcf7812b48d020": LibraryInfo(
        "IERC1820Implementer",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "c6d7a58fa8e4408d90bf4dba2251c7f384442e61": LibraryInfo(
        "IERC1820Registry", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "1d1a1e6a2b8373a0f9c12fecb97e9e9e2f5565bb": LibraryInfo(
        "Pausable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "40c5df80b4b5cbba8434b7662078aa2f7bd11703": LibraryInfo(
        "SafeMath", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "7e7979f1b224b9a2f1521c2e7ee6269e86c192da": LibraryInfo(
        "AddressImpl", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "d2953944bb76616ec71f7ac0973f4a2c7735e3f5": LibraryInfo(
        "ContextMock",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "b9f88ead37062ca195d2a397eca7462b23377705": LibraryInfo(
        "ContextMockCaller",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "e4e81b34ffc158b871c398905044eaa407b53309": LibraryInfo(
        "ERC20PausableMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "1d5e75b5b0c6d5a5411479d0c5922cbc23b88935": LibraryInfo(
        "ERC721GSNRecipientMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "ccb9f10bcbdd9b08e3be1ddcea53285c2edfbbac": LibraryInfo(
        "ERC721Mock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "f6dd2052f9728379c16000c51866baa667ae8ba4": LibraryInfo("ERC777Mock", ["v2.4.0", "v2.5.0"]),
    "40c2c74b3acb1d4f2701bbc1726c54e7b93d879f": LibraryInfo(
        "ERC777SenderRecipientMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "a6ebcc719baf42b346ce99ce787a988dffafbe67": LibraryInfo(
        "EtherReceiverMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "31c735b3a0f5aca4dbcae3cd833d5327d77020e7": LibraryInfo(
        "GSNRecipientERC20FeeMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "f951aa42da5cb767b2d25af86911f06cd5558981": LibraryInfo(
        "GSNRecipientMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "35ec5d4c73fddcf8a5aaf5757ef1af99352b3e7f": LibraryInfo(
        "GSNRecipientSignatureMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "d3525012d52c3d06a22bb704ada33f21c0256dc8": LibraryInfo(
        "ReentrancyAttack",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "860bdd56a5ddf01ae3557917163d7c9dc8de8ee2": LibraryInfo(
        "ERC20ReturnFalseMock",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "ae01681cc37d58ab8052869e687f215e6cb8d0cf": LibraryInfo(
        "ERC20ReturnTrueMock",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "93af43acbe7d5b909433810d28f2ac6826dd1d91": LibraryInfo(
        "ERC20NoReturnMock",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "d09209d71a33bf114bf1adcec684c64deb010de4": LibraryInfo(
        "SafeERC20Wrapper",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.2.0",
            "v3.3.0",
            "v3.4.0",
            "v3.4.1",
            "v3.4.2",
        ],
    ),
    "3d00f6d348841ae204c485cda3c4c2816af76957": LibraryInfo(
        "StringsMock", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "d1523aae49fb6f1896f49e590b6f51039e4bdd72": LibraryInfo("Ownable", ["v2.4.0"]),
    "2fce93f9d6faa205cd88c0a09bd9f76fc5330932": LibraryInfo("Secondary", ["v2.4.0"]),
    "0d32d5cabbfa9f420623b256dc5fb3494ed22769": LibraryInfo(
        "PaymentSplitter", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "99e22b366e81118ef4050f8f5f75962e73330c73": LibraryInfo(
        "PullPayment", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "4562c170bc9809fa46e6666f9728e8e61dd33f72": LibraryInfo(
        "Escrow", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "626414a459336b3ac497b8e49fa22f1f0abf1b92": LibraryInfo("ERC20", ["v2.4.0"]),
    "950167661be5dc085fba4c584183bbd83a29eee7": LibraryInfo(
        "ERC20Burnable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "38d0818e3e974224e2fbabbd73c57eda95034984": LibraryInfo(
        "ERC20Capped", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "e406b324425fe7c3f7c5589e06dbea4796503de1": LibraryInfo(
        "ERC20Detailed", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "3f15c8af26605011c8d5de1ce87ab8fd0ce60ea7": LibraryInfo(
        "ERC20Mintable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "09071ee20d5607366d247ff1fa9aaaa46d606dd8": LibraryInfo(
        "ERC20Pausable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "a8466bda6a100f8073131ee60f1f55f39cc79715": LibraryInfo(
        "IERC20",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "2c19d3f26dbfbf3d39f50dd735fe0fe5b5e6cb69": LibraryInfo(
        "SafeERC20", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "53de48de263bd917431b935fe6733716efaa53aa": LibraryInfo("ERC721", ["v2.4.0"]),
    "f6798a7bd8cd9f0f9315ecf200035b4c1b27652b": LibraryInfo(
        "ERC721Burnable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "5287c032e953f49cbead7d8e8dfb5013fdbea35a": LibraryInfo(
        "ERC721Enumerable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "32a640d5908aa379be7abda1424894a0ed5cb389": LibraryInfo("ERC721Metadata", ["v2.4.0"]),
    "0465da94cef491f15c1f0cf03ab35ba5f57c2e53": LibraryInfo(
        "ERC721Mintable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "652b0218b8ce2fa84fc1489346eb4f8ba6be36fa": LibraryInfo(
        "ERC721Pausable", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "dbb96f95f55be6a05475b97ef7c35bd3e93ab4ed": LibraryInfo(
        "IERC721", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "f4b123f5b40878b70f02476c2e17a144bf88e1a2": LibraryInfo(
        "IERC721Receiver", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "fc247ca5c3f2ce5dfe65d307d34461c314f07225": LibraryInfo("ERC777", ["v2.4.0"]),
    "70795fc39191bc51871b45a31c12b3bfb7a8d95f": LibraryInfo(
        "IERC777", ["v2.4.0", "v2.5.0", "v2.5.1"]
    ),
    "923531fc7154edb1c04430faa466f2fc21be91b5": LibraryInfo(
        "IERC777Recipient",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "91df3b8cb635ee73d073bb41677b30cca16cdfaa": LibraryInfo(
        "IERC777Sender",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "671c527f68ac3d8c6793881d78179da4ad394eba": LibraryInfo("Address", ["v2.4.0"]),
    "0bf7ab409d936c5f8868bfbcdcd40635b2d5975f": LibraryInfo(
        "Arrays",
        [
            "v2.4.0",
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "e6a65bea2d5d2b3629bebed655e5f99ba6b5cb62": LibraryInfo("ReentrancyGuard", ["v2.4.0"]),
    "33fd40c136a0417ba1aca69c95440a6f6af396ee": LibraryInfo("IRelayHub", ["v2.5.0", "v2.5.1"]),
    "e60e312ee7de5b97f6b691d2aa22a754139c0174": LibraryInfo(
        "IRelayRecipient", ["v2.5.0", "v2.5.1"]
    ),
    "80635da095b81f3ac67980a810c197b175cd191a": LibraryInfo(
        "MerkleProof",
        [
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "2001957575c00b8d4f0d2e86da40374cc1f9b95c": LibraryInfo(
        "Counters",
        [
            "v2.5.0",
            "v2.5.1",
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "bee16f12e3d00612347f7716ac3dd919958f6ecd": LibraryInfo("ERC165Checker", ["v2.5.0", "v2.5.1"]),
    "b7ffce9048179efef559653bd0fe78e3dbf3ccc9": LibraryInfo("Create2Impl", ["v2.5.0", "v2.5.1"]),
    "ab5709072e811dc6892d9bea6dc2febc84c2eebb": LibraryInfo("ERC721FullMock", ["v2.5.0", "v2.5.1"]),
    "8eebc80db69e1dc9feea6f06833983578d4b3780": LibraryInfo(
        "EnumerableSetMock", ["v2.5.0", "v2.5.1"]
    ),
    "da3bb9482cc3fef975d4b940aa6a7a241620cddc": LibraryInfo("SafeCastMock", ["v2.5.0", "v2.5.1"]),
    "418be7dc23fea0fb0685acfcd0924205d309da45": LibraryInfo("Ownable", ["v2.5.0", "v2.5.1"]),
    "016a31280fdbbb2437d69d2d2077a7c6905c714d": LibraryInfo("Secondary", ["v2.5.0", "v2.5.1"]),
    "e54799317dc440001a42e881955539c39216f20b": LibraryInfo("ERC20", ["v2.5.0", "v2.5.1"]),
    "7f18034de8806b6e04a081d9139af0bafa7ebe28": LibraryInfo("ERC721", ["v2.5.0", "v2.5.1"]),
    "a8e2e47304e89ec12edb4796701610ca0545f690": LibraryInfo("ERC721Metadata", ["v2.5.0", "v2.5.1"]),
    "270b244803ef7871cc0ea9c7140c58b0cecc7121": LibraryInfo("ERC777", ["v2.5.0"]),
    "46d949813bed5d0c28d461308d29b801440d4b5a": LibraryInfo("Address", ["v2.5.0", "v2.5.1"]),
    "27cd94941b6e8368a47c3056f9881d9b777a12ee": LibraryInfo("Create2", ["v2.5.0", "v2.5.1"]),
    "3f0be66d5ab109f6f063a2f621e2a27f598e9c75": LibraryInfo("EnumerableSet", ["v2.5.0", "v2.5.1"]),
    "288ea0f7c464d6c209aedcb70702d40d055061a5": LibraryInfo(
        "ReentrancyGuard", ["v2.5.0", "v2.5.1", "v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "96b9d4c39c132847fe9878012875a60be6815d6c": LibraryInfo("SafeCast", ["v2.5.0", "v2.5.1"]),
    "d858e0f859c9a0007983f900e87377bc7b9db2d9": LibraryInfo("ERC777Mock", ["v2.5.1"]),
    "c50d4a4bdb1ae07acba0c1808a395989814eb11c": LibraryInfo("ERC777", ["v2.5.1"]),
    "b796dbdd6a4a193975d3e83a2705332b97d04c9e": LibraryInfo(
        "Context", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "26f098ad471cc55860f980fdb2a0e03e76124c5c": LibraryInfo(
        "GSNRecipient", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.1.0-solc-0.7"]
    ),
    "df2e4c908e0f63db31a061d6b1a88aa3ac5e4259": LibraryInfo(
        "GSNRecipientERC20Fee", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "f6e0a568a7b389b06da90d094cff83cb479ea60d": LibraryInfo(
        "__unstable__ERC20Owned", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0"]
    ),
    "250da0268e9484838d295b0a509683c70b9c2bcc": LibraryInfo(
        "GSNRecipientSignature",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "7db2684fb121525320f90ba363fb9d393c882c2a": LibraryInfo(
        "IRelayHub", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0"]
    ),
    "b59618fd7459ca78735d140104a33f746c87ca23": LibraryInfo(
        "IRelayRecipient", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.1.0-solc-0.7"]
    ),
    "f61364a0c94c546c2686fccf64fb00b7e6a238f5": LibraryInfo(
        "AccessControl", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "5d4b8f8c71145f3eea66f7436b857d639d294975": LibraryInfo(
        "Ownable", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "5ce37f6d78b690e78105d779c9c5f8b133b20713": LibraryInfo(
        "ECDSA",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
        ],
    ),
    "e2563eee26d163e13a84de12c231bad5bd9d07ef": LibraryInfo(
        "ERC165", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "bab56366523b8b4b46e5f4745d87d1c4925a4cd5": LibraryInfo(
        "ERC165Checker",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "e0902a009ac1aef60cb3f2396c3e0551cabe50e4": LibraryInfo(
        "ERC1820Implementer",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "8c1783f1553244438a69f197761338b573ea437a": LibraryInfo(
        "IERC1820Registry",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.1.0-solc-0.7", "v3.2.0", "v3.2.1-solc-0.7"],
    ),
    "299995a0dda5331bc9ee5b50a02caecae0ab2f47": LibraryInfo(
        "SafeMath", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "381c1c12d9d6ed7263d499568493801a2f9f6c98": LibraryInfo(
        "SignedSafeMath", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "b36bba5668b0585f8fd14a482b2b732245a71bbb": LibraryInfo(
        "AccessControlMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "ea494ccbabbb741ef48ad0ff5c085f91efcf3a3f": LibraryInfo(
        "AddressImpl", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "efab65e1bceef92614ebe4fbb8f9fb24482b6ed6": LibraryInfo(
        "ArraysImpl",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "3a520123de9cd4ca9a16c3f5b2d60d7d30aba9f7": LibraryInfo(
        "ConditionalEscrowMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "dfd11780fdbce9683363b9951c1736dd9c0a3479": LibraryInfo(
        "Create2Impl",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
        ],
    ),
    "039c37d37cd81934ed60f46f40e5b7c454e5c61e": LibraryInfo(
        "SupportsInterfaceWithLookupMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "945e934e278de6fd89f396f2cf47be09063ca054": LibraryInfo(
        "ERC165NotSupported",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "ea356c162ff728d39db8f4b1f8629294b7dc53c1": LibraryInfo(
        "ERC165CheckerMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "0a36b70b7c01ef2e9ad666db0b7c7815a2954bdc": LibraryInfo(
        "ERC20BurnableMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "44563df6fb78cc199c6afa99364a06e8b6bb1a8b": LibraryInfo(
        "ERC20CappedMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "065fda899fd387ce4fb161a544c6ca5c4d2cefe0": LibraryInfo(
        "ERC20DecimalsMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "0848d902f46092fd3cb28518efb3485754a176bd": LibraryInfo(
        "ERC20Mock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "d3694a314c74d8e0061fd1ee4abe29265e333a8a": LibraryInfo(
        "ERC20PausableMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "b87497aeac600f01a5e99eef27004dba2b386db9": LibraryInfo(
        "ERC20SnapshotMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "801315f0005d984a6660bcc6a0980fd812f1c36a": LibraryInfo(
        "ERC721BurnableMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "7b7d05bbf487b7101f6d0b1b17d9775001297456": LibraryInfo(
        "ERC721GSNRecipientMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "b702ee7d010f646e049b5e6786395716a6c4e5de": LibraryInfo(
        "ERC721Mock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "4265a7d8085494949939f615f62481d368c2ea2a": LibraryInfo(
        "ERC721PausableMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "153e1fe8ab29256f08340d4b68bb4d0e7bf31c1b": LibraryInfo(
        "ERC721ReceiverMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "9b9a5118eced1d02b1558076d4598e9e007ef161": LibraryInfo("ERC777Mock", ["v3.0.0"]),
    "d4ab30adb57b13f8a100753fcbcc100b5b93c41f": LibraryInfo(
        "ERC777SenderRecipientMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "56edef128a9c6161b588e85b7e9f8a7c8719330c": LibraryInfo(
        "EnumerableMapMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "42492e1e3840893868cce13e052e73be0115a282": LibraryInfo(
        "EnumerableSetMock", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "8142f6d05936c535329a037a5982940423113d0d": LibraryInfo(
        "EtherReceiverMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "926923f5dda7a7fdefe2b298549b4c7c899d644d": LibraryInfo(
        "GSNRecipientERC20FeeMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "b25e72ff5f0838564ad1fef33a62269baa223e58": LibraryInfo(
        "GSNRecipientMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.3.0",
            "v3.4.0",
            "v3.4.1",
            "v3.4.2",
        ],
    ),
    "08d9ca42c0b395de9866fdc89cf80baa79f3c544": LibraryInfo(
        "GSNRecipientSignatureMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "35bab91349a98ac9d37a0b0dea207ec66d9df1de": LibraryInfo(
        "OwnableMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b598caa720703755d142c55313587b39afd98fed": LibraryInfo(
        "PausableMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "ee40626ef9ea1cda61726721063073150205a62d": LibraryInfo(
        "PullPaymentMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "9e583d7f7bb1a067f370d89b9fbe3761ec3e9667": LibraryInfo(
        "ReentrancyMock",
        ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"],
    ),
    "b2abff56fa395cf30f6f70e37eca3d75afbba4fd": LibraryInfo(
        "SafeCastMock", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "bd3f6a5cf9aa93cca8f92896283807e732bf562f": LibraryInfo(
        "StringsMock",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "128b25a6695355f36790d5a10fd795b8bb27fa2d": LibraryInfo(
        "PaymentSplitter", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "86fd813a5a70b5d7233bc1dd53d2f794978e8bcd": LibraryInfo("PullPayment", ["v3.0.0"]),
    "88a3718cebe06fc9da77d9678a2b6f0ed68ddba3": LibraryInfo(
        "ConditionalEscrow",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "69fb19ca610d79dbf1138608ac29096e7f1b5976": LibraryInfo(
        "Escrow",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "f2caea65705f8c4230984e0a8c7e764b2d87c29c": LibraryInfo(
        "RefundEscrow", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "54363b19c1cc14361dfea5510bff28f17a35e284": LibraryInfo(
        "ERC20PresetMinterPauser", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "38ca7b059432b97d9bd6ebb4dbfd3a8e7626c059": LibraryInfo(
        "ERC721PresetMinterPauserAutoId", ["v3.0.0"]
    ),
    "01a31d70eac15ebc3e72762f3d9083e2ec58102f": LibraryInfo(
        "ERC20", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0"]
    ),
    "b6e55d3df0d0552ed089b09f61be8bc6379ead02": LibraryInfo(
        "ERC20Burnable", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "32dab051731393e6bfb3688e8cfb871017bb917d": LibraryInfo(
        "ERC20Capped", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "33382c542643be96d197ace0347bc3ca0b450993": LibraryInfo(
        "ERC20Pausable",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b1b3262a12fc93ad5fc3044f105688b26a8fc39c": LibraryInfo(
        "ERC20Snapshot", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.1.0-solc-0.7"]
    ),
    "8ad28076b641582bd77b676374b81cfd0f2e1a16": LibraryInfo(
        "SafeERC20", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "b021a1cfeb77d1b2933aee2118525dec020d52e3": LibraryInfo(
        "TokenTimelock", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "876d34e7701f0b3ebefb39f5fa5c0fe434181466": LibraryInfo(
        "ERC721", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "a880a1b2738b3efcc5a95143d0a326ff227a45d0": LibraryInfo(
        "ERC721Burnable", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "562cd257f69b05c02c7e235fd3a6d3619c428006": LibraryInfo(
        "ERC721Holder", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "fa7968daf5e28907a8097cf716abe22a74102d2b": LibraryInfo(
        "ERC721Pausable",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "c05ee17be3c12e0d5062b147bbc85543ca5e57a0": LibraryInfo("IERC721", ["v3.0.0"]),
    "2f8c54269c3eef1154da10fbe4cc8b9b988909d8": LibraryInfo("IERC721Enumerable", ["v3.0.0"]),
    "c03c0409f543870410ebc74e33089d8bd8fe4d33": LibraryInfo("IERC721Metadata", ["v3.0.0"]),
    "a4499a2caaf32ff3a48dfbb81587c3adf6adfae8": LibraryInfo(
        "IERC721Receiver", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "5899fda2e6c4c8cf2177cc7c078c78e6e5afd218": LibraryInfo("ERC777", ["v3.0.0"]),
    "b9ef6216c31f8261423581d843bf14a333570560": LibraryInfo(
        "IERC777",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b3b149c4a02c930e5f138a7bd4d1ed07e5742f36": LibraryInfo(
        "Address", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "61cc196dcfac4de6436deb8ec083d4aabf408a69": LibraryInfo(
        "Create2", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "a37fb5e05f9228dc03b7c50737be17949c276978": LibraryInfo(
        "EnumerableMap",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "ab23fb82ac99e05ad0a8697c1ad6b8eca4b9b6cf": LibraryInfo(
        "EnumerableSet",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
        ],
    ),
    "21547b61a2857572da1e51464899cdd52ebd5737": LibraryInfo(
        "Pausable", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "7e7fa83b0f54ef795991472b8e1d61d5cf98c7d9": LibraryInfo(
        "SafeCast", ["v3.0.0", "v3.0.1", "v3.0.2"]
    ),
    "47fdeef8766861e816936156be77b55cb8e0d15d": LibraryInfo(
        "Strings",
        [
            "v3.0.0",
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "3ebd393dd34383ead311cc6a4ac498d0562fbeed": LibraryInfo(
        "ERC777Mock", ["v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0", "v3.3.0"]
    ),
    "08d677f4935acdd04f1939d6430d2d98ed95a8b8": LibraryInfo(
        "PullPayment", ["v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
    ),
    "bcab2445fc6987740f10b1b48f5cc9f0a9dc628f": LibraryInfo(
        "ERC721PresetMinterPauserAutoId", ["v3.0.1", "v3.0.2"]
    ),
    "391484feda2d514efcbd8ad05bf24925d6a71d9c": LibraryInfo("IERC721", ["v3.0.1", "v3.0.2"]),
    "043402c29808063960b154297d4d949f81f27e38": LibraryInfo(
        "IERC721Enumerable",
        [
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "609c41e5ec3e7eda3fe7b20d5fdf8459da4741fe": LibraryInfo(
        "IERC721Metadata",
        [
            "v3.0.1",
            "v3.0.2",
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "fe18a97dfdc6f6805760ef16a3a6426fd4ca5742": LibraryInfo("ERC777", ["v3.0.1", "v3.0.2"]),
    "59f0695316bfaf076e70940bb15f611ab18e7380": LibraryInfo(
        "Context",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "6ce10025cea27bb5e02ed9a0a849c592d991f9ba": LibraryInfo(
        "AccessControl",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "05fb43f68cd62715cd9537e2407662ffd80d1b14": LibraryInfo(
        "SafeMath",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "14bdd1cf1d91f81d608b9317df714bfdce5cc5c8": LibraryInfo(
        "SignedSafeMath", ["v3.1.0", "v3.1.0-solc-0.7"]
    ),
    "c387ffafae87632afcf8a61aa9a3046f74207337": LibraryInfo(
        "AddressImpl", ["v3.1.0", "v3.1.0-solc-0.7", "v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"]
    ),
    "77dbf870fb94cfd13fd3fd2cf4d40eed0e1b5fe5": LibraryInfo(
        "CallReceiverMock",
        ["v3.1.0", "v3.1.0-solc-0.7", "v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"],
    ),
    "2fbafc739e08a6e4f30468e02c422a0f46a44133": LibraryInfo(
        "ERC1155BurnableMock", ["v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "edebb3dec4141dedd0e6486b38ae6d2f4a2750df": LibraryInfo(
        "ERC1155Mock", ["v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "497e0d5e7016d8c029788a4612313a68b0dcac11": LibraryInfo(
        "ERC1155PausableMock", ["v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "b63233a551c74f686b15f9d1e41ec9a511b216c9": LibraryInfo(
        "ERC1155ReceiverMock", ["v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "4e0eb152c67034b43787e86dd9517e5acef04406": LibraryInfo(
        "EnumerableAddressSetMock",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
        ],
    ),
    "33031da76437b1311f45e835d07084449361c05e": LibraryInfo(
        "EnumerableUintSetMock",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
        ],
    ),
    "d58e3bc4a8dc2a667dfc6cd02e834693f8970d4f": LibraryInfo(
        "SafeCastMock",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "59444c98b67b5f88dfb7bc0165563cc10963cb54": LibraryInfo(
        "ERC1155PresetMinterPauser", ["v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "57f1c230932cbfd9944efde495ece7b93961216c": LibraryInfo(
        "ERC20PresetMinterPauser", ["v3.1.0", "v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "60a2b550bd5c41484cbb9d96840bde18080cc9e0": LibraryInfo(
        "ERC721PresetMinterPauserAutoId", ["v3.1.0"]
    ),
    "271759a8472e5c3f9bd708d319334bc362f7ea28": LibraryInfo("ERC1155", ["v3.1.0"]),
    "134643457f4b7b6f0e9e7e4d1a9dcc4490977b5b": LibraryInfo(
        "ERC1155Burnable",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "cdb13d40682488f9f0953066325cf069b44dbd1e": LibraryInfo(
        "ERC1155Holder",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "ad8f8fb3ef5b64079ea06b8a84f71961ca862b2c": LibraryInfo(
        "ERC1155Pausable",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "bd50c286a31a9281ae013970efdd8a2698f70a3d": LibraryInfo(
        "ERC1155Receiver", ["v3.1.0", "v3.2.0"]
    ),
    "b51299123b2b7ac6f4473c4e9eeff2fae2527866": LibraryInfo(
        "IERC1155", ["v3.1.0", "v3.1.0-solc-0.7"]
    ),
    "ebbd8915f7e42b138f231d12a57aa3205648c228": LibraryInfo(
        "IERC1155MetadataURI",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "461f1b75562c952dc593e4b74fe5957247b47e96": LibraryInfo(
        "IERC1155Receiver",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "af36aa37efe07de73c75c3e3b2768abaf71d1f7e": LibraryInfo(
        "SafeERC20",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "76e26d8fe94c40bc65de0b949ba063aec0c8888d": LibraryInfo("ERC721", ["v3.1.0"]),
    "8b36b4f8062eab95d4c7b88da93222c71ab4bc9a": LibraryInfo(
        "ERC721Burnable",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "8a49c9027bfd68a7406842fc38a54c1ffdb0f55c": LibraryInfo(
        "ERC721Holder",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "6bc0035b00df60df8ab929ad72f1c15907ead145": LibraryInfo(
        "IERC721", ["v3.1.0", "v3.1.0-solc-0.7"]
    ),
    "66c525cc867324229ddc289348a728c95abd8ac0": LibraryInfo(
        "IERC721Receiver",
        ["v3.1.0", "v3.1.0-solc-0.7", "v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"],
    ),
    "885e6164dd6b49a503e5a2a4ed16277b6eb23ca1": LibraryInfo("ERC777", ["v3.1.0", "v3.2.0"]),
    "61c30616ec7a625371407d69c4f4287bef65465c": LibraryInfo(
        "Address", ["v3.1.0", "v3.1.0-solc-0.7", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"]
    ),
    "e55e6ff86a0622d2187303e42de5dbd1f8bd7577": LibraryInfo(
        "Create2",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
        ],
    ),
    "7253411ae52004badc4d7f7410ce466489d61649": LibraryInfo("Pausable", ["v3.1.0", "v3.2.0"]),
    "26c0a8f218e277e2f800073ec1cf3d9e8589d369": LibraryInfo(
        "ReentrancyGuard", ["v3.1.0", "v3.2.0"]
    ),
    "3bab9320873cd011466b2a6ab0dcac0f5dc1bc69": LibraryInfo(
        "SafeCast",
        [
            "v3.1.0",
            "v3.1.0-solc-0.7",
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "4078d8de60d037cbbb1a421d03159750cef400d7": LibraryInfo(
        "GSNRecipientERC20Fee", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "05584150eb03bca28420d821f0d3079f3c392059": LibraryInfo(
        "__unstable__ERC20Owned",
        ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0-solc-0.7"],
    ),
    "4821563b16a010649bd9fde1586e911f6c9c1841": LibraryInfo(
        "GSNRecipientSignature",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "15cacbe095318831e2b3e609d4018cf5d59bb7af": LibraryInfo("IRelayHub", ["v3.1.0-solc-0.7"]),
    "0453e5d14887ca74d7a9dd93ea24ffd21b33c0cc": LibraryInfo(
        "Ownable", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "1e0f45ff715be57f9424f5703cbaf1c7c0b4cdad": LibraryInfo(
        "ERC165", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "2dab2a74b7d92d977062dc109c47ca5ff6817564": LibraryInfo(
        "AccessControlMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
        ],
    ),
    "8caf6b0156b3bddcfbc8fdca0f640795d2dad50a": LibraryInfo(
        "ArraysImpl",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "a0dd84b48b5d2c1d88cf53ceb5e3f992edb33507": LibraryInfo(
        "ERC1155BurnableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b423c7c0aa88de46bbfd3d42fea4db2cda7733fe": LibraryInfo(
        "ERC1155Mock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "85b3c12fd1d0ddd48e056e0b40f7407323376576": LibraryInfo(
        "ERC1155PausableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "73e683d19ff414928daa00a6fced00488cb31307": LibraryInfo(
        "ERC1155ReceiverMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "83c038d09502c0d9a0315629e03aca228f6aeca7": LibraryInfo(
        "SupportsInterfaceWithLookupMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "32bbc7aff9562c2ae47502929375cd06c0e01aab": LibraryInfo(
        "ERC165InterfacesSupported",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "7d163c3d68597c146c14da4df3f451afed59a2f3": LibraryInfo(
        "ERC20BurnableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "7214c953c5c6ec720257cd10340380687965941f": LibraryInfo(
        "ERC20CappedMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "8971a5f34be9083e20af4a06fb75050ff87cc784": LibraryInfo(
        "ERC20DecimalsMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "22cfcfc29d92bda4cca9a70b78b9ddefab727ccc": LibraryInfo(
        "ERC20Mock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "db4e7558d868ae1b732167860c6d77e361f552fa": LibraryInfo(
        "ERC20PausableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "4f7b8369f212124b124bbd4ff4d9809d1462f947": LibraryInfo(
        "ERC20SnapshotMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "a98e5e8ec5b8c839786c8b5fec95f1a8c0d76999": LibraryInfo(
        "ERC721BurnableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "6bca38a21f8600f2c6e7ba24572beeeca15a7007": LibraryInfo(
        "ERC721GSNRecipientMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "27639747781f75ef1d11c3a8af9e7f9425b6595b": LibraryInfo(
        "ERC721Mock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "f1e38a0757425bc9c416626fcf8f4a73a612264a": LibraryInfo(
        "ERC721PausableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "4fa02f6cb2fe182533fe2c180323c8bdaf20472c": LibraryInfo(
        "ERC721ReceiverMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "01f24211871a64c439300003fc8b8dc76ddff4b6": LibraryInfo(
        "ERC777Mock", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "d286a08d1ddefa6a8fa5b8d6d8a52f4fdee2ce0c": LibraryInfo(
        "GSNRecipientERC20FeeMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "fec57f6d1902f7fbac554b0f375b3117e8e745eb": LibraryInfo(
        "GSNRecipientSignatureMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "ea7b7becb2c1cc0987b63d7cd3065b1819bb4b0a": LibraryInfo(
        "PausableMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "7d8fde97a41abf14faf73685794d849a4c3e0ac1": LibraryInfo(
        "PullPaymentMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "0c8d3622e8f5d7562ad37806f3d75b9290558a3a": LibraryInfo(
        "ReentrancyMock",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "0dbc8bb2fa7ae511f40ac5143ce8817dba57d89c": LibraryInfo(
        "SafeERC20Wrapper",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "9c68614788325a6129235a41228ca6d0d2ae806b": LibraryInfo(
        "PaymentSplitter", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "8084049564949219b37e12ecf91934ad62e5a94d": LibraryInfo(
        "PullPayment", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "1a5d2d9ad8b09f49594f516e1c1bd434264b6441": LibraryInfo(
        "RefundEscrow", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "7ef8bf14f12c46b04f4bb701ac6148af107d151e": LibraryInfo(
        "ERC1155PresetMinterPauser",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "4d3c1b8ff12cb6f53bfe559c4001aaae2ce5bfa9": LibraryInfo(
        "ERC20PresetMinterPauser",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "76e1b471738b29e9ad472002b299e6ca5c992583": LibraryInfo(
        "ERC721PresetMinterPauserAutoId", ["v3.1.0-solc-0.7"]
    ),
    "13032a5e6e8c053928c1a7079d1cec08a8f72545": LibraryInfo("ERC1155", ["v3.1.0-solc-0.7"]),
    "e9aeb04c7cf3cfe28278030bef8e6918e8822bd0": LibraryInfo(
        "ERC1155Receiver",
        ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0-solc-0.7"],
    ),
    "1524e25dfd71e549c0927267e4cf939f87eb856c": LibraryInfo("ERC20", ["v3.1.0-solc-0.7"]),
    "ce38bf299cd7a12c71f467aab654930a323c8947": LibraryInfo(
        "ERC20Burnable",
        [
            "v3.1.0-solc-0.7",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "a093419c3b2483a11d550d411c12a40b4d2bc644": LibraryInfo(
        "ERC20Capped", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "c13eed0a07804745778304d7af258421bc4f2c50": LibraryInfo(
        "TokenTimelock", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "5553fa5d1dd434b4ff2f5631f89923d65a4156db": LibraryInfo("ERC721", ["v3.1.0-solc-0.7"]),
    "c97967b9b005fffa9ed4fc230cf48d48e34e71bc": LibraryInfo("ERC777", ["v3.1.0-solc-0.7"]),
    "c6c506954a6d5d6b55db67cc577e31e7da641ecd": LibraryInfo(
        "Pausable", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "aa82b2ee7d508dc438e8a7d3995278479076184e": LibraryInfo(
        "ReentrancyGuard", ["v3.1.0-solc-0.7", "v3.2.1-solc-0.7"]
    ),
    "85e7ef332d5fc621ce63ccba93ee518591bf8c8b": LibraryInfo(
        "GSNRecipient",
        ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0", "v3.3.0-solc-0.7"],
    ),
    "96d2749e41cfd4e833a6178779093d82efbb7d0b": LibraryInfo(
        "IRelayHub",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "ffe1a6c90aa2b5556371b3799d2c65380a257d0b": LibraryInfo(
        "IRelayRecipient",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "0d2073be4268aabd41cce88b3769748e23142750": LibraryInfo(
        "SignedSafeMath",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "c0bae1111dcdf923d9a02599ff8a04c00e2456ed": LibraryInfo(
        "ClashingImplementation",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "4f92b6c4dfa12c3081d1fe4007e48df4c8c82e5c": LibraryInfo(
        "Impl",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "299556791f944a3fdbb677e5940c9d6865822606": LibraryInfo(
        "DummyImplementation", ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"]
    ),
    "0b65288765b06e6baaa610a1d42eaa2b4591d8cd": LibraryInfo(
        "DummyImplementationV2", ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"]
    ),
    "36075e336521530913cca767578aac6f07a38909": LibraryInfo(
        "InitializableMock",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "2f0630fab703c0cfc42ae33caf06e886fc4e6969": LibraryInfo(
        "SampleHuman",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "0de21f8a03ee4c6f6a63c6b6bf8b4f72d72ceced": LibraryInfo(
        "SampleMother",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "62b03120ad8b165c812e68bfdbba23080bf441b2": LibraryInfo(
        "SampleGramps",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "0bb55179c7e2bafad38c05cdad4d7a4a6b82d90e": LibraryInfo(
        "SampleFather",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "dc4d51c37ecfb1e2967ef74f7a2559a6252a5272": LibraryInfo(
        "SampleChild",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "85d6460e3b0ac8447a7db9493a5ff396c5e9364a": LibraryInfo(
        "Implementation1",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "43af63388be018e6a4448b585ee2244486d266ff": LibraryInfo(
        "Implementation2",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "1b7890b0027cf8b10d871746f93c892d4b2e814c": LibraryInfo(
        "Implementation3",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "257829569899b91fcbbfbd6fe9660d7ed25f82b1": LibraryInfo(
        "Implementation4",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "e179e255d203b40b5e050148327a89a4db0274af": LibraryInfo(
        "MigratableMockV1",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b74cf7f9f38e31bc2c4cc77a87569a094d157de0": LibraryInfo(
        "MigratableMockV2",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "97d9d9e61df537b9d68d8d94b363eb8f58f9c855": LibraryInfo(
        "MigratableMockV3",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "36ef2be3f4842ffce40b0baad7a38c98dca86627": LibraryInfo(
        "ERC721PresetMinterPauserAutoId", ["v3.2.0", "v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "44346833a6bd65fe95c90748b5722a563f3dc3e1": LibraryInfo(
        "Initializable",
        ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0", "v3.3.0-solc-0.7"],
    ),
    "c2f5c325aaa4ab9aa2c8def40e53cb2e7c38dd66": LibraryInfo(
        "Proxy", ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7"]
    ),
    "62927e48e0b61e131a6cfa67ebda7218969a6f3d": LibraryInfo(
        "ProxyAdmin", ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0", "v3.3.0-solc-0.7"]
    ),
    "a312403c3feaf629c2900ce0f0d1434bc359d428": LibraryInfo(
        "TransparentUpgradeableProxy", ["v3.2.0"]
    ),
    "2dc09dba2775be34524d45a25c6a12a6064b687e": LibraryInfo(
        "UpgradeableProxy", ["v3.2.0", "v3.3.0"]
    ),
    "1451ecddce18800239ff93690b719b8a654a8b2e": LibraryInfo("ERC1155", ["v3.2.0"]),
    "4635856f8449649c520428ead6e61d6f9b1e13a8": LibraryInfo(
        "IERC1155",
        [
            "v3.2.0",
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "12525308d365e1082fcf3ada1fb2d71db3972b16": LibraryInfo("ERC20", ["v3.2.0"]),
    "0ea2181daa5c7e76ccbabf8a9999f9fbd1833820": LibraryInfo(
        "ERC20Snapshot",
        ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0", "v3.3.0-solc-0.7"],
    ),
    "65ebeb77cd51d64c2e748bd176562b4e4b3766b7": LibraryInfo("ERC721", ["v3.2.0"]),
    "365098499bb100597dd9267be4172eb9a51e49f7": LibraryInfo(
        "IERC721", ["v3.2.0", "v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0", "v3.3.0-solc-0.7"]
    ),
    "aca21574c58b1e1387769de3b07df2bd8648fe2a": LibraryInfo("Address", ["v3.2.0"]),
    "5e2433d4880abf2da08dc7bb2b1bed1ee89500dc": LibraryInfo(
        "ERC721PresetMinterPauserAutoId",
        [
            "v3.2.1-solc-0.7",
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "060fa9715f285857c483f5f8aa8f283597b32a8e": LibraryInfo(
        "TransparentUpgradeableProxy", ["v3.2.1-solc-0.7"]
    ),
    "eeb1b0eb21f40d26aeaa5db59da4d89bdd78eb3a": LibraryInfo(
        "UpgradeableProxy", ["v3.2.1-solc-0.7", "v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "a6e8c979be5bb5af9fbb1e614b27b38839a5894d": LibraryInfo("ERC1155", ["v3.2.1-solc-0.7"]),
    "99b6d5df430ce23689a152c8438164c5de872197": LibraryInfo("ERC20", ["v3.2.1-solc-0.7"]),
    "c60a6be3f3fce5a3b3ef5122354fffa11cc2f04a": LibraryInfo("ERC721", ["v3.2.1-solc-0.7"]),
    "ac504766b532baf6b726e48a8e3c99f16b2453c2": LibraryInfo("ERC777", ["v3.2.1-solc-0.7"]),
    "f9fd0c5c9e330675fda7856b975b0fe6b02624d0": LibraryInfo(
        "GSNRecipientERC20Fee", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "f1fee8d515a2f71cfbbc450e793a2d2b17caca7a": LibraryInfo(
        "Ownable", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "b503decf7949df51f4ba6808c081792e70437c0d": LibraryInfo(
        "ERC165", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "761f89f6ffc7ca427b95c3f0101db6d1f271d0e8": LibraryInfo(
        "IERC1820Registry",
        [
            "v3.2.2-solc-0.7",
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
        ],
    ),
    "7640634b8811549a807f0ba07f7acb29afbedf2d": LibraryInfo(
        "GSNRecipientMock",
        [
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "ef02f12e6402f08a97633ad225b6b312578ad132": LibraryInfo(
        "PaymentSplitter", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "248a8a1273db727248a7412571724b5707d2946b": LibraryInfo(
        "PullPayment",
        [
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "397958f6f4842504963dbd017cfb8bc64d4cc2f8": LibraryInfo(
        "RefundEscrow", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "84a1ee038830d25ac77a33ebe4b6d27360da022c": LibraryInfo(
        "TransparentUpgradeableProxy", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "bbc4789f86eff2f3a7f1da837ae6a85de7e2f803": LibraryInfo(
        "ERC1155", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "73606b13add74a0032c16e323d11c28d0a62fa05": LibraryInfo("ERC20", ["v3.2.2-solc-0.7"]),
    "c7e4c94e1c49864431de7e3b2dea4595757189d6": LibraryInfo(
        "ERC20Capped", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "ca4fe971d9d72558abd50f77b6cd8b3de2554b26": LibraryInfo(
        "TokenTimelock", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "eab2db3a101c13a594e8f1d140adf52c64242bf1": LibraryInfo(
        "ERC721", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "505e83265ba5e1b1939a2c199ec99b5beef596bb": LibraryInfo(
        "ERC777", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "ee5e60d9ed917eab36f085b0b128c2fff2caf10b": LibraryInfo(
        "Pausable", ["v3.2.2-solc-0.7", "v3.3.0-solc-0.7"]
    ),
    "bc88ca03e46528a04853c32ebf121df42c4d9edd": LibraryInfo(
        "ReentrancyGuard",
        [
            "v3.2.2-solc-0.7",
            "v3.3.0-solc-0.7",
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "2cefc88832911d8f000cf1f853a8a1ec34a83869": LibraryInfo("GSNRecipientERC20Fee", ["v3.3.0"]),
    "ff468e5fb020023b45058cd9d6baa684a07c169a": LibraryInfo("Ownable", ["v3.3.0"]),
    "62e78f66a0dc5a7ad8b7f155a4a3c0bc056d37ed": LibraryInfo("TimelockController", ["v3.3.0"]),
    "7661544d7b4503ae1db879c1b06335abe437eb43": LibraryInfo("ECDSA", ["v3.3.0", "v3.3.0-solc-0.7"]),
    "79f657470505cee15284ebf0afac69c26820b6bd": LibraryInfo("ERC165", ["v3.3.0"]),
    "3a5cd51f0635a3fb082c4e761450b541cedd5e9f": LibraryInfo(
        "AddressImpl", ["v3.3.0", "v3.3.0-solc-0.7"]
    ),
    "780be56bedddc62c2722b13e5fe2e258e07da87e": LibraryInfo(
        "CallReceiverMock",
        [
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
        ],
    ),
    "eebcccd00f6a1385ea11f82064fe982637af2cd8": LibraryInfo(
        "Create2Impl",
        [
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "54279277126550e93cb4518ef5b0ec055915ec67": LibraryInfo(
        "DummyImplementation", ["v3.3.0", "v3.3.0-solc-0.7"]
    ),
    "0b1c723fb1caabd0949393e90cbb3a18af826a7b": LibraryInfo(
        "DummyImplementationV2",
        [
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "8f7732e30464761faf28ca7d986c979cb78b55ff": LibraryInfo(
        "EnumerableBytes32SetMock",
        [
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
        ],
    ),
    "08b973b9862e47b6cef3ae3540a9c798a2e3948a": LibraryInfo("PaymentSplitter", ["v3.3.0"]),
    "3e2e2f659b27f72c72462d35a41afed6c71e1310": LibraryInfo(
        "PullPayment", ["v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "36cbd240c302af1fc3f2bd00aa7f204ccbe1e051": LibraryInfo("RefundEscrow", ["v3.3.0"]),
    "80b95e3cad825888ef85966822547e32c545d044": LibraryInfo("Proxy", ["v3.3.0", "v3.3.0-solc-0.7"]),
    "fb5050efb413c3776ec0c9ffa540df1a42d3ce2b": LibraryInfo(
        "TransparentUpgradeableProxy", ["v3.3.0"]
    ),
    "93c13eddcfcd62395624270cde928e5d24d3b4b8": LibraryInfo("ERC1155", ["v3.3.0"]),
    "61e358e538e2273e31fa7133009c7a3c4ff8b9dd": LibraryInfo("ERC1155Receiver", ["v3.3.0"]),
    "0dc22cde3abaf6c0fa621b32f9f7934e22f4c1d1": LibraryInfo("ERC20", ["v3.3.0"]),
    "63536d5bfe0f79c8ef6782baebe76002151cb22e": LibraryInfo("ERC20Capped", ["v3.3.0"]),
    "dd756683800487b41064dd881e0b65a419862aa0": LibraryInfo("TokenTimelock", ["v3.3.0"]),
    "818503b17c0db33bfe69b5cc461cbc061d0c65b9": LibraryInfo("ERC721", ["v3.3.0"]),
    "04278f72bdb6c61d366aec038058a1212a4f07e9": LibraryInfo(
        "IERC721Receiver",
        [
            "v3.3.0",
            "v3.3.0-solc-0.7",
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "5512c580e9da164446f6551a20486a35e1c08807": LibraryInfo("ERC777", ["v3.3.0"]),
    "da934a25d30edfd91855d54555dc0144dbbfd7cb": LibraryInfo(
        "Address", ["v3.3.0", "v3.3.0-solc-0.7"]
    ),
    "179de8c468d36b2e51824b07136adedae7bcbdc3": LibraryInfo(
        "EnumerableSet", ["v3.3.0", "v3.3.0-solc-0.7"]
    ),
    "12cb21575ea5e6e30c37c9a7440fcc2b3adb0845": LibraryInfo("Pausable", ["v3.3.0"]),
    "ffca07556d8e39845429a3b009980201301c5b6e": LibraryInfo(
        "ReentrancyGuard", ["v3.3.0", "v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "be045cb6e49d12aa04b07af22ad6e600d472b78f": LibraryInfo(
        "TimelockController", ["v3.3.0-solc-0.7"]
    ),
    "6af4381b463ec0dcd9e2332bff9cf3ea9568ba29": LibraryInfo("ERC20", ["v3.3.0-solc-0.7"]),
    "33beec74bb53c2ee0e9e12f694e367258724e6b2": LibraryInfo(
        "GSNRecipient",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "32a14bea425dc2959b680187600942f4901efceb": LibraryInfo(
        "GSNRecipientERC20Fee", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "fa5e7908a5cb10013f735b6718ba6ef4fb41b794": LibraryInfo(
        "__unstable__ERC20Owned", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "5d07d72245331e4275c204db282ad3900383f778": LibraryInfo(
        "Ownable", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "5d26e032a554805a01aca59579417663de70f966": LibraryInfo(
        "TimelockController", ["v3.4.0", "v3.4.1"]
    ),
    "63a2430e318736b284bccc524d6c619d329ce419": LibraryInfo(
        "ECDSA",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "2cf03d8347d7129c4de359dcaa4f0dc40f88684a": LibraryInfo(
        "EIP712", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "92215334770433b2add7c67ac51233591f7fe922": LibraryInfo(
        "ERC20Permit", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "e2f97eec1c3991924b7b1456696f87048be7d783": LibraryInfo(
        "IERC20Permit",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
        ],
    ),
    "f35d0cf20e1373848e42b706d4d6aa9fd46988c2": LibraryInfo(
        "ERC165", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "c8909db38edab0286eb1e83f45baad9b70ed6340": LibraryInfo(
        "ERC165Checker",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "dbf020d120894cffa01451b8caa8cac408122c47": LibraryInfo(
        "ERC1820Implementer",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "a1815b90bd687d3a96e0d4cc57bc8aa5acc126a9": LibraryInfo(
        "SafeMath",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "1eee0a26498f2e503cda12d7f0a3631e9256d11f": LibraryInfo(
        "AddressImpl",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "64ba98e0a7a3462e9a936a0744ed9d1f27f4efe2": LibraryInfo(
        "BadBeaconNoImpl",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "49252afe482c957eb4d0d4e1f61a70fae4534bbe": LibraryInfo(
        "BadBeaconNotContract",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "f21645963792a804fe46d24eae733ced9792325e": LibraryInfo(
        "ClonesMock",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "c312288ff11bbaa9f288b73efa4e89905b4b3e0c": LibraryInfo(
        "DummyImplementation",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "fba59a0ad823b65925d38fba35a9fb0acba4f11c": LibraryInfo(
        "EIP712External", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "3f41e938116aa300aad2aefadfbcaa6193c490ef": LibraryInfo(
        "ERC165CheckerMock",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "f5bc328483f38e40a88c2830fc7d26319aa9b5fb": LibraryInfo(
        "ERC20PermitMock", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "02d7d727adc8cb0dbc83f8e1803c172a0990296f": LibraryInfo(
        "ERC777Mock", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "7cdf827fe3a903fbcaa418bad074950ae9f8c8d2": LibraryInfo(
        "ERC777SenderRecipientMock",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "3a93528b96d70af4e872192f05dfc7ee25419517": LibraryInfo(
        "EnumerableMapMock",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "c68710ed96a182101e1024d3e1aa91cfd2a636d2": LibraryInfo(
        "SafeMathMock",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "5a91c81404f840fd7f9054fe06f3a1c5036d4343": LibraryInfo(
        "PaymentSplitter", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "e7ac2394f80e32ef8d86823bf3ab56e94543490f": LibraryInfo(
        "Escrow",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "46e54ddada38f2432fbbd672068ebc144fba6137": LibraryInfo(
        "RefundEscrow", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "222751ccf88f680c3c75ab80cfb80797d45b2651": LibraryInfo(
        "ERC20PresetFixedSupply", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "1a1081be6939302bfc77c7b3be6c5f874118297f": LibraryInfo(
        "ERC777PresetFixedSupply", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "ce7db6d05e7868e70e75528f1c0fbd9297bc6fcf": LibraryInfo(
        "BeaconProxy", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "4249e310139fbc623392ee676281a60d143c16da": LibraryInfo(
        "Clones",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "869d95b3589c7fa6b2ecb1dfeb9008c463c267bf": LibraryInfo(
        "IBeacon",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "0fbaee3e2bef583ef42cb3ed731b3e40b68aea33": LibraryInfo(
        "Initializable",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "3785f5c4f386559127baa5a185d2ec13ad4c53af": LibraryInfo(
        "Proxy",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "1c570dba696f08a170e92f985d839dbe0ecb4a91": LibraryInfo(
        "ProxyAdmin",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "a7386fcd820a2c66235bb3e835a30b553545812f": LibraryInfo(
        "TransparentUpgradeableProxy", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "870cdbd1d2ddaf132c3a1a6a1d48d6ea004b123a": LibraryInfo(
        "UpgradeableBeacon", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "9ce86a848977d6ebddddd293ea9e81836c488c6a": LibraryInfo(
        "UpgradeableProxy", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "3160f17274036d6719cd64c436b4167104e70bc1": LibraryInfo(
        "ERC1155", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "1c6dbf08eb3ea12cf8a55ba920f32971bf194e89": LibraryInfo(
        "ERC1155Pausable",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b5611144434fe88f4b7fa065d3fe437178a770ce": LibraryInfo(
        "ERC1155Receiver", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "1c7854ebfeea3b6b4ada23aa0dec5cdd142d5524": LibraryInfo(
        "ERC20", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "54480a412d33bc4808a6f4626c12a186086c236b": LibraryInfo(
        "ERC20Capped", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "06ea9a75c96d6774e79699e85d93b2b2daf7e701": LibraryInfo(
        "ERC20Snapshot",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "7042e55c509ff3cbe7c149238e29fed880359381": LibraryInfo(
        "TokenTimelock", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "6146ecf60a2e9e538355b19cf9095a9723197adc": LibraryInfo("ERC721", ["v3.4.0"]),
    "7e232aaf85bb00c9401b300972a3f6322faed39d": LibraryInfo(
        "IERC721",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "9fa1eca3807f9186d44ae941020d506dfe551adc": LibraryInfo(
        "ERC777", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "041cd09ad5b7832a451916a4eab7c14b9157f9bb": LibraryInfo(
        "Address",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "1c6caa372c1211fa570af1576c88d16cacb426c0": LibraryInfo(
        "Create2",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "cafd568a2be123baff9a85ba0d347a428fb5777e": LibraryInfo(
        "EnumerableMap",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "1690dfe17f8334a2a88203427ce601d9c6b25760": LibraryInfo(
        "EnumerableSet",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
        ],
    ),
    "3246d2bfdfc6dd0197a0fe1497632d66ae05fd58": LibraryInfo(
        "Pausable", ["v3.4.0", "v3.4.1", "v3.4.2"]
    ),
    "b12a995aa8744db27ab0e367133c4cf01eb3a9de": LibraryInfo(
        "Strings",
        [
            "v3.4.0",
            "v3.4.0-solc-0.7",
            "v3.4.1",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2",
            "v3.4.2-solc-0.7",
        ],
    ),
    "1dca314c082a2d86c4b13fc44d00ed3caf84660d": LibraryInfo(
        "GSNRecipientERC20Fee",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "507897800a5e8a472a426aebecc8e766854e20cd": LibraryInfo(
        "__unstable__ERC20Owned",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "e7f6d7ee5a886c88c0052fc24f06e83a3f3a08d1": LibraryInfo(
        "Ownable",
        [
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "b1eaec929a4492a5ab9c3ee0941f4d0ad4dae002": LibraryInfo(
        "TimelockController", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2"]
    ),
    "050c8ca6f92fe1485057a1faa1293ac23af4e9ec": LibraryInfo(
        "EIP712", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"]
    ),
    "4fd1e1d5762c465c2779bb5062ab69c1c15df7b6": LibraryInfo(
        "ERC20Permit",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7", "v4.0.0"],
    ),
    "8ebfa908d5afc1a43d6c42fb85da4d675ad2acaa": LibraryInfo(
        "ERC165", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"]
    ),
    "69db7dc4835bf134acaadee0aa2d3f51ab9e655b": LibraryInfo(
        "EIP712External",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "91dc025deeeb2e4dead2db739f04e2d00619a818": LibraryInfo(
        "ERC20PermitMock",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "f37b58e417ed7f71db679b2c2fa5c0ce14226133": LibraryInfo(
        "ERC777Mock",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7", "v4.0.0"],
    ),
    "b052abe16f942be8a710a608a09f437476b8ca03": LibraryInfo(
        "PaymentSplitter",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "47f3ee26c503ec9c706f580520db5e78af9aeeef": LibraryInfo(
        "RefundEscrow",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "8a505d49e69fe65120a99979dbdca39b8efe22f5": LibraryInfo(
        "ERC20PresetFixedSupply",
        [
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "ea8b53fd468c496848babd2a0e108b002c94c3d7": LibraryInfo(
        "ERC777PresetFixedSupply",
        [
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "2bc90d97df0f2ee6653f0237130bdf57ca2437ab": LibraryInfo(
        "BeaconProxy",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7", "v4.0.0"],
    ),
    "f1f156b98ccda98d19e894c141bc0317cc5eb9c0": LibraryInfo(
        "TransparentUpgradeableProxy",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "1ae15cdffe0ca9340174ae68cb8d2892fe831bc5": LibraryInfo(
        "UpgradeableBeacon",
        [
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "1c2989c2b4cad10ff8b0ed4f7cffce37d3f7a6dd": LibraryInfo(
        "UpgradeableProxy",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "51ad04dc5cdffc68238a1696f78d7672555ec7dd": LibraryInfo(
        "ERC1155", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"]
    ),
    "48ba59afc22a61b178aba0199a30340b43f9ba62": LibraryInfo(
        "ERC1155Receiver",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "7cf1a0c8c25eaa2edbfccc040d2942fbb7d7596e": LibraryInfo(
        "ERC20", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"]
    ),
    "12d077e4475d8cc3dd032a10fb2f97138c5c2bf4": LibraryInfo(
        "ERC20Capped",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "8846bad470e1c4a2177e3247c29c6604a2307157": LibraryInfo(
        "TokenTimelock",
        ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"],
    ),
    "171ab805afaa2a3b05e4bdba9d9a8271c77db63a": LibraryInfo(
        "ERC721", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7"]
    ),
    "a908082bdc2115f43aabea87e8c2897833bfda29": LibraryInfo(
        "ERC777", ["v3.4.0-solc-0.7", "v3.4.1-solc-0.7", "v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"]
    ),
    "0424544a512fcdda8b090610916a0f7c5d375387": LibraryInfo(
        "Pausable",
        [
            "v3.4.0-solc-0.7",
            "v3.4.1-solc-0.7",
            "v3.4.1-solc-0.7-2",
            "v3.4.2-solc-0.7",
            "v4.0.0",
            "v4.1.0",
        ],
    ),
    "1321258244d9c40eff5a48ed1ecb88b2577a56b7": LibraryInfo("ERC721", ["v3.4.1", "v3.4.2"]),
    "a0a26ed94d63bffb8f31246bdfce9867514cd672": LibraryInfo(
        "ERC721", ["v3.4.1-solc-0.7-2", "v3.4.2-solc-0.7"]
    ),
    "b01a301a7d54e6d284e847eb9d9e24076112808c": LibraryInfo("TimelockController", ["v3.4.2"]),
    "69d0e361a511bf3103d25a77dbe77048ee5e0115": LibraryInfo(
        "TimelockController", ["v3.4.2-solc-0.7"]
    ),
    "ef9cee4fc16302d9c2f27edb367db294c1b81f5f": LibraryInfo("IAccessControl", ["v4.0.0", "v4.1.0"]),
    "dab86c163c575d30473cb3a5c0624b44334efc12": LibraryInfo("AccessControl", ["v4.0.0"]),
    "2207123df93140cd294823148a2558be596e6495": LibraryInfo(
        "IAccessControlEnumerable", ["v4.0.0", "v4.1.0"]
    ),
    "abbe8b6df781ca55c069fd98e85f817213835c6d": LibraryInfo(
        "AccessControlEnumerable", ["v4.0.0", "v4.1.0"]
    ),
    "9565576e12fc40a6a8a79f663a4899ef55e80c5e": LibraryInfo(
        "PaymentSplitter", ["v4.0.0", "v4.1.0"]
    ),
    "92411b430030f18396dc798bcf7d29c2d53b68eb": LibraryInfo("TimelockController", ["v4.0.0"]),
    "259338440d397d3da2a4bf44649d51cc646c5aa0": LibraryInfo("ERC2771Context", ["v4.0.0", "v4.1.0"]),
    "566d42bf0d67adb04c1e73658ef5802b61702c97": LibraryInfo(
        "MinimalForwarder", ["v4.0.0", "v4.1.0"]
    ),
    "253248bcf8aaa75c515f000d674e69e3ad2dc67c": LibraryInfo(
        "AccessControlEnumerableMock", ["v4.0.0"]
    ),
    "868d87ef0ff053e2007b9e9180f2d5daede6491a": LibraryInfo("ClonesMock", ["v4.0.0", "v4.1.0"]),
    "e4ddf77999bc8a4befcd1d9428b77ec0156f1c82": LibraryInfo("EIP712External", ["v4.0.0", "v4.1.0"]),
    "56a0750afc35891ff98a07f7c36aecbb2103c32e": LibraryInfo(
        "ERC1155ReceiverMock", ["v4.0.0", "v4.1.0"]
    ),
    "8ac6ce7dd83fe6abaaea9e149de7fab285cb6f76": LibraryInfo(
        "ERC165MissingData",
        [
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "b33e2d44585e75d38aa904a4e210baf4350189da": LibraryInfo("ERC165Mock", ["v4.0.0", "v4.1.0"]),
    "e89f235cccbc06e2bac7c41f6da38fd77d4de644": LibraryInfo(
        "ERC165StorageMock",
        [
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "8ab8d35fe19014b9066aa8ffc249623257072208": LibraryInfo(
        "ERC20DecimalsMock", ["v4.0.0", "v4.1.0"]
    ),
    "67b9f92bb0f7ef4c509fd6db84af16f6a1dc95f8": LibraryInfo(
        "ERC20PermitMock", ["v4.0.0", "v4.1.0"]
    ),
    "417a78c41729dfd05ac2baac8e6678dbb95f5a05": LibraryInfo(
        "ERC2771ContextMock", ["v4.0.0", "v4.1.0"]
    ),
    "4e57221ebf4782201f0d1ca5b851e5bb12ec2b8b": LibraryInfo(
        "ERC721BurnableMock", ["v4.0.0", "v4.1.0"]
    ),
    "e4bb74aec903fc8db95fad4c8192ff627923d2e9": LibraryInfo(
        "ERC721EnumerableMock", ["v4.0.0", "v4.1.0"]
    ),
    "cef3ef778dd17371bf88d3a20cbdcc3c71298afa": LibraryInfo("ERC721Mock", ["v4.0.0"]),
    "9e5a3684f1b44a48c73787f823a3d7898f922753": LibraryInfo(
        "ERC721PausableMock", ["v4.0.0", "v4.1.0"]
    ),
    "947534cf69fa1bf1babb1d89e68fa2435d73f59b": LibraryInfo(
        "ERC721ReceiverMock", ["v4.0.0", "v4.1.0"]
    ),
    "6fbee4f33e2aa55d513022b4b6629ef896f52db1": LibraryInfo(
        "ERC721URIStorageMock", ["v4.0.0", "v4.1.0"]
    ),
    "d955f8e424d0b8531fcec97fd70d2eefa06daf04": LibraryInfo("StringsMock", ["v4.0.0", "v4.1.0"]),
    "bf6d216501296a25f572b36b4ececf1e7f752b8e": LibraryInfo("Clones", ["v4.0.0", "v4.1.0"]),
    "3caba018d8b811d7a9487df761635928bc7caf3f": LibraryInfo("ERC1967Proxy", ["v4.0.0"]),
    "03f4e4dc310c6685debfa53240c8029d66d6a9d5": LibraryInfo(
        "TransparentUpgradeableProxy", ["v4.0.0"]
    ),
    "db88ad8eb489e2e93a76e7f0d0843f442bb3e802": LibraryInfo("Initializable", ["v4.0.0", "v4.1.0"]),
    "fcafd1a2198e83e29448c4961babe00d479a259e": LibraryInfo("PullPayment", ["v4.0.0", "v4.1.0"]),
    "06a7146060ceeb791b34296ac3859ddf9924c8d9": LibraryInfo("ERC1155", ["v4.0.0", "v4.1.0"]),
    "fc0e45a63f6c27366e72fba2e93045493a1d0fcc": LibraryInfo(
        "ERC1155PresetMinterPauser", ["v4.0.0", "v4.1.0"]
    ),
    "991da8c1a4e38a69803a920b2ba6f04f3534ba90": LibraryInfo(
        "ERC1155Receiver", ["v4.0.0", "v4.1.0"]
    ),
    "32f4baf24d04431b9f31d7fffbc14873db05910c": LibraryInfo("ERC20", ["v4.0.0"]),
    "b8948a765f56a1cfae8a3b92033d3a7f583d266f": LibraryInfo("ERC20Burnable", ["v4.0.0", "v4.1.0"]),
    "3ed786a6529d43a95101022d405252fbd955f7f6": LibraryInfo("ERC20Capped", ["v4.0.0", "v4.1.0"]),
    "975df6aa796d442e90665e8639659a8da4d06175": LibraryInfo("ERC20Snapshot", ["v4.0.0", "v4.1.0"]),
    "d6d1fc2391215c66cbe050ddb24066c54a8ec13f": LibraryInfo(
        "ERC20PresetMinterPauser", ["v4.0.0", "v4.1.0"]
    ),
    "b923239c1bd5ce64cdd82b8a78585e70ce09a0b5": LibraryInfo("SafeERC20", ["v4.0.0", "v4.1.0"]),
    "3cc2d212711b9aed654821263900fe101441e08e": LibraryInfo("TokenTimelock", ["v4.0.0", "v4.1.0"]),
    "ade76f270c6838a189583a70457b1f34f547fa89": LibraryInfo("ERC721", ["v4.0.0"]),
    "e32fa6056318ff4036b6b34ae3631d92cc2ea489": LibraryInfo(
        "ERC721Enumerable", ["v4.0.0", "v4.1.0"]
    ),
    "174c62a690020e2cb1b08c2ed4ebf665a78e3bd9": LibraryInfo(
        "ERC721URIStorage", ["v4.0.0", "v4.1.0"]
    ),
    "387defc33a85bd87dc92cf3e1b956407169ec624": LibraryInfo(
        "ERC721PresetMinterPauserAutoId", ["v4.0.0", "v4.1.0"]
    ),
    "8a77655c684246218b9a58702a073110c1960c2a": LibraryInfo("ERC777", ["v4.0.0"]),
    "fffccb2e4aaddd018bf1f74f424764d0d8f3ddcb": LibraryInfo("Context", ["v4.0.0", "v4.1.0"]),
    "2a02aed9ef802a8544d18afe1df202a0fc9f22fc": LibraryInfo("Counters", ["v4.0.0", "v4.1.0"]),
    "64e303670df935fe5d0a7e7bd932ae8850f6f201": LibraryInfo("Strings", ["v4.0.0", "v4.1.0"]),
    "b1f1fd21fabeee2b3f8d781a3f7b61d2da0fa499": LibraryInfo("ECDSA", ["v4.0.0"]),
    "53aa499a4c694653ffb7ad64295f7564c8d25f4e": LibraryInfo("EIP712", ["v4.0.0", "v4.1.0"]),
    "fef23c7cba2fd6827ad096a963156b7122a5714d": LibraryInfo("Escrow", ["v4.0.0", "v4.1.0"]),
    "c52d6d7307f32769c227bc90ff35f7ed9484a418": LibraryInfo("RefundEscrow", ["v4.0.0", "v4.1.0"]),
    "27eb537f38f4e78bf50d746739387234f230a4db": LibraryInfo(
        "ERC165",
        [
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "e00b58223b3f1aebcc28924cdbf577f342709c68": LibraryInfo("ERC165Checker", ["v4.0.0", "v4.1.0"]),
    "8ab170369493cd6ef28c81f35ec9fb0597632270": LibraryInfo(
        "ERC165Storage",
        [
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "01bd41c8fc215254e0fccc0f1937381becb83c93": LibraryInfo("ERC1820Implementer", ["v4.0.0"]),
    "725b5b6b3cb30d120bdc97b353b214d7e0d5457d": LibraryInfo("SafeCast", ["v4.0.0", "v4.1.0"]),
    "c3556d686a5da76a47d19d4e3c1aa5d53cc96011": LibraryInfo("SafeMath", ["v4.0.0", "v4.1.0"]),
    "31f7a9169859955645a6b3b01225caa339e68a92": LibraryInfo(
        "SignedSafeMath",
        [
            "v4.0.0",
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "50b36c99d71a6f1e5bc74eb37305fb633ca745b1": LibraryInfo("EnumerableMap", ["v4.0.0", "v4.1.0"]),
    "1eeccb2aba20ae782f788b591c1c73247a2f5710": LibraryInfo("AccessControl", ["v4.1.0"]),
    "0d100f93955e406b8f4c64256fe2fac9f58feaa3": LibraryInfo("TimelockController", ["v4.1.0"]),
    "03ad79036f06316b924f8e839e05f9f7418203d9": LibraryInfo("IERC1271", ["v4.1.0"]),
    "32778f5dea953b5c71cda22b9034d3a99c80a260": LibraryInfo(
        "IERC3156FlashBorrower",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "7a7395520740c3e9ca99f25ac256918525d6947b": LibraryInfo("IERC3156FlashLender", ["v4.1.0"]),
    "7b42fc0929549dded5a794ba5cbb6234482d5ae5": LibraryInfo(
        "AccessControlEnumerableMock",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "105af4b6cb195a355234adb0f75e29dc35fbfe58": LibraryInfo(
        "AccessControlMock",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "e69690c196421663cbeb3e40e3ec80db2419b7f8": LibraryInfo(
        "ERC1271WalletMock",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "400c8eb934cb0cc695a18678a58f974169150eeb": LibraryInfo("ERC3156FlashBorrowerMock", ["v4.1.0"]),
    "d7d5ac3eeb3537f6007674f03f33da91b2a99606": LibraryInfo("ERC20FlashMintMock", ["v4.1.0"]),
    "760696c2eddc1f804ccdd6ad139de35e315a8f5a": LibraryInfo("ERC721Mock", ["v4.1.0"]),
    "1aed59d47401d84a7d52819e97f7efbb125604bd": LibraryInfo("ERC777Mock", ["v4.1.0"]),
    "d4d4dc6d063c378fe8df00eba9ea1d3da940c6df": LibraryInfo("MulticallTest", ["v4.1.0"]),
    "d51ce27019d1ba250fe0737caab014f9c51aefd3": LibraryInfo("MulticallTokenMock", ["v4.1.0"]),
    "5ceef95f1a2229c02c5f838080b549fefa9d185e": LibraryInfo("SignatureCheckerMock", ["v4.1.0"]),
    "d9969b56a2b7a0b53970600d4563508c1ca509e6": LibraryInfo("StorageSlotMock", ["v4.1.0"]),
    "1859856bc5a07e18d8967ec00b4d89cd6ea11e0a": LibraryInfo(
        "UUPSUpgradeableMock",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "02306349e880c95b317f34313bf0d335bcb20711": LibraryInfo(
        "UUPSUpgradeableUnsafeMock",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "9d3be3ef2fe57b5f8345d6bb0b34500b94b3039f": LibraryInfo(
        "UUPSUpgradeableBrokenMock", ["v4.1.0"]
    ),
    "ad0004727dde87f3bf6a518a02ccc9475c378edd": LibraryInfo(
        "ERC1967Proxy",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "e2bf5ece630b73ede3fa56a42a625ff79cf7a07b": LibraryInfo("ERC1967Upgrade", ["v4.1.0"]),
    "775dad710f41a2629d9d5506682c1cd574eae0a6": LibraryInfo(
        "BeaconProxy",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "f1865b420ea4dee35a07e61461aa012d55131f33": LibraryInfo(
        "TransparentUpgradeableProxy", ["v4.1.0"]
    ),
    "a1b5157f3148bf64bed9182b4d0617a8eadfd581": LibraryInfo("UUPSUpgradeable", ["v4.1.0"]),
    "9d146a9046589ef5728295f53cb3fc9209f6f3e9": LibraryInfo("ERC20", ["v4.1.0"]),
    "e3f871942e9365cc12cdb31ac4196e415579b5af": LibraryInfo(
        "IERC20Metadata",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "1b85965b7436f201b003472d4afba8ef1e2f0707": LibraryInfo("ERC20FlashMint", ["v4.1.0"]),
    "2207444dc8582d69d9546a2434504f679dc50d9c": LibraryInfo("ERC20Permit", ["v4.1.0"]),
    "6e83d64273b978f98df3e2379c388010ec2860f4": LibraryInfo("IERC20Permit", ["v4.1.0"]),
    "1751dd56c4410e19af4980136ef1ba8e54000493": LibraryInfo("ERC721", ["v4.1.0"]),
    "5714897c18afeeddd7dbe406d9878e22f5d751d1": LibraryInfo("ERC777", ["v4.1.0"]),
    "63d1095e1fb56da130b614eeaa63f4803f99f7e5": LibraryInfo("Multicall", ["v4.1.0"]),
    "fe5963116e1e943c56b62faf6875a3f8482cfe84": LibraryInfo(
        "StorageSlot",
        [
            "v4.1.0",
            "v4.2.0",
            "v4.3.0",
            "v4.3.1",
            "v4.3.2",
            "v4.3.3",
            "v4.4.0",
            "v4.4.1",
            "v4.4.2",
            "v4.5.0",
        ],
    ),
    "b06559b6a9527a4db570993b98327d1e16908ed2": LibraryInfo("ECDSA", ["v4.1.0"]),
    "f6325fbfc5e1ff1f03992fba565321bbc17ed789": LibraryInfo("SignatureChecker", ["v4.1.0"]),
    "6a11687f7b7fc1433b269fd4abac331c66fa8a77": LibraryInfo("ERC1820Implementer", ["v4.1.0"]),
    "6eb9cd105fa9d0262ed7a11160b76381b39cebd5": LibraryInfo("IERC1820Registry", ["v4.1.0"]),
    "e91a667e7a573e6eea5d853b468e8f3d60d81889": LibraryInfo("EnumerableSet", ["v4.1.0"]),
    "5c61094952cd50d3802c31177357efd5d8964614": LibraryInfo("IAccessControl", ["v4.2.0"]),
    "8694d4f12fbafeb16850afc3464c06ea0a548a0a": LibraryInfo("AccessControl", ["v4.2.0"]),
    "28331601ee481fd4a956fdbe388c3abf54f3b65b": LibraryInfo("IAccessControlEnumerable", ["v4.2.0"]),
    "64d6a3bb174631f086b16b5e8486a5f794d976b7": LibraryInfo("AccessControlEnumerable", ["v4.2.0"]),
    "4d7c63c045201a4bb4b072b90c0ccb7e3da4f871": LibraryInfo(
        "Ownable", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "42b68abf0eec947d970be6ed8863108313d0af33": LibraryInfo(
        "PaymentSplitter", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "c1f9217c77f35c660dfb3d88d0406508c56488a6": LibraryInfo(
        "TimelockController", ["v4.2.0", "v4.3.0"]
    ),
    "bc8959ed38c71118622ffefeebc4c039b892709b": LibraryInfo(
        "IERC1271",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "0b811309fd111891492fcc5d96a2cb3acd8d72e9": LibraryInfo(
        "IERC3156FlashLender",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "b6f84fda4cb8fdbaa97a02726fa37281f78e5c91": LibraryInfo("ERC2771Context", ["v4.2.0"]),
    "42603ef9257bbe665bb87cffe0b376d7b67712ab": LibraryInfo(
        "MinimalForwarder",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "c2aec4893bc9a14ca843763da02fb355261d8a85": LibraryInfo(
        "AddressImpl",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "aa59563d28f55355429620d46a95f62807bf714c": LibraryInfo(
        "ArraysImpl",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "129786c0f640a54e1262bd0fa09c0402fa4f5310": LibraryInfo(
        "BadBeaconNoImpl",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "c7276d5682c391177c65742657733021762fde2e": LibraryInfo(
        "BitMapMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "da0acb035f001bc47226ca65e7805071ebcbc590": LibraryInfo(
        "ClashingImplementation",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "9a62fc52dfa77cec1a4fb20a17dc85c2b00165b0": LibraryInfo(
        "ClonesMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e319f874c429173e1b901ab7fc2014f7acc17b54": LibraryInfo(
        "ContextMockCaller",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "46564e62cbf056df3d249a990973bdb709e83c2b": LibraryInfo(
        "CountersImpl",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f89165a7467e5e4a909e2b013e8383263d133e18": LibraryInfo(
        "Create2Impl",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "5654add772b6dac7815ecc69eeb4c6da58f6ce7c": LibraryInfo(
        "Impl",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "9db5258aacf562685ca737ca2de3e42ab6d55a00": LibraryInfo(
        "DummyImplementation",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e2170d2050cc953a0791202b11eb01c352a015b3": LibraryInfo(
        "DummyImplementationV2",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "75a5093a9fb3b7de904b13481d04f0570bf5a6ff": LibraryInfo(
        "EIP712External",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "369690b5196bce6039aaec5397827ac325a7b4f5": LibraryInfo(
        "ERC1155BurnableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "ffc5443dbc5dd5285e2ded467043517e152a75cc": LibraryInfo(
        "ERC1155Mock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "b3a1f1f5c11bb12f910ba0e8d951451eae1d0292": LibraryInfo(
        "ERC1155PausableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "71fec413985069608d5a44630c2fdbd3b8418ccd": LibraryInfo(
        "ERC1155ReceiverMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "5cf44c06a1081d98ecd7e65cc1aae83995055909": LibraryInfo(
        "ERC1155SupplyMock", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2"]
    ),
    "ad0b6a02674048a5e3a3d4d4a551934a2c897c74": LibraryInfo(
        "SupportsInterfaceWithLookupMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "070505611a17dcef9932ae5eb779350f79698235": LibraryInfo(
        "ERC165InterfacesSupported",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "93bb8c99dfe0581125332fb3ebd0e3955144df3e": LibraryInfo(
        "ERC165NotSupported",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "6b299c538b2c135312b0c72d8af712c821f831a2": LibraryInfo(
        "ERC165Mock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "8fee474311bd35767aa7afb389d6e4799eb5b8cf": LibraryInfo(
        "ERC20BurnableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "bf3af764a6c36127b5ff5e46f045291de91933ec": LibraryInfo(
        "ERC20CappedMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "21c4be0176e151069878b58aae5a1d165223e6ce": LibraryInfo(
        "ERC20DecimalsMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "cd2d838c0fb41e79aae2433e909abc6c0e8122bf": LibraryInfo(
        "ERC20FlashMintMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f83b56148b0339522b662f03900cff6983c51850": LibraryInfo(
        "ERC20Mock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e28bdd635291e4e5aefef3245e353609f1515968": LibraryInfo(
        "ERC20PausableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "9b65c5d1a96a1e41eb6182254c051eece2af5c54": LibraryInfo(
        "ERC20PermitMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "2ba8af8608e5448e4715cda8e571bcc6cfd48963": LibraryInfo(
        "ERC20VotesCompMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "0ab46f9bd08b5723b1d914e41725574517a12ad6": LibraryInfo(
        "ERC20VotesMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "b1c70a189722a29fdab6b49e27b040472f5a2e16": LibraryInfo(
        "ERC20WrapperMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "62a9a8199169e0de7117864ee9d256bb4b52083e": LibraryInfo(
        "ERC2771ContextMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "ae5f39a87a79311e6e4ad375b3ade2b5e03131ea": LibraryInfo(
        "ERC3156FlashBorrowerMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e09d1048186c05d41f0015ba69aa70a86b243c00": LibraryInfo(
        "ERC721BurnableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "7fae99c0b5530d32609982b4d533509b8674f0ee": LibraryInfo(
        "ERC721EnumerableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "9578913f5871c5e1567c53da7d5675d75dc92747": LibraryInfo(
        "ERC721Mock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "449cd793d9e4639b31812292d0319b59b0ca8e55": LibraryInfo(
        "ERC721PausableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "b10cef059262dfabaeade8ff51fd80d2aaba7537": LibraryInfo(
        "ERC721ReceiverMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "85c61f773cca6fa57c335796e1ca1f5b98ea1485": LibraryInfo(
        "ERC721URIStorageMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "75e9ad33d99c316414a0d3506cab37488b722728": LibraryInfo(
        "ERC777Mock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "2af1eabb238c84878673e589fd69defacb92e040": LibraryInfo(
        "ERC777SenderRecipientMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "4ce3c0c2f9d135ac50c7075651c9b930daecd603": LibraryInfo(
        "EnumerableMapMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "867d1f1aa9db24d77f5ecb83a38eb4a60b09dce9": LibraryInfo(
        "EtherReceiverMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "a8e715f4952f7265ec539aba50e8eea7a45f924e": LibraryInfo(
        "InitializableMock", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "e67f151ab39236b0419d7e8b0a583c10e549efb3": LibraryInfo(
        "MathMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "1f337a2bbb0e83495566c6cff4791828463f973c": LibraryInfo(
        "MerkleProofWrapper", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "c02597d82e217259e7d73000bd1f2789d1c7cd61": LibraryInfo(
        "MulticallTest",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "517131a8a0737e26e7be43853b9c24ff6a20552d": LibraryInfo(
        "MulticallTokenMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "7fadf3b05e77e38e5049e165344022d1e624b617": LibraryInfo(
        "SampleHuman", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "769bdb6cddb7c34bb955535a6f0f77f49e98f292": LibraryInfo(
        "SampleMother", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "a2b8b3961965b90f6c7b4ecaa477bd0d77f8c7d7": LibraryInfo(
        "SampleGramps", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "504d033dfcae64d76986dcb5cb8c5be4d1dded4d": LibraryInfo(
        "SampleFather", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "86e3593fee13c15d567cc136bacdca20ea1e6101": LibraryInfo(
        "SampleChild", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "cb6a1051fd2f5bc747c3f773fc3af72c484ab3a7": LibraryInfo(
        "OwnableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "24cf84f54a22c4a772fe74d9f72853640e102262": LibraryInfo(
        "PausableMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "1167e7738408a66d3897f34aeef40c9ef438686e": LibraryInfo(
        "PullPaymentMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "a8fac5d6e42c033f8c2372dcb6ccdcfd37cc1437": LibraryInfo(
        "ReentrancyAttack",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "7b976c578c5adaf74bc18e387c7e12147609b8a7": LibraryInfo(
        "ReentrancyMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e66dfe8c2da2a470c76b3d0a0cfe5e7a7580de9a": LibraryInfo(
        "Implementation1",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "a1226699bd48b90ff377b53c4a70f27c25a9a16b": LibraryInfo(
        "Implementation2",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "c9e618dc47d2ac5cc6dbce47d9b0130d4cc9377e": LibraryInfo(
        "Implementation3",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "3ce30a36b36ec42b787dd5be03a12341207a7fa6": LibraryInfo(
        "Implementation4",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f29c76324fd21e33388b40bd77ace0ef9c5c0d41": LibraryInfo(
        "SafeCastMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "2689010b084a75537c8e662d0d4c1c82460a7661": LibraryInfo(
        "ERC20ReturnFalseMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "acc2c209743671f9c4e44c829247831bf350a0a0": LibraryInfo(
        "ERC20ReturnTrueMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "74fd9057d3dffcddeae355918b7644eaa8ef7244": LibraryInfo(
        "ERC20NoReturnMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "86229693a21d889433acfa056ae7db96ba4a6cef": LibraryInfo(
        "SafeERC20Wrapper",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "4823c60f1f994ca554eea1ecbfa81e5b83b5d561": LibraryInfo(
        "SafeMathMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "97db478067ab766d3fa0758aca22823b38c81327": LibraryInfo(
        "SignatureCheckerMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e826f1b32cee3777ae3a3d0bef3cd8c20ac9cf7d": LibraryInfo(
        "MigratableMockV1",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "2e635423850dc52ed5a3b9afdec568a0519c6402": LibraryInfo(
        "MigratableMockV2",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "27932bcd6aeb679027157cf623195bd425b3d85b": LibraryInfo(
        "MigratableMockV3",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "2786cb54d7147fd4c067acd9bcd2ccb9cc57dbd8": LibraryInfo(
        "StorageSlotMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "b17d5f234e99981e2caad9c0f56ffaa53ad3e125": LibraryInfo(
        "StringsMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "5df1b89723d0bdcc5d517d4317b9c32184247a15": LibraryInfo(
        "UUPSUpgradeableBrokenMock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "d90c57be785b0a21161e20792e434763a5617e42": LibraryInfo(
        "Clones",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "1a59f5b5a1457a6db4f0fde03cb7ae600702f205": LibraryInfo(
        "ERC1967Upgrade",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "3fb535ddf3bc10f6ee9803c6d0be51c32f15947c": LibraryInfo(
        "Proxy", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "dd95705feafaba2f8cf136c536916bc6e15679ce": LibraryInfo(
        "ProxyAdmin",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "4a8ef6e66df0839cd7aaab06e9e5101d0b427ab3": LibraryInfo(
        "TransparentUpgradeableProxy",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "04a6f67acb954ffe770a8a034c7b342ba53d470d": LibraryInfo(
        "Initializable", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0"]
    ),
    "dc77065c6d2328495a7a5373a4384cdfa419b536": LibraryInfo(
        "UUPSUpgradeable", ["v4.2.0", "v4.3.0", "v4.3.1"]
    ),
    "52cabe02daf5bc8b106eca66daf0d7a2af4a1c28": LibraryInfo(
        "Pausable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e087c5b92178714f1e90fa95c2eb7d96e584b267": LibraryInfo(
        "PullPayment",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "362780bb1082d2ee05b02fbf3586f2efdf55787d": LibraryInfo(
        "ReentrancyGuard", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "e0b83559902f4dbc79b69b31b5d5a55566f0a4d8": LibraryInfo("ERC1155", ["v4.2.0"]),
    "26a7097a902c5d0ec06e9afe7a1b16e919e04f4d": LibraryInfo(
        "IERC1155",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f7f86cc447e330c0f2fe6c75893393527f9f0b75": LibraryInfo(
        "IERC1155Receiver",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "dcc175b857019b96cc84b4b554e4078167fd8061": LibraryInfo(
        "ERC1155Burnable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "6dbb111b0880293ce2d796b20c6a84f2b39b537d": LibraryInfo(
        "ERC1155Pausable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "6c4f2cc4be0924e6b4ad2a9b3c46efb8054335ca": LibraryInfo(
        "ERC1155Supply", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2"]
    ),
    "0ba967a226fd02a14a5e8da8780b72a207f642df": LibraryInfo(
        "ERC1155PresetMinterPauser",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "8f6be89b0ce95a5a8507d0473dd6bdc86fc05893": LibraryInfo(
        "ERC1155Holder",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "3eed534c118e1b55d8807ccdace65018f8e6cbfd": LibraryInfo(
        "ERC1155Receiver",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "5861a2fbfab58b39cbd32dfc63795083f43d1e65": LibraryInfo("ERC20", ["v4.2.0"]),
    "eefc9e89d017a91a4ce1f87accc52538bb130e97": LibraryInfo(
        "IERC20", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "36c08003131ccd3493f61caa424d4ef45e40abef": LibraryInfo(
        "ERC20Burnable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "d577838d7d5ecc6f5fca04d568956aaf48c13597": LibraryInfo(
        "ERC20Capped",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "4f57398877163b33c21ce35e9e43b94b72d943ab": LibraryInfo("ERC20FlashMint", ["v4.2.0"]),
    "4a726b7b47a1ef62e108e4eabde5e35a24fd062e": LibraryInfo(
        "ERC20Pausable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "aa54946245c2f1991404df914c8a529eece3f57d": LibraryInfo(
        "ERC20Snapshot",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "370ff7cbbbcefc8776065285a30cda977191d936": LibraryInfo("ERC20Votes", ["v4.2.0"]),
    "6b887b5359c94e61da10ae9dbc82502becb4b45f": LibraryInfo(
        "ERC20VotesComp",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "a7bc491c206021ef00c4c58e34737ed6319ccf6e": LibraryInfo(
        "ERC20Wrapper",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "273d56d9e427a9c91ac82db0a87ecf5d1d4da973": LibraryInfo(
        "ERC20Permit",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "1d200e39cf5dd9bd315f3461c1a664558662d5e8": LibraryInfo(
        "IERC20Permit",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "d6bac8d6f8bff3ba4a2c45d3cf23101a81a093b3": LibraryInfo(
        "ERC20PresetMinterPauser",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f1eefb4a9491a1ca4f3c88a9d8518d110f7ab8e8": LibraryInfo(
        "SafeERC20",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "d53bbb9fbcdf3ed1c0ff29350e7c813dabf9a5ac": LibraryInfo(
        "TokenTimelock",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "2caaed78e7c5899dfdfdc82812a31048d90f11d7": LibraryInfo("ERC721", ["v4.2.0"]),
    "7899b986a2072f4ac72b129375c7eac5eee84c3e": LibraryInfo(
        "IERC721",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "15cb97070ec4da6593205c442a6fcae406e7af9a": LibraryInfo(
        "IERC721Receiver",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "ef9f288af616034ca45cbbfb70926273848a17c3": LibraryInfo(
        "ERC721Enumerable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "06ee92df7f5d22b92b723b7fa47a7163a8bee826": LibraryInfo(
        "ERC721Pausable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "29e0c18d75d521f4530bfd591cfea713a1f49e0c": LibraryInfo(
        "ERC721URIStorage",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "8f3477480c38a4dfda7d4192ea80511fd8eb063d": LibraryInfo(
        "IERC721Enumerable",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "7a4d553b1a0193fcf9fd4d9468bb5700c27db42b": LibraryInfo(
        "IERC721Metadata",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f3c528e97bbb7f9aac27c721e2d17cbc75be7ce5": LibraryInfo(
        "ERC721PresetMinterPauserAutoId",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "0093e17405d73820432e8da360f33ddc23308530": LibraryInfo(
        "ERC721Holder",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "ec44444770bfb356bacc955d93d5237656af1390": LibraryInfo(
        "ERC777", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "e0bfb77c486769ad6acb629279feaf28455cccc4": LibraryInfo(
        "IERC777",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "14955bd29186d48ce191852b38f761ce1622fef1": LibraryInfo("Address", ["v4.2.0"]),
    "5625fde14370990aa8d4d094ba822a866b36fbd3": LibraryInfo(
        "Arrays",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "4ac4dc8857640e049508901478e37e13576e9925": LibraryInfo(
        "Context",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "55cf39dc3f389da17665b6cff3c6b4c47ee5ae5f": LibraryInfo(
        "Counters",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "61ca214711b37f23de183403ef96eba568654e74": LibraryInfo(
        "Create2",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "abe82d145668c3c90d148f2ca2971ea0cdd3c9ed": LibraryInfo(
        "Multicall",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "3965655fb49d3d12cb7b48155c684401673fbb96": LibraryInfo(
        "Strings",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "db454d7154deefdcc0d1dea7d458b572c4a0a67b": LibraryInfo("ECDSA", ["v4.2.0"]),
    "4fea412076493cc56d86c5296289f1ccc4bd2638": LibraryInfo(
        "MerkleProof", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "8c92fa340338deb4146af78038d2f8195df99ed0": LibraryInfo("SignatureChecker", ["v4.2.0"]),
    "a94f50827517d3595fb4ea61c7357ef87858dd74": LibraryInfo(
        "EIP712", ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "2de350f849494c8ac4872728cd696d77f879efea": LibraryInfo(
        "Escrow",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "fc0669b213fd21fcbf82b48b6a5834a0e8e4797f": LibraryInfo(
        "RefundEscrow",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "ffbe0135815bb9d107067eac054384ce9c559853": LibraryInfo("ERC165Checker", ["v4.2.0"]),
    "6843b3e0971a80f76c78626e5fbd5816449c4891": LibraryInfo(
        "ERC1820Implementer",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "3ab18388a1564c59b08f34c40e49fba6ed2030fa": LibraryInfo(
        "IERC1820Registry",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e4a7521c8dfccec8ef656905b09facaee8dfdb01": LibraryInfo("Math", ["v4.2.0"]),
    "69e808bc327ca30cce6784a56944f386502da108": LibraryInfo(
        "SafeCast",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "e3d19a417652f39488237ae86f633fc55f37ddd8": LibraryInfo(
        "SafeMath",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "61d0bee3d53d397afc63ceb8f5aebb843ad4f58c": LibraryInfo("BitMaps", ["v4.2.0"]),
    "f4e98a17d92c50528ac5512cf6d19c28381a671a": LibraryInfo(
        "EnumerableMap",
        ["v4.2.0", "v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "034b7e7cc2490688bf19079ab52aca584c622a2d": LibraryInfo("EnumerableSet", ["v4.2.0"]),
    "3ff259364b811ce55fbaf0b7d6e145fe32532877": LibraryInfo(
        "AccessControl", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "982c66e73b9fd3c148d7f157a38fb08a074922a9": LibraryInfo(
        "AccessControlEnumerable", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "47e570ba4dfb58e4d36d325ca74008a1ac3a25ef": LibraryInfo(
        "IAccessControl",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "d78d847dd07ed931c12f77b0f7626eb4e0100745": LibraryInfo(
        "IAccessControlEnumerable",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "1f9a441bb3f9991cf0d8db4a0f7338155dc1135e": LibraryInfo(
        "Governor", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "c802a401fe1793af47cb8b418684023cd4d5361b": LibraryInfo(
        "IGovernor", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "5fd29ee0161a032ec9a5e86f2d8cd71f53bc6ed1": LibraryInfo(
        "GovernorCompatibilityBravo", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "0d8b9df97940d08bb323a575ef0d7060676ed260": LibraryInfo(
        "IGovernorCompatibilityBravo", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "54543b187e4d9f29dc31c819093f48d9969d7d8a": LibraryInfo(
        "GovernorCountingSimple", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "dae38923cfdcb3de8c354a88b7b13fc2ecc26e12": LibraryInfo(
        "GovernorProposalThreshold", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "946bb0a46b5c75167f052528a401a12768de1f45": LibraryInfo(
        "ICompoundTimelock",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "6d6fc8587f4cc604ecc04de3ee0f8377c88c2e38": LibraryInfo(
        "GovernorTimelockCompound", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "8a58931413fa94e76f02d330097fcfa9c1c48bd9": LibraryInfo(
        "GovernorTimelockControl",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "2eb8af93a3b36609392bf643c72a9d03f0a6f398": LibraryInfo(
        "GovernorVotes", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "fb68a921152337bcb1e01376223f4c55de026197": LibraryInfo(
        "GovernorVotesComp",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "f5c1995c54bbbda556c0b279624eb88f03cdea3f": LibraryInfo(
        "GovernorVotesQuorumFraction",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"],
    ),
    "bce8f84c0ec1c03925f2478e3a3fccb33f60f35e": LibraryInfo(
        "IGovernorTimelock",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "9bd35ec7f53dbd0a4a87d1a93c424f09916497f6": LibraryInfo(
        "IERC1363", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "898275960fb383e8850df71e6e26dc86a5af34ee": LibraryInfo(
        "IERC1363Receiver",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "8e978b1851c28780339fc78c1095ef2e9844ee55": LibraryInfo(
        "IERC1363Spender",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "8794d872af0a539cdb093481e698677eff5e2745": LibraryInfo(
        "IERC2981", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "e72cca0e88cb8abd72845272eb6c90402063a578": LibraryInfo(
        "IERC2612", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "2bfb18e3d399cff65ab9b803c1e058868d26387a": LibraryInfo(
        "ERC2771Context", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "88fb8242a3f1c90475facda5a92901c903676ce3": LibraryInfo(
        "ECDSAMock", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "339f780618b8638444d16c9e43ee94e0dedbd4d8": LibraryInfo(
        "EnumerableBytes32SetMock",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "a32259aa2046b09ffc5dc8b1a89cd3bbdf4163a1": LibraryInfo(
        "EnumerableAddressSetMock",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "47212bb1a4a0679b281ef4d5d1ff20b1d8e152e4": LibraryInfo(
        "EnumerableUintSetMock",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "6892b367ba9dbfecaf18e5ec15291d334a2a67a2": LibraryInfo(
        "GovernorCompMock", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "fa5c7c49cb08c80190788a5f66c38869fae7ae51": LibraryInfo(
        "GovernorCompatibilityBravoMock", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "aa27e63eb1eda7556b559ae08ed141575a001370": LibraryInfo(
        "GovernorMock", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "bc7e434e2afd6cea41ec96110028e63c2c55db42": LibraryInfo(
        "GovernorTimelockCompoundMock", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "d8b5430cf0a55144e3ebfb8a06f882614dbb7718": LibraryInfo(
        "GovernorTimelockControlMock", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "cce92ebddff5d610dca62d66c72c9cb83c62700f": LibraryInfo(
        "TimersBlockNumberImpl",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "83786236d97273dfc27838a31c523b1d362bf105": LibraryInfo(
        "TimersTimestampImpl",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "8a04dcf69374c0eb397038120d6f3efdcc2ffd76": LibraryInfo(
        "CompTimelock",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "60dfa68371a6272fc626fd9aae7e556621402067": LibraryInfo(
        "ERC1155", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "f0766528233a6368c8539a4627387175feb32b94": LibraryInfo(
        "ERC20", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "91e9f927a20d0de07df4ea6e3c2060bcca716ea3": LibraryInfo(
        "ERC20FlashMint", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "b655b4fbbb49760010632cc8d0fc006b15f0c4ee": LibraryInfo(
        "ERC20Votes", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "e92b2feb6b8539d301c2c4c66b91fdf11ab3a691": LibraryInfo(
        "ERC721", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "1fde194446c5afd545cc902213afbec2c87a46bd": LibraryInfo(
        "Address", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "6ced0927362ad42d906b44d8616661c2da119c84": LibraryInfo(
        "Timers", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "14c1e71a34bcc6538f8de689211c51c0ec0a8d11": LibraryInfo(
        "ECDSA", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3"]
    ),
    "b590e553b7df8030182c6ecb4721a9c5dad81c98": LibraryInfo(
        "SignatureChecker", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "eebebdb79c1b3e1f8ffcff988f929b6dc1eda7dc": LibraryInfo(
        "ERC165Checker",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "9f15868ec22f5af898a458488bc83dfe12bf8817": LibraryInfo(
        "Math", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "2d212d3ead2002233febe7e68c6851cb66449d97": LibraryInfo(
        "BitMaps", ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "1896e438b057c94ccba383036112041dd7cbad62": LibraryInfo(
        "EnumerableSet",
        ["v4.3.0", "v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"],
    ),
    "898b9a1a1bb87f2ca186905c385d3bca567eebb7": LibraryInfo(
        "TimelockController", ["v4.3.1", "v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "2219a93edab7ad1455f89d93bc04bfd6799232a1": LibraryInfo(
        "UUPSUpgradeable", ["v4.3.2", "v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "8b6ce0d7b4ad592774afeadd155078d4027ab95a": LibraryInfo(
        "ERC1155SupplyMock", ["v4.3.3", "v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "dba518f42d643a2286c0bf8eacd3613c53d85ca4": LibraryInfo("ERC1155Supply", ["v4.3.3"]),
    "a99091ffa64d372a750e960e401381eb95593793": LibraryInfo(
        "AccessControl", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "27faee4bc796dc15628234c0aff9f28e6a93eda9": LibraryInfo(
        "AccessControlEnumerable", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "bad3e51ef939deac2032e71376b598cdbfa12b14": LibraryInfo(
        "Ownable", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "5492770f5c3d20f1b82762f03356ef4fd6995126": LibraryInfo(
        "PaymentSplitter", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "c7fbf0739abbc9f1f60596b280bbd07bb4390681": LibraryInfo(
        "VestingWallet", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "f258a176329f89585b497b54a6c49c51dec02479": LibraryInfo(
        "Governor", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "13ef8f5e7fef9d50c289b20dc3b1ee35d9fc08a5": LibraryInfo(
        "IGovernor", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "84f5273d82b316b964e0094fedc4790215ae3f4a": LibraryInfo(
        "GovernorCompatibilityBravo", ["v4.4.0", "v4.4.1"]
    ),
    "828f00113b4c019ae42020b90286d6c0d902bc08": LibraryInfo(
        "IGovernorCompatibilityBravo", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "d60a1b5753981b2f04d1b3e8fe01856bca55d895": LibraryInfo(
        "GovernorCountingSimple", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "7b5312b7e518b77b9ca1807058090a7f27908f75": LibraryInfo(
        "GovernorProposalThreshold", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "5caea9b7191c8bf8fe302e98f69d61efe4a626cf": LibraryInfo(
        "GovernorSettings", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "392943039111895161ca27cf1884863f7f9a96b9": LibraryInfo(
        "GovernorTimelockCompound", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "bc5e88dd5c3e739eea0b8f33568044dd0a04abf7": LibraryInfo(
        "ECDSAMock", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "96506e6a865793695afaa9ba6149baf8acca2f1c": LibraryInfo(
        "GovernorCompMock", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "920beda23e95dc26939587a933619dfae19492c2": LibraryInfo(
        "GovernorCompatibilityBravoMock", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "00d7d368e9e122f5d5162e42c6247685e5c94a7a": LibraryInfo(
        "GovernorMock", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "6ba6c91c65d91381889a327f62e600e48bab91b5": LibraryInfo(
        "GovernorTimelockCompoundMock", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "22674de544356a14664077d9598afc866e1e08d3": LibraryInfo(
        "GovernorTimelockControlMock", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "308abb0377baa296b93206b78e0f17a7eacd5dd0": LibraryInfo(
        "MerkleProofWrapper", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "d594afd3a1d8065b0999fab33b33ee98afbb1a9e": LibraryInfo(
        "MyGovernor1", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "a6e00d1c93dca6635da940320b7ca27b97aac5a9": LibraryInfo(
        "MyGovernor2", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "73feea0db74075f5757321a99d1602d8255eb17f": LibraryInfo(
        "MyGovernor", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "514e3afefce9342035a181c08c0ec2ee4ea03640": LibraryInfo(
        "ReentrancyGuard", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "d324c57106e8a29e644543f66c6466102c4cff4d": LibraryInfo(
        "ERC1155", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "cdcb56b1b4f8d6c2baa0aad1d5d293975be3b6b6": LibraryInfo(
        "ERC1155Supply", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "642fb791ce5f30f714a33b8eadf51e3cc183f353": LibraryInfo(
        "ERC20Votes", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "5ea292ebdd2f061e9379b500f2fceba49ef00761": LibraryInfo(
        "ERC721", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "61ac98a69d3dfd3c15232499e2315581004d8522": LibraryInfo(
        "ECDSA", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "461520eae9f1d49bd16c01cdd05800f72633691d": LibraryInfo(
        "MerkleProof", ["v4.4.0", "v4.4.1", "v4.4.2"]
    ),
    "876796dde039fc6fe4b5d43d9ca6e411af135800": LibraryInfo(
        "EIP712", ["v4.4.0", "v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "81903dc774a37209651c9c2e0b2ba85b56f381f1": LibraryInfo(
        "InitializableMock", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "a0ec129eecdccb3a692f9be3661a19f39d1312e2": LibraryInfo(
        "ConstructorInitializableMock", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "f0b9b893ca9aad442d6d92dca525a1c5332c474b": LibraryInfo(
        "SampleHuman", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "1c97276a55c8d0090fa15d4b99d27deaa955e3b7": LibraryInfo(
        "SampleMother", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "26b8494cd75563c4d5f0b141c27c59065421eaf9": LibraryInfo(
        "SampleGramps", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "4fad92aa7e239a5a470b35c3ab8d1101c69c23a0": LibraryInfo(
        "SampleFather", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "31fd7aee4912ba9ae36ba4a04a4a05d9d2690afb": LibraryInfo(
        "SampleChild", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "eec4af0ee55aba5b65b0ac375db706b2541e5653": LibraryInfo(
        "Initializable", ["v4.4.1", "v4.4.2", "v4.5.0"]
    ),
    "94d8214a6855376d8fcde6f26316c8d848faeb6d": LibraryInfo(
        "GovernorCompatibilityBravo", ["v4.4.2", "v4.5.0"]
    ),
    "2a8c112fa192928eae7c1e7b8f8322fa7766121e": LibraryInfo(
        "CallReceiverMock", ["v4.4.2", "v4.5.0"]
    ),
    "f6b1a7502344283a76b1385153d5dbe17bd792ae": LibraryInfo("AccessControl", ["v4.5.0"]),
    "a1d8fc054c5d73114421ce0f143b4fabf3568d42": LibraryInfo("AccessControlEnumerable", ["v4.5.0"]),
    "7019d3d6e4cf90818adcc5d8f2034670cda85daf": LibraryInfo("Governor", ["v4.5.0"]),
    "dbbf75e8914cd4f0946c52f98d04f493e94dd620": LibraryInfo("IGovernor", ["v4.5.0"]),
    "c00e7da3dba00f6c11fdcbbf357b6dc18110e2b9": LibraryInfo(
        "GovernorPreventLateQuorum", ["v4.5.0"]
    ),
    "1bc4aae7c1537cd679c7193f3f7652101d30a892": LibraryInfo("GovernorTimelockCompound", ["v4.5.0"]),
    "58969c4290386e434b89e71174668703cec1ab45": LibraryInfo("GovernorTimelockControl", ["v4.5.0"]),
    "29836afa63a7f71b8afb1d048e444b4b75cd822b": LibraryInfo("GovernorVotes", ["v4.5.0"]),
    "800c4417f2601773c7bb90aaf81a1dea6f47485f": LibraryInfo(
        "GovernorVotesQuorumFraction", ["v4.5.0"]
    ),
    "5235772d4436eccec983d7c5edbd240052c9ba22": LibraryInfo("IVotes", ["v4.5.0"]),
    "563ff993a6b7d8def9f98ac8bbba2e0d260ceff0": LibraryInfo("Votes", ["v4.5.0"]),
    "287623ca3a4ee8b95286d73ba6b2ed74b31aa56e": LibraryInfo("IERC2981", ["v4.5.0"]),
    "2d3287e3ef37104daa848d29ba9e569939dfb421": LibraryInfo("IERC1822Proxiable", ["v4.5.0"]),
    "55a1a0a2c8d2703791c32dbbe88d26107897fc53": LibraryInfo("ERC2771Context", ["v4.5.0"]),
    "0f78a22d966157b538e172ee646c8b2aa2ddcce5": LibraryInfo("MinimalForwarder", ["v4.5.0"]),
    "2ba4a77e01e137cab1d1ad573bae7e2bfef25b8f": LibraryInfo("Base64Mock", ["v4.5.0"]),
    "9ad73f0552ac99d3e074b3c630658afda1049412": LibraryInfo("CheckpointsImpl", ["v4.5.0"]),
    "660557bd64e5e8e21d5d45f4ee8fb6ad951d0452": LibraryInfo("ERC2771ContextMock", ["v4.5.0"]),
    "ea0f405b0d5c246931e84d1375055083872f097c": LibraryInfo("ERC721RoyaltyMock", ["v4.5.0"]),
    "e0e331829d37789f4c66f72174b609e65e382d54": LibraryInfo("ERC721VotesMock", ["v4.5.0"]),
    "c67fdb73a1ebdc6f94bd34f84f7410d860b179d4": LibraryInfo("GovernorMock", ["v4.5.0"]),
    "3d5d49916ab335e7e63e6ac8c6bbdde4ce91774a": LibraryInfo(
        "GovernorPreventLateQuorumMock", ["v4.5.0"]
    ),
    "846f47565f55b3ce4e7e1991a4f76a0f6d257cae": LibraryInfo(
        "GovernorTimelockCompoundMock", ["v4.5.0"]
    ),
    "d80b0d79f0062440f20d9cd7992ef3b6412d74ee": LibraryInfo(
        "GovernorTimelockControlMock", ["v4.5.0"]
    ),
    "50fc19942debe7b63d6307cc2ad4f485739a4f6f": LibraryInfo("GovernorVoteMocks", ["v4.5.0"]),
    "50c9c79167cff6cae0533e799ccb7da86cf72d90": LibraryInfo("ERC20ReturnFalseMock", ["v4.5.0"]),
    "1306e3dd922f348e0ad76610cec7acfbb1363489": LibraryInfo("SignedMathMock", ["v4.5.0"]),
    "fb165320294354e11a7e2d11e8c1b73000dac9c7": LibraryInfo(
        "UUPSUpgradeableLegacyMock", ["v4.5.0"]
    ),
    "794af8bd5c3a40c9e038b52ec27b22abcb52c8bb": LibraryInfo("VotesMock", ["v4.5.0"]),
    "a3dc30773372880a622a3577d2097f9976622b0b": LibraryInfo("MyGovernor1", ["v4.5.0"]),
    "b154ab0518de330d71a343878580a2dd4130c6cd": LibraryInfo("MyGovernor2", ["v4.5.0"]),
    "20d2a2d2701c4357b2abce38302a1caa427ae884": LibraryInfo("MyGovernor", ["v4.5.0"]),
    "6bc0b1abdafe6cd09f3b89d0a2204361106cd29d": LibraryInfo("ERC1967Upgrade", ["v4.5.0"]),
    "1cce6c0614504a6d6ee709651a1182a1cbba8e2e": LibraryInfo("Proxy", ["v4.5.0"]),
    "dd05a2a306a051e1c4c381d967584d02c114038a": LibraryInfo("UUPSUpgradeable", ["v4.5.0"]),
    "2f99143bf51f009a94948a12b8ee5b5af48743c6": LibraryInfo("IERC1155Receiver", ["v4.5.0"]),
    "dfd6949ce9bb4cf1b409dec313064e123de4d18d": LibraryInfo("ERC20", ["v4.5.0"]),
    "6fa24eddd6020e757903a86dd74f335e9d6d92ae": LibraryInfo("IERC20", ["v4.5.0"]),
    "6137641e7029f78ccdb9ed7576394655140f1687": LibraryInfo("ERC20Burnable", ["v4.5.0"]),
    "630204f30f220515a71dada488ef5e2b5f8cac65": LibraryInfo("ERC20FlashMint", ["v4.5.0"]),
    "f132d224bf01c7af2adab4143b27eb01e3af3908": LibraryInfo("ERC20Votes", ["v4.5.0"]),
    "c78fb00bcac30eac9c9f09370bfb134f1fb0dace": LibraryInfo("ERC20VotesComp", ["v4.5.0"]),
    "73965f3b502d3eb2c7b119a1a3385dbbf61431e1": LibraryInfo("TokenTimelock", ["v4.5.0"]),
    "d1216cfae4bd3a10f1d1875dfff6d645866adf43": LibraryInfo("ERC721", ["v4.5.0"]),
    "bf9ad9a6de08088c645ff86bdf875c0beac8a3b5": LibraryInfo("ERC721Royalty", ["v4.5.0"]),
    "a8385ddba748ac6b2d17f1c342aba1e9b5d6927d": LibraryInfo("IERC721Enumerable", ["v4.5.0"]),
    "6f84eff1a9116fbf20abd5c4457e4897ab40a415": LibraryInfo("ERC721Votes", ["v4.5.0"]),
    "b457774f9fc82764468c9438603124f1243e042f": LibraryInfo("ERC777", ["v4.5.0"]),
    "89520f76f5c9a9c6bad97750f2e01377f76bad6f": LibraryInfo("ERC2981", ["v4.5.0"]),
    "be306f01ae84e9a1a568f703b8bcc9b1a0c49898": LibraryInfo("Address", ["v4.5.0"]),
    "3bc96067d15f810ae58d139dd854197d0c3be98a": LibraryInfo("Base64", ["v4.5.0"]),
    "0802f0deda6bb9b59cdbe73a5e5c6a238ea5668b": LibraryInfo("Checkpoints", ["v4.5.0"]),
    "fc9ecdcc8173f23d1db2eecc243d1ab3999dbe35": LibraryInfo("Multicall", ["v4.5.0"]),
    "68081d1d7d71bcdbb1507f31b71fe09f66b5ad21": LibraryInfo("ECDSA", ["v4.5.0"]),
    "33ea0fbdba5f8542328ddac5067b9384c8988296": LibraryInfo("MerkleProof", ["v4.5.0"]),
    "1c3856f541a8333183cfecbed1f6034030f2dd2a": LibraryInfo("SignatureChecker", ["v4.5.0"]),
    "29e09293303b76a688d81e63b7c3469ef5459b59": LibraryInfo("SignedMath", ["v4.5.0"]),
}
