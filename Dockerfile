# syntax=docker/dockerfile:1.3
FROM ubuntu:jammy AS python-wheels
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    python3-pip \
  && rm -rf /var/lib/apt/lists/*

COPY . /slither

RUN cd /slither && \
    echo pip3 install --no-cache-dir --upgrade pip && \
    pip3 wheel -w /wheels . solc-select pip setuptools wheel


FROM ubuntu:jammy AS final

LABEL name=slither
LABEL src="https://github.com/trailofbits/slither"
LABEL creator=trailofbits
LABEL dockerfile_maintenance=trailofbits
LABEL desc="Static Analyzer for Solidity"

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends python3-pip \
  && rm -rf /var/lib/apt/lists/*

# improve compatibility with amd64 solc in non-amd64 environments (e.g. Docker Desktop on M1 Mac)
ENV QEMU_LD_PREFIX=/usr/x86_64-linux-gnu
RUN if [ ! "$(uname -m)" = "x86_64" ]; then \
  export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends libc6-amd64-cross \
  && rm -rf /var/lib/apt/lists/*; fi

RUN useradd -m slither
USER slither

COPY --chown=slither:slither . /home/slither/slither
WORKDIR /home/slither/slither

ENV PATH="/home/slither/.local/bin:${PATH}"

# no-index ensures we install the freshly-built wheels
RUN --mount=type=bind,target=/mnt,source=/wheels,from=python-wheels \
    pip3 install --user --no-cache-dir --upgrade --no-index --find-links /mnt pip slither-analyzer solc-select

RUN solc-select install 0.4.25 && solc-select use 0.4.25

CMD /bin/bash
