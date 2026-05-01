#!/usr/bin/env bash
set -euo pipefail

show_release() {
  local repo="$1"
  local tag="$2"
  printf '\n%s %s\n' "$repo" "$tag"
  gh release view "$tag" --repo "$repo" --json assets \
    | jq -r '.assets[] | select(.name | test("\\.(exe|msi|deb|AppImage|rpm)$")) | [.name, (.downloadCount // 0)] | @tsv'
}

show_release CaptTymur/skipi.app "${1:-v0.4.78}"
show_release CaptTymur/skipi-landing "${2:-crewing-v0.4.77}"
