FROM ubuntu:xenial

LABEL name=slither
LABEL src="https://github.com/trailofbits/slither"
LABEL creator=trailofbits
LABEL dockerfile_maintenance=trailofbits
LABEL desc="Static Analyzer for Solidity"

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev

RUN wget https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz \
  && tar -xf Python-3.8.12.tgz \
  && cd Python-3.8.12 \
  && ./configure --enable-optimizations \
  && make -j 8 \
  && make altinstall

RUN wget https://github.com/ethereum/solidity/releases/download/v0.4.25/solc-static-linux \
 && chmod +x solc-static-linux \
 && mv solc-static-linux /usr/bin/solc

RUN useradd -m slither
USER slither

# If this fails, the solc-static-linux binary has changed while it should not.
RUN [ "c9b268750506b88fe71371100050e9dd1e7edcf8f69da34d1cd09557ecb24580  /usr/bin/solc" = "$(sha256sum /usr/bin/solc)" ]

COPY --chown=slither:slither . /home/slither/slither
WORKDIR /home/slither/slither

RUN python3.8 setup.py install --user
ENV PATH="/home/slither/.local/bin:${PATH}"
CMD /bin/bash
