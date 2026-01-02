#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="python3"
WITH_INKSCAPE=0

usage() {
  cat <<'USAGE'
Usage: ./setup.sh [--with-inkscape] [--python PATH]

Options:
  --with-inkscape   Install Homebrew (if missing) + Inkscape (macOS only)
  --python PATH     Python executable to use (default: python3)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-inkscape)
      WITH_INKSCAPE=1
      shift
      ;;
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python not found: $PYTHON_BIN"
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/requirements.txt"

deactivate

if [[ $WITH_INKSCAPE -eq 1 ]]; then
  if ! command -v brew >/dev/null 2>&1; then
    if [[ "$(uname -s)" != "Darwin" ]]; then
      echo "Homebrew install is only supported on macOS."
      exit 1
    fi
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [[ -x /opt/homebrew/bin/brew ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x /usr/local/bin/brew ]]; then
      eval "$(/usr/local/bin/brew shellenv)"
    fi
  fi
  if brew list --cask inkscape >/dev/null 2>&1; then
    echo "Inkscape is already installed."
  else
    echo "Installing Inkscape via Homebrew..."
    brew install --cask inkscape
  fi
fi

echo "Setup complete. Activate with: source $VENV_DIR/bin/activate"
