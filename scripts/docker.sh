#!/usr/bin/env bash
# Build or run a service image, or clean up Docker. A service is any
# services/<name>/Dockerfile; the image is named skincare-<name>.
#   scripts/docker.sh mcp-server build
#   scripts/docker.sh mcp-server run
#   scripts/docker.sh clean
set -euo pipefail
cd "$(dirname "$0")/.." # repo root = the build context, so COPY paths are repo-relative

usage() {
  echo "usage: scripts/docker.sh <service> build|run   or   scripts/docker.sh clean" >&2
  exit 1
}

if [ "${1:-}" = clean ]; then
  docker image prune -f                       # untagged leftovers from rebuilds
  docker builder prune -f --filter until=168h # cache older than 7 days; newer cache keeps rebuilds fast
  docker system df
  exit 0
fi

[ $# -eq 2 ] || usage
service=$1
action=$2
[ -f "services/$service/Dockerfile" ] || { echo "no services/$service/Dockerfile" >&2; exit 1; }
image="skincare-$service"

case "$action" in
  build)
    docker build -f "services/$service/Dockerfile" -t "$image" .
    docker image prune -f # the previous build of this tag is now untagged: drop it
    docker images "$image"
    ;;
  # ponytail: port fixed at 7860; add a PORT argument when two services must run side by side.
  run) docker run --rm -p 7860:7860 "$image" ;;
  *) usage ;;
esac
