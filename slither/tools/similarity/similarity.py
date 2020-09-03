import sys

try:
    import numpy as np
except ImportError:
    print("ERROR: in order to use slither-simil, you need to install numpy:")
    print("$ pip3 install numpy --user\n")
    sys.exit(-1)


def similarity(v1, v2):
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    return np.dot(v1, v2) / n1 / n2
