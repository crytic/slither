import sys

try:
    from fastText import load_model
    from fastText import train_unsupervised
except ImportError:
    print("ERROR: in order to use slither-simil, you need to install fastText 0.2.0:")
    print("$ pip3 install https://github.com/facebookresearch/fastText/archive/0.2.0.zip --user\n")
    sys.exit(-1)
