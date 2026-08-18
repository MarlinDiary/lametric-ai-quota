FROM node:22-bookworm-slim

ARG TARGETARCH
ARG CODEXBAR_VERSION=0.52.0
ARG CODEX_VERSION=0.147.0
ARG CLAUDE_CODE_VERSION=2.1.234

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libcurl4 \
        libsqlite3-0 \
        libxml2 \
        libz3-4 \
        python3 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "$TARGETARCH" in \
      amd64) CB_ARCH=x86_64; CB_SHA=cae0cac1f178e57ddd2f7deeba0cba0605f084205f2d8b421fcdbe4aa7144376 ;; \
      arm64) CB_ARCH=aarch64; CB_SHA=302c3b5b7286c040c4f11f9a011a9f36e3172f12aa83f2c86a3caf40c6a3625a ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 64 ;; \
    esac; \
    archive="CodexBarCLI-v${CODEXBAR_VERSION}-linux-musl-${CB_ARCH}.tar.gz"; \
    curl -fL --retry 3 -o "/tmp/${archive}" \
      "https://github.com/steipete/CodexBar/releases/download/v${CODEXBAR_VERSION}/${archive}"; \
    echo "${CB_SHA}  /tmp/${archive}" | sha256sum -c -; \
    mkdir -p /opt/codexbar; \
    tar -xzf "/tmp/${archive}" -C /opt/codexbar; \
    ln -s /opt/codexbar/codexbar /usr/local/bin/codexbar; \
    rm "/tmp/${archive}"

RUN npm install -g --include=optional \
      "@openai/codex@${CODEX_VERSION}" \
      "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
    && npm cache clean --force

WORKDIR /app
COPY src /app/src
COPY assets /app/assets
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENV PYTHONPATH=/app/src \
    HOME=/data/home \
    CODEX_HOME=/data/home/.codex \
    CLAUDE_CONFIG_DIR=/data/home/.claude \
    CODEXBAR_CONFIG=/data/home/.config/codexbar/config.json \
    PORT=8080 \
    REFRESH_INTERVAL=300 \
    CODEXBAR_CODEX_SOURCE=oauth \
    CODEXBAR_CLAUDE_SOURCE=oauth

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && python3 -m compileall -q /app/src \
    && codexbar --version \
    && codex --version \
    && claude --version

EXPOSE 8080
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python3", "-m", "lametric_quota"]
