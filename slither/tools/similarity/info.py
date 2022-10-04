import logging
import sys
import os.path
import traceback

from .model import load_model
from .encode import parse_target, encode_contract

logging.basicConfig()
logger = logging.getLogger("Slither-simil")


def info(args):

    try:

        model = args.model
        if os.path.isfile(model):
            model = load_model(model)
        else:
            model = None

        filename = args.filename
        contract, fname = parse_target(args.fname)

        if filename is None and contract is None and fname is None:
            logger.info("%s uses the following words:", args.model)
            for word in model.get_words():
                logger.info(word)
            sys.exit(0)

        if filename is None or contract is None or fname is None:
            logger.error("The encode mode requires filename, contract and fname parameters.")
            sys.exit(-1)

        irs = encode_contract(filename, **vars(args))
        if len(irs) == 0:
            sys.exit(-1)

        x = (filename, contract, fname)
        y = " ".join(irs[x])

        to_log = f"Function {fname} in contract {contract} is encoded as:"
        logger.info(to_log)
        logger.info(y)
        if model is not None:
            fvector = model.get_sentence_vector(y)
            logger.info(fvector)

    except Exception:  # pylint: disable=broad-except
        to_log = f"Error in {args.filename}"
        logger.error(to_log)
        logger.error(traceback.format_exc())
        sys.exit(-1)
