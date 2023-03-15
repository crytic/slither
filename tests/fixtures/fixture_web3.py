import sys

import pytest
from tests.fixtures.ganache_instance import GanacheInstance

try:
    from web3 import Web3
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)


@pytest.fixture(scope="module", name="web3")
def fixture_web3(ganache: GanacheInstance):
    w3 = Web3(Web3.HTTPProvider(ganache.provider, request_kwargs={"timeout": 30}))
    return w3
