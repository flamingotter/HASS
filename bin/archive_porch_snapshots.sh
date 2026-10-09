#!/bin/bash
set -e

ARCHIVE_DIR="/media/snapshots/porch/archive"
mkdir -p "$ARCHIVE_DIR"

RAW_TAG="${1:-EVENT}"
# Sanitize tag: strip brackets, convert non-alphanumeric chars to underscores
TAG=$(echo "$RAW_TAG" | tr -d '[]' | tr -cs '[:alnum:]_' '_' | sed 's/^_//;s/_$//')
[ -z "$TAG" ] && TAG="EVENT"

TS=$(date +%Y-%m-%d_%H%M%S)

# Archive doorbell snapshots (t0, t1, t3) if they exist
for slot in t0 t1 t3; do
  src="/media/snapshots/porch/doorbell_${slot}.jpg"
  if [ -f "$src" ]; then
    cp "$src" "${ARCHIVE_DIR}/${TS}_${TAG}_${slot}.jpg"
  fi
done

# Archive approach video sample
if [ -f "/media/snapshots/porch/approach_sample.mp4" ]; then
  cp "/media/snapshots/porch/approach_sample.mp4" "${ARCHIVE_DIR}/${TS}_${TAG}_approach.mp4"
elif [ -f "/media/snapshots/porch/approach.mp4" ]; then
  cp "/media/snapshots/porch/approach.mp4" "${ARCHIVE_DIR}/${TS}_${TAG}_approach.mp4"
fi

# Auto-prune files older than 3 days (72 hours = 4320 minutes)
find "$ARCHIVE_DIR" -type f \( -name "*.jpg" -o -name "*.mp4" \) -mmin +4320 -delete

