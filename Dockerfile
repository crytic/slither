# syntax=docker/dockerfile:1.12

# --- Stage 1: Build ---
FROM ubuntu:noble AS builder

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       python3 python3-venv curl \
  && curl -LsSf https://astral.sh/uv/install.sh \
       | UV_INSTALL_DIR=/usr/local/bin sh \
  && rm -rf /var/lib/apt/lists/*

# armv7 lacks prebuilt wheels for C extensions (bitarray, cytoolz, etc.)
RUN if [ "$(dpkg --print-architecture)" = "armhf" ]; then \
      apt-get update \
      && apt-get install -y --no-install-recommends \
           build-essential python3-dev \
      && rm -rf /var/lib/apt/lists/*; \
    fi

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    UV_PROJECT_ENVIRONMENT=/app

WORKDIR /build

# Layer 1: deps only (cached until pyproject.toml or uv.lock change)
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --locked --no-dev --no-install-project

# Layer 2: install project (rebuilds on source changes)
COPY slither/ slither/
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked --no-dev --no-editable


# --- Stage 2: Runtime ---
FROM ubuntu:noble AS final

LABEL org.opencontainers.image.title="slither" \
      org.opencontainers.image.description="Static Analyzer for Solidity" \
      org.opencontainers.image.url="https://github.com/crytic/slither" \
      org.opencontainers.image.source="https://github.com/crytic/slither" \
      org.opencontainers.image.vendor="Trail of Bits" \
      org.opencontainers.image.licenses="AGPL-3.0"

RUN export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends python3 ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Cross-arch solc compat (e.g. Docker Desktop on Apple Silicon)
ENV QEMU_LD_PREFIX=/usr/x86_64-linux-gnu
RUN if [ "$(dpkg --print-architecture)" != "amd64" ]; then \
      export DEBIAN_FRONTEND=noninteractive \
      && apt-get update \
      && apt-get install -y --no-install-recommends libc6-amd64-cross \
      && rm -rf /var/lib/apt/lists/*; \
    fi

RUN useradd --create-home slither
USER slither
WORKDIR /home/slither

# Copy the pre-built venv from builder
COPY --from=builder --chown=slither:slither /app /app
ENV PATH="/app/bin:${PATH}"

# Pre-download latest solc so the image is ready to use
RUN solc-select use latest --always-install

CMD ["/bin/bash"]
