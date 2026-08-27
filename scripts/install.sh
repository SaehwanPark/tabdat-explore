#!/bin/sh
# TabDat-Explore Frictionless Installer
# Usage: curl -LsSf https://raw.githubusercontent.com/SaehwanPark/tabdat-explore/main/scripts/install.sh | sh

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

printf "${BOLD}${BLUE}=== Installing TabDat-Explore ===${NC}\n\n"

# 1. Check Operating System
OS="$(uname -s)"
case "$OS" in
  Linux|Darwin)
    printf "Detected operating system: ${GREEN}%s${NC}\n" "$OS"
    ;;
  *)
    printf "${RED}Error: TabDat installer supports Linux and macOS. Detected: %s${NC}\n" "$OS" >&2
    exit 1
    ;;
esac

# 2. Check for uv package manager
if ! command -v uv >/dev/null 2>&1; then
  printf "uv package manager not found on PATH. Installing uv...\n"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # Source uv env if available
  if [ -f "$HOME/.cargo/env" ]; then
    . "$HOME/.cargo/env"
  elif [ -f "$HOME/.local/bin/env" ]; then
    . "$HOME/.local/bin/env"
  fi
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  printf "${RED}Error: uv could not be installed or is not in PATH.${NC}\n" >&2
  printf "Please install uv manually: https://docs.astral.sh/uv/\n" >&2
  exit 1
fi

printf "Using uv: ${GREEN}%s${NC}\n" "$(command -v uv)"

# 3. Install TabDat CLI globally using uv tool
printf "\nInstalling TabDat CLI globally...\n"
if [ -n "$TABDAT_INSTALL_FROM" ]; then
  uv tool install --force "$TABDAT_INSTALL_FROM"
else
  # Install from GitHub repository
  uv tool install --force "git+https://github.com/SaehwanPark/tabdat-explore.git"
fi

# Ensure tool bin directory is on PATH
TOOL_DIR="$HOME/.local/bin"
case ":$PATH:" in
  *":$TOOL_DIR:"*) ;;
  *)
    export PATH="$TOOL_DIR:$PATH"
    ;;
esac

printf "\n${BOLD}${GREEN}✓ TabDat-Explore successfully installed!${NC}\n\n"
printf "Run ${BOLD}tabdat doctor${NC} to check installed backends.\n"
printf "Run ${BOLD}tabdat${NC} to launch the interactive shell.\n"
printf "Run ${BOLD}tabdat -c \"help summarize\"${NC} to view command documentation.\n\n"
