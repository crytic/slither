from solc_select import solc_select
from slither import Slither
from slither.detectors.all_detectors import DomainSeparatorCollision


def test_permit_domain_collision():
    """There is not a (known) collision for this function signature
    so this test mutates a function's name to mock it.
    """
    solc_select.switch_global_version("0.8.0", always_install=True)
    sl = Slither("tests/mock_permit_domain_collision.sol")
    assert len(sl.contracts_derived) == 1
    contract = sl.contracts_derived[0]
    # This will memoize the solidity signature and mutating the name
    # won't change the function selector calculated
    func = contract.get_function_from_signature("DOMAIN_SEPARATOR()")
    # Change the name to mock
    func.name = "MOCK_COLLISION"
    sl.register_detector(DomainSeparatorCollision)
    results = sl.run_detectors()
    assert len(results) == 1
