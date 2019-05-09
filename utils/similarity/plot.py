import logging
import sys
import traceback
import operator
import numpy as np
import random

try:
    from sklearn import decomposition
    import matplotlib.pyplot as plt
except ImportError:
    decomposition = None
    plt = None
    
from fastText import load_model
from .encode import load_and_encode

logger = logging.getLogger("Slither-simil")

def plot(args):

    if decomposition is None or plt is None:
        logger.error("ERROR: In order to use plot mode in slither-simil, you need to install sklearn and matplotlib:")
        logger.error("$ pip3 install sklearn matplotlib --user")
        sys.exit(-1)

    try:

        model = args.model
        model = load_model(model)
        filename = args.filename
        contract = args.contract
        fname = args.fname
        solc = args.solc
        infile = args.input
        ext = args.filter
        nsamples = args.nsamples

        if fname is None or infile is None:
            logger.error('The plot mode requieres fname and input parameters.')
            sys.exit(-1)

        logger.info('Loading data..')
        cache = load_and_encode(infile, model, ext=ext, solc=solc, nsamples=nsamples)

        data = list()
        fs = list()

        logger.info('Procesing data..')
        for (f,c,n),y in cache.items():
            if (c == contract or contract is None) and n == fname:
                fs.append(f)
                data.append(y)

        if len(data) == 0:
            logger.error('No contract was found with function %s', fname)
            sys.exit(-1)

        data = np.array(data)
        pca = decomposition.PCA(n_components=2)
        tdata = pca.fit_transform(data)

        logger.info('Plotting data..')
        plt.figure()
        assert(len(tdata) == len(fs))
        for ([x,y],l) in zip(tdata, fs):
            x = random.gauss(0, 0.01) + x
            y = random.gauss(0, 0.01) + y
            plt.scatter(x, y, c='blue')
            plt.text(x-0.001,y+0.001, l)

        logger.info('Saving figure to plot.png..')
        plt.savefig('plot.png', bbox_inches='tight')
 
    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
