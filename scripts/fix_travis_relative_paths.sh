CURRENT_PATH=$(pwd)
TRAVIS_PATH='/home/travis/build/crytic/slither'
for f in tests/expected_json/*json; do
    sed "s|$CURRENT_PATH|$TRAVIS_PATH|g" "$f" -i
done
