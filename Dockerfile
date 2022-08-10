# syntax=docker/dockerfile:1.3
FROM ubuntu:jammy AS python-wheels
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    python3-pip

COPY . /slither

RUN cd /slither && \
    echo pip3 install --no-cache-dir --upgrade pip && \
    pip3 wheel -w /wheels . pip setuptools wheel


FROM ubuntu:jammy AS final

LABEL name=slither
LABEL src="https://github.com/trailofbits/slither"
LABEL creator=trailofbits
LABEL dockerfile_maintenance=trailofbits
LABEL desc="Static Analyzer for Solidity"

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y python3-pip wget

RUN wget -q https://github.com/ethereum/solidity/releases/download/v0.4.25/solc-static-linux \
 && chmod +x solc-static-linux \
 && mv solc-static-linux /usr/bin/solc

RUN useradd -m slither
USER slither

# If this fails, the solc-static-linux binary has changed while it should not.
RUN [ "c9b268750506b88fe71371100050e9dd1e7edcf8f69da34d1cd09557ecb24580  /usr/bin/solc" = "$(sha256sum /usr/bin/solc)" ]

COPY --chown=slither:slither . /home/slither/slither
WORKDIR /home/slither/slither

ENV PATH="/home/slither/.local/bin:${PATH}"

# no-index ensures we install the freshly-built wheels
RUN --mount=type=bind,target=/mnt,source=/wheels,from=python-wheels \
    pip3 install --user --no-cache-dir --upgrade --no-index --find-links /mnt pip slither-analyzer

CMD /bin/bash
