#!/bin/zsh
set -u

cd -- "$(dirname "$0")"

APP_NAME="Multi Platform Media Downloader"
VENV_DIR=".venv"
VENV_PYTHON="$VENV_DIR/bin/python"
REQUIREMENTS_FILE="requirements.txt"
REQUIREMENTS_STAMP="$VENV_DIR/.requirements.sha"

print_step() {
  printf "\n==> %s\n" "$1"
}

pause_on_error() {
  printf "\n%s başlatılamadı. Detayları yukarıda görebilirsin.\n" "$APP_NAME"
  printf "Kapatmak için Enter'a bas..."
  read -r _
}

version_ok() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

find_python() {
  local candidates=(
    "/opt/homebrew/bin/python3.14"
    "/opt/homebrew/bin/python3.13"
    "/opt/homebrew/bin/python3.12"
    "/opt/homebrew/bin/python3.11"
    "/opt/homebrew/bin/python3.10"
    "/opt/homebrew/bin/python3"
    "python3"
  )

  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1 && version_ok "$candidate"; then
      command -v "$candidate"
      return 0
    fi
  done

  return 1
}

ensure_venv() {
  local python_bin="$1"

  if [[ -x "$VENV_PYTHON" ]] && version_ok "$VENV_PYTHON"; then
    return 0
  fi

  if [[ -d "$VENV_DIR" ]]; then
    local backup=".venv-backup-$(date +%Y%m%d-%H%M%S)"
    print_step "Eski venv Python 3.10+ değil; $backup olarak ayrılıyor"
    mv "$VENV_DIR" "$backup" || return 1
  fi

  print_step "Python venv hazırlanıyor"
  "$python_bin" -m venv "$VENV_DIR" || return 1
}

ensure_requirements() {
  local current_sha
  current_sha="$(shasum -a 256 "$REQUIREMENTS_FILE" | awk '{print $1}')"

  if [[ -f "$REQUIREMENTS_STAMP" ]] && [[ "$(cat "$REQUIREMENTS_STAMP")" == "$current_sha" ]]; then
    return 0
  fi

  print_step "Python paketleri yükleniyor"
  "$VENV_PYTHON" -m pip install --upgrade pip || return 1
  "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE" || return 1
  printf "%s" "$current_sha" > "$REQUIREMENTS_STAMP"
}

main() {
  local python_bin
  python_bin="$(find_python)" || {
    printf "Python 3.10+ bulunamadı.\n"
    printf "macOS için önerilen kurulum: brew install python-tk@3.14\n"
    return 1
  }

  ensure_venv "$python_bin" || return 1
  ensure_requirements || return 1

  print_step "$APP_NAME açılıyor"
  "$VENV_PYTHON" main.py
}

main || pause_on_error
