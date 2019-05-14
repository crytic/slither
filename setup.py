from setuptools import setup, find_packages

setup(
    name='slither-analyzer',
    description='Slither is a Solidity static analysis framework written in Python 3.',
    url='https://github.com/crytic/slither',
    author='Trail of Bits',
    version='0.6.3',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=['prettytable>=0.7.2', 'pysha3>=1.0.2', 'crytic-compile>=0.1.1'],
    license='AGPL-3.0',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'slither = slither.__main__:main',
            'slither-check-upgradeability = utils.upgradeability.__main__:main',
            'slither-find-paths = utils.possible_paths.__main__:main',
            'slither-simil = utils.similarity.__main__:main'
        ]
    }
)
