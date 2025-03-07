#!/usr/bin/env bash

test_examples(){
    cd examples

    python print_basic_information.py > results.txt 
    if [ $? -ne 0 ]
    then
        exit -1
    fi

    DIFF=$(diff results.txt expected_results_print_basic_information.txt)
    
    if [  "$DIFF" != "" ] 
    then
        echo "print_basic_information.py failed"
        cat results.txt
        echo ""
        cat expected_results_print_basic_information.txt
        echo ""
        echo "$DIFF"
        exit -1
    fi

    echo "print_basic_information.py passed"
    cd ..
}

test_exercise(){
    cd "exercises/exercise$1"

    python solution.py > results.txt 
    if [ $? -ne 0 ]
    then
        exit -1
    fi

    DIFF=$(diff results.txt expected_results.txt)

    if [  "$DIFF" != "" ] 
    then
        echo "exercise $1 failed"
        cat results.txt
        echo ""
        cat expected_results.txt
        echo ""
        echo "$DIFF"
        exit -1
    fi

    echo "exercise $1 passed"
    cd ../..
}


cd program-analysis/slither
pip install slither-analyzer
solc-select install 0.8.20
solc-select use 0.8.20

test_examples

solc-select install 0.5.11
solc-select use 0.5.11
test_exercise 1

solc-select use 0.8.20
test_exercise 2

test_exercise 3

echo "Slither tests passed"

