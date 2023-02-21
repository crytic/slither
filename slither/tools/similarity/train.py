import argparse
import logging
import os
import sys
import traceback

from slither.tools.similarity.cache import save_cache
from slither.tools.similarity.encode import encode_contract, load_contracts
from slither.tools.similarity.model import train_unsupervised

logger = logging.getLogger("Slither-simil")


def train(args: argparse.Namespace) -> None:  # pylint: disable=too-many-locals

    try:
        last_data_train_filename = "last_data_train.txt"
        model_filename = args.model
        dirname = args.input

        if dirname is None:
            logger.error("The train mode requires the input parameter.")
            sys.exit(-1)

        contracts = load_contracts(dirname, **vars(args))
        logger.info("Saving extracted data into %s", last_data_train_filename)
        cache = []
        with open(last_data_train_filename, "w", encoding="utf8") as f:
            for filename in contracts:
                # cache[filename] = dict()
                for (filename_inner, contract, function), ir in encode_contract(
                    filename, **vars(args)
                ).items():
                    if ir != []:
                        x = " ".join(ir)
                        f.write(x + "\n")
                        cache.append((os.path.split(filename_inner)[-1], contract, function, x))

        logger.info("Starting training")
        model = train_unsupervised(input=last_data_train_filename, model="skipgram")
        logger.info("Training complete")
        logger.info("Saving model")
        model.save_model(model_filename)

        for i, (filename, contract, function, irs) in enumerate(cache):
            cache[i] = ((filename, contract, function), model.get_sentence_vector(irs))

        logger.info("Saving cache in cache.npz")
        save_cache(cache, "cache.npz")
        logger.info("Done!")

    except Exception:  # pylint: disable=broad-except
        logger.error(f"Error in {args.filename}")
        logger.error(traceback.format_exc())
        sys.exit(-1)
