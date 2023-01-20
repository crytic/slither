from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="slither-analyzer",
    description="Slither is a Solidity static analysis framework written in Python 3.",
    url="https://github.com/crytic/slither",
    author="Trail of Bits",
    version="0.9.2",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "packaging",
        "prettytable>=0.7.2",
        "pycryptodome>=3.4.6",
        "crytic-compile>=0.3.0",
        # "crytic-compile@git+https://github.com/crytic/crytic-compile.git@master#egg=crytic-compile",
    ],
    extras_require={
        "dev": [
            "black==22.3.0",
            "pylint==2.13.4",
            "pytest",
            "pytest-cov",
            "deepdiff",
            "numpy",
            "solc-select>=v1.0.0b1",
            "openai",
        ]
    },
    license="AGPL-3.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
            "slither-doctor = slither.tools.doctor.__main__:main",
            "slither-documentation = slither.tools.documentation.__main__:main",
        ]
    },
)
