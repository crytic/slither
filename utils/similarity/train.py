import argparse
import logging
import sys
import traceback
import operator
import os

from fastText import train_unsupervised
from .encode  import encode_contract, load_contracts
from .cache   import save_cache

logger = logging.getLogger("Slither-simil")

def train(args):

    try:
        last_data_train_filename = "last_data_train.txt"
        model_filename = args.model
        solc = args.solc
        dirname = args.input
        ext = args.filter
        nsamples = args.nsamples

        if dirname is None:
            logger.error('The train mode requires the input parameter.')
            sys.exit(-1)

        contracts = load_contracts(dirname, ext=ext, nsamples=nsamples)
        logger.info('Saving extracted data into', last_data_train_filename)
        cache = []
        with open(last_data_train_filename, 'w') as f:
            for filename in contracts:
                #cache[filename] = dict()
                for (filename, contract, function), ir in encode_contract(filename,solc).items():
                    if ir != []:
                        x = " ".join(ir)
                        f.write(x+"\n")
                        cache.append((os.path.split(filename)[-1], contract, function, x))

        logger.info('Starting training')
        model = train_unsupervised(input=last_data_train_filename, model='skipgram')
        logger.info('Training complete')
        model.save_model(model_filename)

        for i,(filename, contract, function, irs) in enumerate(cache):
            cache[i] = ((filename, contract, function), model.get_sentence_vector(irs))

        logger.info('Saved cache in cache.npz')
        save_cache(cache, "cache.npz")
 
    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
