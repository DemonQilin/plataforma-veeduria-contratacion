#!/usr/bin/env bash
# Verifica que cada AGENTS.md sea idéntico a su CLAUDE.md, comparando lo que está en el
# índice de git (lo que se va a confirmar), no el árbol de trabajo.
set -euo pipefail

status=0
while IFS= read -r claude; do
  agents="${claude%CLAUDE.md}AGENTS.md"
  if ! git ls-files --error-unmatch --cached -- "$agents" >/dev/null 2>&1; then
    echo "Falta $agents: debe existir y ser igual a $claude." >&2
    status=1
  elif ! diff -q <(git show ":$claude") <(git show ":$agents") >/dev/null; then
    echo "$agents difiere de $claude. Cópialo: cp $claude $agents && git add $agents" >&2
    status=1
  fi
done < <(git ls-files --cached -- 'CLAUDE.md' '*/CLAUDE.md')

exit "$status"
