from setuptools import setup, find_packages

setup(
    name='slither-analyzer',
    description='Slither is a Solidity static analysis framework written in Python 3.',
    url='https://github.com/trailofbits/slither',
    author='Trail of Bits',
    version='0.5.0',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=['prettytable>=0.7.2'],
    license='AGPL-3.0',
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'slither = slither.__main__:main'
        ]
    }
)
