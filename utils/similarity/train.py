import argparse
import logging
import sys
import traceback
import operator

from fastText import train_unsupervised
from .encode import encode_contract, load_contracts

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
        with open(last_data_train_filename, 'w') as f:
            for contract in contracts: 
                for function,ir in encode_contract(contract,solc).items():
                    if ir != []:
                        f.write(" ".join(ir)+"\n")
    
        model = train_unsupervised(input=last_data_train_filename, model='skipgram')
        model.save_model(model_filename)
        print(model.get_words())
 
    except Exception:
        logger.error('Error in %s' % args.filename)
        logger.error(traceback.format_exc())
        sys.exit(-1)
