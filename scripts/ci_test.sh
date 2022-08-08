#!/usr/bin/env bash

### Test Detectors

DIR="$(cd "$(dirname "$0")" && pwd)"

CURRENT_PATH=$(pwd)
TRAVIS_PATH='/home/travis/build/crytic/slither'

# test_slither file.sol detectors
test_slither(){

    expected="$DIR/../tests/expected_json/$(basename "$1" .sol).$2.json"

    # run slither detector on input file and save output as json
    if slither "$1" --solc-disable-warnings --detect "$2" --json "$DIR/tmp-test.json";
    then
        echo "Slither crashed"
        exit 255
    fi

    if [ ! -f "$DIR/tmp-test.json" ]; then
        echo ""
        echo "Missing generated file"
        echo ""
        exit 1
    fi
    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$DIR/tmp-test.json" -i
    result=$(python "$DIR/json_diff.py" "$expected" "$DIR/tmp-test.json")

    rm "$DIR/tmp-test.json"
    if [ "$result" != "{}" ]; then
      echo ""
      echo "failed test of file: $1, detector: $2"
      echo ""
      echo "$result"
      echo ""
      exit 1
    fi

    # run slither detector on input file and save output as json
    if slither "$1" --solc-disable-warnings --detect "$2" --legacy-ast --json "$DIR/tmp-test.json";
    then
        echo "Slither crashed"
        exit 255
    fi

    if [ ! -f "$DIR/tmp-test.json" ]; then
        echo ""
        echo "Missing generated file"
        echo ""
        exit 1
    fi

    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$DIR/tmp-test.json" -i
    result=$(python "$DIR/json_diff.py" "$expected" "$DIR/tmp-test.json")

    rm "$DIR/tmp-test.json"
    if [ "$result" != "{}" ]; then
      echo ""
      echo "failed test of file: $1, detector: $2"
      echo ""
      echo "$result"
      echo ""
      exit 1
    fi
}

# generate_expected_json file.sol detectors
generate_expected_json(){
    # generate output filename
    # e.g. file: uninitialized.sol detector: uninitialized-state
    # ---> uninitialized.uninitialized-state.json
    output_filename="$DIR/../tests/expected_json/$(basename "$1" .sol).$2.json"
    output_filename_txt="$DIR/../tests/expected_json/$(basename "$1" .sol).$2.txt"

    # run slither detector on input file and save output as json
    slither "$1" --solc-disable-warnings --detect "$2" --json "$output_filename" > "$output_filename_txt" 2>&1


    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$output_filename" -i
    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$output_filename_txt" -i
}

