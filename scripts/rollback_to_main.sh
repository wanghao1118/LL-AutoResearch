#!/usr/bin/env bash
set -euo pipefail

repo="${1:-$(git rev-parse --show-toplevel)}"
cd "$repo"
git show-ref --verify --quiet refs/heads/main
git restore --source=main --staged --worktree -- .
printf 'restored tracked files from main\n'
