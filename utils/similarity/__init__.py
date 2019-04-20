# from https://stackoverflow.com/questions/563022/whats-python-good-practice-for-importing-and-offering-optional-features
import sys

try:
    import fastText
except ImportError:
    fastText = None

if fastText is None:
    print("ERROR: in order to use slither-simil, you need to install fastText 0.2.0:")
    print("$ pip3 install https://github.com/facebookresearch/fastText/archive/0.2.0.zip --user\n")
    sys.exit(-1)
