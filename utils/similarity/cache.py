import numpy as np

from .encode import encode_contract, load_contracts

def load_cache(infile, model, ext=None, solc='solc'):
    cache = dict()
    if infile.endswith(".npz"):
        with np.load(infile) as data:
            array = data['arr_0'][0]
            for x,y in array:
                cache[x] = y
    else: 
        contracts = load_contracts(infile, ext=ext)
        for contract in contracts:
            for x,ir in encode_contract(contract, solc=solc).items():
                if ir != []:
                    y = " ".join(ir)
                    cache[x] = model.get_sentence_vector(y)
    return cache

def save_cache(cache, outfile):
    np.savez(outfile,[np.array(cache)])
