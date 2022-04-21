from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="slither-analyzer",
    description="Slither is a Solidity static analysis framework written in Python 3.",
    url="https://github.com/crytic/slither",
    author="Trail of Bits",
    version="0.8.3",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "prettytable>=0.7.2",
        "pysha3>=1.0.2",
        "crytic-compile>=0.2.3",
        # "crytic-compile",
    ],
    # dependency_links=["git+https://github.com/crytic/crytic-compile.git@master#egg=crytic-compile"],
    license="AGPL-3.0",
    long_description=long_description,
    entry_points={
        "console_scripts": [
            "slither = slither.__main__:main",
            "slither-check-upgradeability = slither.tools.upgradeability.__main__:main",
            "slither-find-paths = slither.tools.possible_paths.__main__:main",
            "slither-simil = slither.tools.similarity.__main__:main",
            "slither-flat = slither.tools.flattening.__main__:main",
            "slither-format = slither.tools.slither_format.__main__:main",
            "slither-check-erc = slither.tools.erc_conformance.__main__:main",
            "slither-check-kspec = slither.tools.kspec_coverage.__main__:main",
            "slither-prop = slither.tools.properties.__main__:main",
            "slither-mutate = slither.tools.mutator.__main__:main",
            "slither-read-storage = slither.tools.read_storage.__main__:main",
        ]
    },
)
