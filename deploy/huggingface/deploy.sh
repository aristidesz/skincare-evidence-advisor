#!/bin/sh
# Deploy the MCP server to a public Hugging Face Docker Space, in one commit.
# Once: uvx --from huggingface_hub hf auth login   (a token with write access)
# Usage: deploy/huggingface/deploy.sh <hf-username>/<space-name>
set -eu

SPACE="$1"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/src/tools"
cp deploy/huggingface/Dockerfile deploy/huggingface/README.md "$STAGE/"
cp src/tools/*.py "$STAGE/src/tools/"
cp src/mcp_server.py "$STAGE/src/"

HF="uvx --from huggingface_hub hf"
$HF repos create "$SPACE" --type space --sdk docker --public --exist-ok
$HF upload "$SPACE" "$STAGE" . --type space --commit-message "Deploy MCP server"
