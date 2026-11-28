# The one layer of the Claude Code adapter: the claude command line, pinned.
ARG BASE
FROM ${BASE}
ARG CLI_VERSION
ARG CLI_SHA256
RUN export HOME=/tmp/install \
 && mkdir -p "$HOME" \
 && curl -fsSL https://claude.ai/install.sh | bash -s -- "${CLI_VERSION}" \
 && install -m 0755 "$(readlink -f "$HOME/.local/bin/claude")" /usr/local/bin/claude \
 && rm -rf /tmp/install /root/.claude /root/.claude.json /root/.local /root/.cache \
 && echo "${CLI_SHA256}  /usr/local/bin/claude" | sha256sum -c -
