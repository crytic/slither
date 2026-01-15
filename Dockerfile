# syntax=docker/dockerfile:1.12
FROM ubuntu:jammy AS final

LABEL name=slither \
      src="https://github.com/trailofbits/slither" \
      creator=trailofbits \
      dockerfile_maintenance=trailofbits \
      desc="Static Analyzer for Solidity"

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl git python3 python3-pip python3-venv \
  && rm -rf /var/lib/apt/lists/*

# Install uv if available for this architecture (amd64/arm64)
# uv doesn't support armv7, so those builds will use pip instead
RUN arch=$(uname -m) && \
    if [ "$arch" = "x86_64" ] || [ "$arch" = "aarch64" ]; then \
      curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh; \
    fi

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

# Install dependencies - use uv if available (with lockfile), pip otherwise
RUN if command -v uv >/dev/null 2>&1; then \
      uv sync --frozen --no-install-project; \
    else \
      python3 -m venv .venv; \
    fi

# Copy source code
COPY --chown=slither:slither . .

# Install the project itself and solc-select
RUN if command -v uv >/dev/null 2>&1; then \
      uv sync --frozen && \
      uv tool install solc-select; \
    else \
      . .venv/bin/activate && \
      pip install --no-cache-dir -e . solc-select; \
    fi

ENV PATH="/home/slither/slither/.venv/bin:/home/slither/.local/bin:${PATH}"

RUN solc-select use latest --always-install

CMD ["/bin/bash"]
