import sys
import logging
import subprocess

import os.path
from solcParsing.slitherSolc import SlitherSolc
from utils.colors import red

logger = logging.getLogger("Slither")
logging.basicConfig()

class Slither(SlitherSolc):

    def __init__(self, filename, solc='solc', disable_solc_warnings=False ,solc_arguments=''):

        if not os.path.isfile(filename):
            logger.error('{} does not exist (are you in the correct directory?)'.format(filename))
            exit(-1)
        is_ast_file = False
        if filename.endswith('json'):
            is_ast_file = True
        elif not filename.endswith('.sol'):
            raise Exception('Incorrect file format')

        if is_ast_file:
            with open(filename) as astFile:
                data = astFile.read()
                if not data:
                    logger.info('Empty AST file: %s', filename)
                    sys.exit(-1)
        else:
            cmd = [solc, filename, '--ast-json']
            if solc_arguments:
                # To parse, we first split the string on each '--'
                solc_args = solc_arguments.split('--')
                # Split each argument on the first space found
                # One solc option may have multiple argument sepparated with ' '
                # For example: --allow-paths /tmp .
                # split() removes the delimiter, so we add it again
                solc_args = [('--'+x).split(' ', 1) for x in solc_args if x]
                # Flat the list of list
                solc_args = [item for sublist in solc_args for item in sublist]
                cmd += solc_args
            # Add . as default allowed path
            if '--allow-paths' not in cmd:
                cmd += ['--allow-paths', '.']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            data, err = process.communicate()

            if err and (not disable_solc_warnings):
                err = err.split('\n')
                err = [x if 'Error' not in x else red(x) for x in err]
                err = '\n'.join(err)
                logger.info('Compilation warnings/errors on %s:\n%s', filename, err)


        data = data.split('\n=')

        super(Slither, self).__init__(filename)
        for d in data:
            self.parse_contracts_from_json(d)

        self.analyze_contracts()



