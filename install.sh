#!/bin/bash
# install.sh: one-command installer for the knowledge skills into an AI agent's skills directory
# Usage:
#   bash install.sh                     # default: codebuddy + trae (global)
#   bash install.sh codebuddy trae      # pick targets by name
#   bash install.sh copilot             # current project's .agents/skills/ (run at the business repo root)
#   bash install.sh <any-directory>     # custom directory
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
else
  TARGETS=("$@")
fi

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

if [ -z "${!VAULT_VAR:-}" ]; then
  echo ""
  echo "⚠ Environment variable $VAULT_VAR (knowledge data root) not detected"
  echo "  The agent relies on it to locate knowledge data at runtime. Set it (persistent; restart terminals/IDEs):"
  echo "    PowerShell: setx $VAULT_VAR \"D:\\workspaces\\zxning\\zxning-agent-knowledge-vault\""
  echo "    or via GUI: Environment Variables → User Variables → New"
else
  echo "Knowledge data root: ${!VAULT_VAR}"
fi

echo ""
echo "Next step: add the knowledge-base onboarding section to the AGENTS.md at your business project root"
echo "  (for product / repo / knowledge_base_path priority, see the tool repo README.md Quick Start - Step 2)"
