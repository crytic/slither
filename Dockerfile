FROM alpine:3.6

LABEL name slither
LABEL src "https://github.com/trailofbits/slither"
LABEL creator trailofbits
LABEL dockerfile_maintenance trailofbits
LABEL desc "Static Analyzer for Solidity"

# Mostly stolen from ethereum/solc.
RUN apk add --no-cache git python3 build-base cmake boost-dev \
&& sed -i -E -e 's/include <sys\/poll.h>/include <poll.h>/' /usr/include/boost/asio/detail/socket_types.hpp \
&& git clone https://github.com/ethereum/solidity \
&& cd /solidity && git checkout 59dbf8f1085b8b92e8b7eb0ce380cbeb642e97eb \ 
&& cd /solidity && make solc && install -s  solc/solc /usr/bin \
&& cd / && rm -rf solidity \
&& rm -rf /var/cache/apk/* \
&& git clone https://github.com/trailofbits/slither.git
WORKDIR slither
RUN python3 setup.py install
ENTRYPOINT ["slither"]
CMD ["tests/uninitialized.sol"]
