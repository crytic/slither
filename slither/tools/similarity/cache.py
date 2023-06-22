import sys
from typing import Dict, Optional

try:
    import numpy as np
except ImportError:
    print("ERROR: in order to use slither-simil, you need to install numpy")
    print("$ pip3 install numpy --user\n")
    sys.exit(-1)


def load_cache(infile: str, nsamples: Optional[int] = None) -> Dict:
    cache = {}
    with np.load(infile, allow_pickle=True) as data:
        array = data["arr_0"][0]
        for i, (x, y) in enumerate(array):
            cache[x] = y
            if i == nsamples:
                break

    return cache


def save_cache(cache: Dict, outfile: str) -> None:
    np.savez(outfile, [np.array(cache)])
