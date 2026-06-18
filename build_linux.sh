#!/usr/bin/env bash
set -euo pipefail

# Build helper for Linux (runs on a Linux host, not Windows)
# Usage: ./build_linux.sh [mode]
# mode: onefile | onedir | appimage  (default: appimage)

APP_NAME=${APP_NAME:-MediaSalvager}
VENV=${VENV:-.venv}
PYTHON=${PYTHON:-python3}
MODE=${1:-appimage}
ADD_DATA="media_salvager/assets:media_salvager/assets"

echo "Build mode: ${MODE}"

# 1) Setup venv
if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv at $VENV"
  $PYTHON -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
pip install --upgrade pyinstaller

# Helper: run PyInstaller with our common options
run_pyinstaller() {
  local extra="$1"
  echo "Running PyInstaller: $extra"
  python -m PyInstaller --clean $extra --name "$APP_NAME" --add-data "$ADD_DATA" main.py
}

case "$MODE" in
  onefile)
    run_pyinstaller "--onefile --windowed"
    echo "Single-file build complete: dist/${APP_NAME}"
    ;;

  onedir)
    run_pyinstaller "--onedir --windowed"
    echo "One-dir build complete: dist/${APP_NAME}/"
    ;;

  appimage)
    # 1) do an onedir build
    run_pyinstaller "--onedir --windowed"

    APPDIR="dist/${APP_NAME}"
    BINARY_PATH="$APPDIR/${APP_NAME}"

    # Ensure binary exists
    if [ ! -f "$BINARY_PATH" ]; then
      echo "ERROR: Expected binary at $BINARY_PATH not found" >&2
      exit 1
    fi

    # Create a minimal .desktop if none exists
    DESKTOP_FILE="$APPDIR/${APP_NAME}.desktop"
    if [ ! -f "$DESKTOP_FILE" ]; then
      echo "Creating minimal .desktop file"
      cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=${APP_NAME}
Exec=${APP_NAME}
Type=Application
Terminal=false
Categories=Utility;
EOF
    fi

    # Try to find an icon inside assets
    ICON_SRC="media_salvager/assets/icon.png"
    if [ -f "$ICON_SRC" ]; then
      cp "$ICON_SRC" "$APPDIR/${APP_NAME}.png"
    fi

    # Download linuxdeployqt if not present
    LINUXDEPLOYQT=${LINUXDEPLOYQT:-linuxdeployqt-continuous-x86_64.AppImage}
    if [ ! -f "$LINUXDEPLOYQT" ]; then
      echo "Downloading linuxdeployqt AppImage (this may take a while)"
      curl -L -o "$LINUXDEPLOYQT" "https://github.com/probonopd/linuxdeployqt/releases/download/continuous/linuxdeployqt-continuous-x86_64.AppImage"
      chmod +x "$LINUXDEPLOYQT"
    fi

    echo "Running linuxdeployqt to produce AppImage"
    # linuxdeployqt expects to be pointed at the binary inside the AppDir
    ./"$LINUXDEPLOYQT" "$BINARY_PATH" -appimage -qmldir=.

    echo "AppImage build finished (look for a .AppImage file)"
    ;;

  *)
    echo "Unknown mode: $MODE" >&2
    echo "Usage: $0 [onefile|onedir|appimage]"
    exit 2
    ;;

esac

# Post-build note about ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "WARNING: ffmpeg not found on PATH. The app requires ffmpeg/ffprobe at runtime." >&2
  echo "You can either install ffmpeg on the target system or bundle a static ffmpeg binary next to the app." >&2
fi

echo "Done."
