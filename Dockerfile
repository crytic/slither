FROM alpine:3.6

LABEL name slither
LABEL src "https://github.com/trailofbits/slither"
LABEL creator trailofbits
LABEL dockerfile_maintenance trailofbits
LABEL desc "Static Analyzer for Solidity"

# Mostly stolen from ethereum/solc.
RUN apk add --no-cache git python3 build-base cmake boost-dev \
&& sed -i -E -e 's/include <sys\/poll.h>/include <poll.h>/' /usr/include/boost/asio/detail/socket_types.hpp \
&& git clone --depth 1 --recursive -b release https://github.com/ethereum/solidity \
&& cd /solidity && cmake -DCMAKE_BUILD_TYPE=Release -DTESTS=0 -DSTATIC_LINKING=1 \
&& cd /solidity && make solc && install -s  solc/solc /usr/bin \
&& cd / && rm -rf solidity \
&& rm -rf /var/cache/apk/* \
&& git clone https://github.com/trailofbits/slither.git
WORKDIR slither
RUN python3 setup.py install
ENTRYPOINT ["slither"]
CMD ["tests/uninitialized.sol"]
