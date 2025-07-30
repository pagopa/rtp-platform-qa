#!/bin/bash

OWNER=$(git config --get remote.origin.url | sed -E 's|.*github.com[:/](.*)/.*|\1|' | cut -d/ -f1)

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <deployment-file.yaml>"
  exit 1
fi

FILE="$1"

echo "Deploying $FILE with GHCR owner: $OWNER"
sed "s|__OWNER__|$OWNER|g" "$FILE" | kubectl apply -n srtp -f -
