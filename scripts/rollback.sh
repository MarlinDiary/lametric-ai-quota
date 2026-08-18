#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <commit-to-revert>" >&2
  exit 64
fi

git diff --quiet
git diff --cached --quiet
git rev-parse --verify "$1^{commit}" >/dev/null
git revert --no-edit "$1"

cat <<'EOF'
Rollback commit created locally. Review it, run ./scripts/verify.sh, then push it to trigger Railway.
EOF
