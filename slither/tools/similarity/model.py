import sys

try:
    from fasttext import load_model
    from fasttext import train_unsupervised
except ImportError:
    print("ERROR: in order to use slither-simil, you need to install fasttext>=0.2.0:")
    print("$ pip3 install fasttext --user\n")
    sys.exit(-1)
