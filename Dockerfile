FROM ghcr.io/pulp/pulp-ci-centos9:latest

ENV UV_CACHE_DIR=/pulp-docs/.cache/uv/

WORKDIR /pulp-docs

COPY . .

RUN uv pip install --system .
