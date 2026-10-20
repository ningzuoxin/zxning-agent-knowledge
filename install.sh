#!/bin/bash
# install.sh: one-command installer for the knowledge skills into an AI agent's skills directory
# Usage:
#   bash install.sh                     # default: codebuddy + trae (global)
#   bash install.sh codebuddy trae      # pick targets by name
#   bash install.sh copilot             # current project's .agents/skills/ (run at the business repo root)
#   bash install.sh <any-directory>     # custom directory
#   bash install.sh snippet [product]   # append the knowledge-base onboarding section to ./AGENTS.md
#                                       # (run at the business repo root; product defaults to the directory name)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KB_PATH="$SCRIPT_DIR"
VAULT_VAR="ZXNING_AGENT_KNOWLEDGE_VAULT"

target_dir() {
  case "$1" in
    codebuddy) echo "$HOME/.codebuddy/skills" ;;
    trae)      echo "$HOME/.trae-cn/skills" ;;
    copilot)   echo "$PWD/.agents/skills" ;;
    *)         echo "$1" ;;
  esac
}

usage() {
  cat <<'EOF'
Usage: bash install.sh [target...]

Targets:
  codebuddy    ~/.codebuddy/skills               (CodeBuddy IDE, global)
  trae         ~/.trae-cn/skills                 (Trae-CN, global)
  copilot      <current project>/.agents/skills  (GitHub Copilot, project-level; run at the business repo root)
  <directory>  any custom skills directory
  snippet [product]
               append the knowledge-base onboarding section to ./AGENTS.md
               (standalone mode; run at the business repo root; product defaults to the directory name)

With no arguments, installs to codebuddy + trae by default.
EOF
  exit 1
}

[ -f "$SCRIPT_DIR/skills/zxning-mem-recall/SKILL.md" ] || {
  echo "Error: skills/ not found (install.sh must sit at the tool repo root)"
  exit 1
}

if [ $# -eq 0 ]; then
  TARGETS=(codebuddy trae)
  MODE=install
elif [ "$1" = "snippet" ]; then
  [ $# -le 2 ] || usage
  MODE=snippet
  SNIPPET_PRODUCT="${2:-}"
else
  TARGETS=("$@")
  MODE=install
fi

if [ "$MODE" = "snippet" ]; then
  echo "=== Knowledge-base onboarding snippet ==="
  echo "Project: $PWD"
  echo ""
  SNIPPET_SRC="$SCRIPT_DIR/AGENTS_SNIPPET.md"
  [ -f "$SNIPPET_SRC" ] || {
    echo "Error: AGENTS_SNIPPET.md not found at the tool repo root"
    exit 1
  }
  TARGET_MD="$PWD/AGENTS.md"
  if [ -f "$TARGET_MD" ] && grep -q "zxning-mem:begin" "$TARGET_MD"; then
    echo "  = snippet already present in AGENTS.md (skipped)"
  else
    [ -f "$TARGET_MD" ] || printf "# AGENTS.md\n" > "$TARGET_MD"
    {
      echo ""
      sed "s/{{PRODUCT}}/${SNIPPET_PRODUCT:-$(basename "$PWD")}/g" "$SNIPPET_SRC"
    } >> "$TARGET_MD"
    echo "  ✓ snippet appended to AGENTS.md (product: ${SNIPPET_PRODUCT:-$(basename "$PWD")})"
  fi
  echo ""
else
  echo "=== Installing knowledge skills ==="
  echo "Tool repo: $KB_PATH"
  echo ""

  for t in "${TARGETS[@]}"; do
    DST="$(target_dir "$t")"
    DST="${DST/#\~/$HOME}"
    mkdir -p "$DST"
    echo "[$t] → $DST"
    for skill in zxning-mem-recall zxning-mem-remember zxning-mem-doctor zxning-mem-init; do
      SRC="$KB_PATH/skills/$skill"
      if [ -d "$SRC" ]; then
        rm -rf "$DST/$skill"
        cp -r "$SRC" "$DST/$skill"
        find "$DST/$skill" -type d -name "__pycache__" -prune -exec rm -rf {} +
        echo "  ✓ installed: $skill"
      else
        echo "  ⚠ skipped: $skill (source directory not found)"
      fi
    done
    echo ""
  done

  echo "=== Installation complete ==="
fi

if [ -z "${!VAULT_VAR:-}" ]; then
  echo ""
  echo "⚠ Environment variable $VAULT_VAR (knowledge data root) not detected"
  echo "  The agent relies on it to locate knowledge data at runtime. Set it (persistent; restart terminals/IDEs):"
  echo "    PowerShell: setx $VAULT_VAR \"D:\\workspaces\\zxning\\zxning-agent-knowledge-vault\""
  echo "    or via GUI: Environment Variables → User Variables → New"
else
  echo "Knowledge data root: ${!VAULT_VAR}"
fi

if [ "$MODE" = "snippet" ]; then
  echo "Next step: restart your IDE/agent, then start a session and check that it recalls knowledge from $VAULT_VAR"
else
  echo ""
  echo "Next step: onboard a business project with:  bash install.sh snippet [product]  (run at that project's root)"
fi
