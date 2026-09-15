#!/bin/bash
# High-reliability fetch for Stitch HTML (handles redirects and TLS).
# Usage: ./fetch-stitch.sh "<htmlCode.downloadUrl>" "temp/source.html"
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo "用法: $0 <HTTPS 下载地址> <输出路径>" >&2
  exit 1
fi
STITCH_FETCH_URL=$1
STITCH_FETCH_OUTPUT=$2
case "$STITCH_FETCH_URL" in
  https://*) ;;
  *) echo "缺少 HTTPS 下载地址，请重新获取屏幕资产元数据。" >&2; exit 1 ;;
esac
mkdir -p "$(dirname "$STITCH_FETCH_OUTPUT")"
STITCH_FETCH_STAGE=$(mktemp "${STITCH_FETCH_OUTPUT}.download.XXXXXX")
trap 'rm -f "$STITCH_FETCH_STAGE"' EXIT
if curl --proto '=https' --proto-redir '=https' -L -f -sS --connect-timeout 10 --max-time 120 --compressed "$STITCH_FETCH_URL" -o "$STITCH_FETCH_STAGE" 2>/dev/null; then
  mv "$STITCH_FETCH_STAGE" "$STITCH_FETCH_OUTPUT"
  echo "资产已保存: $STITCH_FETCH_OUTPUT"
else
  echo "下载未完成，旧资产已保留；请检查网络或刷新过期链接。" >&2
  exit 1
fi
