#!/usr/bin/env bash
# Package the hunt for AgentCore Runtime's direct code deploy: the skynet package, its data and config, and
# aarch64 / CPython 3.13 wheels for its dependencies (the runtime is ARM64). Output: dist/runtime.zip.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; root="$here/../.."
stage="$(mktemp -d)"; trap 'rm -rf "$stage"' EXIT
mkdir -p "$here/dist"
# Pinned to the versions the tests and the local Bedrock hunt ran on. Unpinned, the build took anthropic 1.13,
# which replaced httpx with httpx2 and broke the client's response tap at import (10. Oct 2026).
uv pip install --quiet --target "$stage" --python-version 3.13 --python-platform aarch64-manylinux2014 \
  --only-binary :all: anthropic==0.109.2 httpx==0.28.1 pydantic==2.13.4 bedrock-agentcore==1.24.1 \
  boto3==1.43.111 botocore==1.43.111
# fail the build, not the first invocation, if a pinned import is missing
for m in anthropic httpx pydantic bedrock_agentcore boto3; do [ -d "$stage/$m" ] || { echo "missing $m" >&2; exit 1; }; done
cp -r "$root/skynet" "$stage/skynet"; find "$stage/skynet" -name __pycache__ -prune -exec rm -rf {} +
# the terminal UI and the arena are not used in the runtime; their deps (textual, rich) are not packaged
cp -r "$root/data" "$stage/data"; cp "$root/config.bedrock.toml" "$stage/"
cat > "$stage/main.py" <<'PY'
from skynet.agentcore_app import build_app

app = build_app()

if __name__ == "__main__":
    app.run()
PY
(cd "$stage" && rm -f "$here/dist/runtime.zip" && zip -qr "$here/dist/runtime.zip" . -x '*.pyc')
ls -la "$here/dist/runtime.zip"
