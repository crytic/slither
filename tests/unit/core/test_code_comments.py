from pathlib import Path

from slither import Slither


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
CUSTOM_COMMENTS_TEST_DATA_DIR = Path(TEST_DATA_DIR, "custom_comments")


def test_upgradeable_comments(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.10")
    slither = Slither(Path(CUSTOM_COMMENTS_TEST_DATA_DIR, "upgrade.sol").as_posix(), solc=solc_path)
    compilation_unit = slither.compilation_units[0]
    proxy = compilation_unit.get_contract_from_name("Proxy")[0]

    assert proxy.is_upgradeable_proxy

    v0 = compilation_unit.get_contract_from_name("V0")[0]

    assert v0.is_upgradeable
    print(v0.upgradeable_version)
    assert v0.upgradeable_version == "version-0"

    v1 = compilation_unit.get_contract_from_name("V1")[0]
    assert v0.is_upgradeable
    assert v1.upgradeable_version == "version_1"


def test_contract_comments(solc_binary_path) -> None:
    comments = " @title Test Contract\n @dev Test comment"

    solc_path = solc_binary_path("0.8.10")
    slither = Slither(
        Path(CUSTOM_COMMENTS_TEST_DATA_DIR, "contract_comment.sol").as_posix(), solc=solc_path
    )
    compilation_unit = slither.compilation_units[0]
    contract = compilation_unit.get_contract_from_name("A")[0]

    assert contract.comments == comments

    # Old solc versions have a different parsing of comments
    # the initial space (after *) is also not kept on every line
    comments = "@title Test Contract\n@dev Test comment"
    solc_path = solc_binary_path("0.5.16")
    slither = Slither(
        Path(CUSTOM_COMMENTS_TEST_DATA_DIR, "contract_comment.sol").as_posix(), solc=solc_path
    )
    compilation_unit = slither.compilation_units[0]
    contract = compilation_unit.get_contract_from_name("A")[0]

    assert contract.comments == comments

    # Test with legacy AST
    comments = "@title Test Contract\n@dev Test comment"
    slither = Slither(
        Path(CUSTOM_COMMENTS_TEST_DATA_DIR, "contract_comment.sol").as_posix(),
        solc_force_legacy_json=True,
        solc=solc_path,
    )
    compilation_unit = slither.compilation_units[0]
    contract = compilation_unit.get_contract_from_name("A")[0]

    assert contract.comments == comments
