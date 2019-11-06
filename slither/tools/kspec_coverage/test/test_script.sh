#!/bin/bash

set -x

# Klab examples from https://github.com/dapphub/klab/tree/master/examples
slither-kspec-coverage ./token/token.sol ./token/spec.md
slither-kspec-coverage ./heal/vat.sol ./heal/spec.md
slither-kspec-coverage ./safeAdd/safeAdd.sol ./safeAdd/spec.md
slither-kspec-coverage ./multipleCalls/easyNest.sol ./multipleCalls/spec.md
slither-kspec-coverage ./multipleInternals/constant.sol ./multipleInternals/spec.md

# Makerdao
slither-kspec-coverage ./makerdao/cat.sol ./makerdao/spec_cat.md
slither-kspec-coverage ./makerdao/dai.sol ./makerdao/spec_dai.md
slither-kspec-coverage ./makerdao/end.sol ./makerdao/spec_end.md
slither-kspec-coverage ./makerdao/flap.sol ./makerdao/spec_flapper.md
slither-kspec-coverage ./makerdao/flip.sol ./makerdao/spec_flipper.md
slither-kspec-coverage ./makerdao/flop.sol ./makerdao/spec_flopper.md
slither-kspec-coverage ./makerdao/join.sol ./makerdao/spec_gemJoin.md
slither-kspec-coverage ./makerdao/join.sol ./makerdao/spec_daiJoin.md
slither-kspec-coverage ./makerdao/jug.sol ./makerdao/spec_jug.md
slither-kspec-coverage ./makerdao/pot.sol ./makerdao/spec_pot.md
slither-kspec-coverage ./makerdao/spot.sol ./makerdao/spec_spotter.md
slither-kspec-coverage ./makerdao/vat.sol ./makerdao/spec_vat.md
slither-kspec-coverage ./makerdao/vow.sol ./makerdao/spec_vow.md





