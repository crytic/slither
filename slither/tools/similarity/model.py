import sys

try:
    from fasttext import load_model
    from fasttext import train_unsupervised
except ImportError:
    #print("ERROR: in order to use slither-simil, you need to install fasttext 0.2.0:")
    #print("$ pip3 install https://github.com/facebookresearch/fasttext/archive/0.2.0.zip --user\n")
    print("ERROR: in order to use slither-simil, you need to install the latest fasttext version (Currently test with 0.9.2 [Apr 28, 2020]):")
    print("$ git clone https://github.com/facebookresearch/fastText.git\n$cd fastText\npipi3 install . --user\n")
    sys.exit(-1)
