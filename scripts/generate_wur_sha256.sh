#!/usr/bin/env bash
set -euo pipefail

# Run from the repository root.
RAW_DIR="data/raw/wur"
MANIFEST="metadata/wur_sha256.txt"

if [[ ! -d "$RAW_DIR" ]]; then
    echo "Error: $RAW_DIR does not exist." >&2
    exit 1
fi

mkdir -p "$(dirname "$MANIFEST")"

# Hash every regular file under the raw dataset directory.
# The manifest is outside RAW_DIR, so it will not hash itself.
find "$RAW_DIR" -type f -print0 \
    | sort -z \
    | xargs -0 -r sha256sum > "$MANIFEST"

echo "Wrote $MANIFEST"
echo "Files hashed: $(wc -l < "$MANIFEST")"

# Verify immediately.
sha256sum --check "$MANIFEST"
