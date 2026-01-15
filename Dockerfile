# syntax=docker/dockerfile:1.12
FROM ubuntu:jammy AS final

LABEL name=slither \
      src="https://github.com/trailofbits/slither" \
      creator=trailofbits \
      dockerfile_maintenance=trailofbits \
      desc="Static Analyzer for Solidity"

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends git python3 python3-venv \
  && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# improve compatibility with amd64 solc in non-amd64 environments (e.g. Docker Desktop on M1 Mac)
ENV QEMU_LD_PREFIX=/usr/x86_64-linux-gnu
RUN if [ ! "$(uname -m)" = "x86_64" ]; then \
  export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends libc6-amd64-cross \
  && rm -rf /var/lib/apt/lists/*; fi

RUN useradd -m slither
USER slither

WORKDIR /home/slither/slither

# Copy dependency files first for layer caching
COPY --chown=slither:slither pyproject.toml uv.lock ./

# Install dependencies (creates venv in .venv)
RUN uv sync --frozen --no-install-project

# Copy source code
COPY --chown=slither:slither . .

# Install the project itself and solc-select
RUN uv sync --frozen && \
    uv tool install solc-select

ENV PATH="/home/slither/slither/.venv/bin:/home/slither/.local/bin:${PATH}"

RUN solc-select use latest --always-install

CMD ["/bin/bash"]
