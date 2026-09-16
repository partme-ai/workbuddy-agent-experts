#!/bin/bash
# Build the macOS .pkg installer for WorkBuddy Experts (reproducible).
# Prereqs: experts/ prebuilt tree present (python3 scripts/build.py).
set -euo pipefail
cd "$(dirname "$0")/../.."

VERSION="${1:-1.0.0}"
STAGE="$(mktemp -d)/pkg"
PAYLOAD="$STAGE/payload"
INSTALL_LOC="/Library/Application Support/WorkBuddyExperts"

mkdir -p "$PAYLOAD/$INSTALL_LOC"
cp -R experts "$PAYLOAD/$INSTALL_LOC/experts"
mkdir -p "$PAYLOAD/$INSTALL_LOC/tools"
cp release/macos/tools/install.js release/macos/tools/uninstall.js "$PAYLOAD/$INSTALL_LOC/tools/"
cp "release/macos/payload/卸载专家团.command" "$PAYLOAD/$INSTALL_LOC/"
mkdir -p "$STAGE/scripts"
cp release/macos/scripts/postinstall "$STAGE/scripts/postinstall"

pkgbuild --quiet \
  --root "$PAYLOAD" \
  --scripts "$STAGE/scripts" \
  --identifier "ai.partme.workbuddy-experts" \
  --version "$VERSION" \
  --install-location "/" \
  "$STAGE/WorkBuddy-Experts.pkg"

productbuild --package "$STAGE/WorkBuddy-Experts.pkg" \
  --identifier "ai.partme.workbuddy-experts" \
  "dist/WorkBuddy-Experts-v$VERSION.pkg"

echo "built: dist/WorkBuddy-Experts-v$VERSION.pkg ($(du -h "dist/WorkBuddy-Experts-v$VERSION.pkg" | cut -f1))"
echo "注意：未签名 pkg 首次打开需在『系统设置 → 隐私与安全性』确认。"
