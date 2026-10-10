#!/usr/bin/env bash
# Package only what the archive Lambda imports: the stdlib-only archive path. boto3 is in the runtime.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; root="$here/../.."
stage="$(mktemp -d)"; trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/skynet" "$here/dist"
for f in __init__ archive archive_aws evidence gateway_lambda grid scenario; do cp "$root/skynet/$f.py" "$stage/skynet/"; done
mkdir -p "$stage/data" && cp "$root/data/cyberdyne_1984.json" "$stage/data/"
(cd "$stage" && rm -f "$here/dist/archive_lambda.zip" && zip -qr "$here/dist/archive_lambda.zip" .)
echo "built $here/dist/archive_lambda.zip"
