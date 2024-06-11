from setuptools import setup, find_packages

setup(
    name="slither_my_plugin",
    description="This is an example of detectors and printers to Slither.",
    url="https://github.com/trailofbits/slither-plugins",
    author="Trail of Bits",
    version="0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=["slither-analyzer>=0.6.0"],
    entry_points={
        "slither_analyzer.plugin": "slither my-plugin=slither_my_plugin:make_plugin",
    },
)
