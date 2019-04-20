import logging
import sys
import traceback
import operator
import numpy as np
import random

from sklearn import decomposition
import matplotlib.pyplot as plt

from fastText import load_model
from .cache import load_cache

logger = logging.getLogger("crytic-pred")

def plot(args):

    try:
        model = args.model
        model = load_model(model)
        filename = args.filename
        contract = args.contract
        fname = args.fname
        solc = args.solc
        infile = args.input
        ext = args.filter

        if contract is None or fname is None or infile is None:
            logger.error('The plot mode requieres contract, fname and input parameters.')
            sys.exit(-1)

        cache = load_cache(infile, model, ext=ext, solc=solc)
        #save_cache("cache.npz", cache)

        data = list()
        fs = list()
        for (f,c,n),y in cache.items():
            if c == contract and n == fname:
                fs.append(f)
                data.append(y)
            #r[x] = similarity(fvector, y)

       
        data = np.array(data)
        pca = decomposition.PCA(n_components=2)
        tdata = pca.fit_transform(data)
        plt.figure()
        assert(len(tdata) == len(fs))
        for ([x,y],l) in zip(tdata, fs):
            x = random.gauss(0, 0.01) + x
            y = random.gauss(0, 0.01) + y
            plt.scatter(x, y, c='blue')
            plt.text(x-0.001,y+0.001, l.split("_")[1].replace(".sol.ast.compact.json",""))

        plt.show()
        #r = sorted(r.items(), key=operator.itemgetter(1), reverse=True)
        #for x,score in r[:10]:
 
    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
