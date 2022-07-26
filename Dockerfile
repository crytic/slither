FROM ubuntu:focal

LABEL name=slither
LABEL src="https://github.com/trailofbits/slither"
LABEL creator=trailofbits
LABEL dockerfile_maintenance=trailofbits
LABEL desc="Static Analyzer for Solidity"

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get upgrade -yq \
  && apt-get install -yq gcc git python3 python3-dev python3-setuptools wget software-properties-common

RUN wget -q https://github.com/ethereum/solidity/releases/download/v0.4.25/solc-static-linux \
 && chmod +x solc-static-linux \
 && mv solc-static-linux /usr/bin/solc

RUN useradd -m slither
USER slither

# If this fails, the solc-static-linux binary has changed while it should not.
RUN [ "c9b268750506b88fe71371100050e9dd1e7edcf8f69da34d1cd09557ecb24580  /usr/bin/solc" = "$(sha256sum /usr/bin/solc)" ]

COPY --chown=slither:slither . /home/slither/slither
WORKDIR /home/slither/slither

RUN python3 setup.py install --user
ENV PATH="/home/slither/.local/bin:${PATH}"
CMD /bin/bash
