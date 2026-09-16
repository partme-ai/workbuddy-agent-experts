#!/bin/bash
# 卸载 WorkBuddy 专家团（双击运行）
# 只移除本包安装的 55 个插件与注册条目，不触碰其他数据。
exec /usr/bin/osascript -l JavaScript \
  "/Library/Application Support/WorkBuddyExperts/tools/uninstall.js" \
  "/Library/Application Support/WorkBuddyExperts/experts" \
  "$HOME/.workbuddy"
