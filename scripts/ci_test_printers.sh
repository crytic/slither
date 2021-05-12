#!/usr/bin/env bash

### Test printer 

cd tests/ast-parsing/compile || exit

# Do not test the evm printer,as it needs a refactoring
ALL_PRINTERS="cfg,constructor-calls,contract-summary,data-dependency,echidna,function-id,function-summary,modifiers,call-graph,human-summary,inheritance,inheritance-graph,slithir,slithir-ssa,vars-and-auth,require,variable-order"

# Only test 0.5.17 to limit test time
for file in *0.5.17-compact.zip; do
  if ! slither "$file" --print "$ALL_PRINTERS" > /dev/null 2>&1 ; then
    echo "Printer failed"
    echo "$file"
    exit 1
  fi
done


slither examples/scripts/test_evm_api.sol --print evm 
