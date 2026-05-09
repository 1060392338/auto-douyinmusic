#!/bin/bash
# 启动 Chrome 9223（无头模式兼容 DrissionPage 的变通方案）
# 使用 --window-position 将窗口移出屏幕，等效后台运行
exec "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9223 \
  --user-data-dir="/Users/mac/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data" \
  --remote-allow-origins="*" \
  --window-position=-32000,-32000 \
  --window-size=1,1 \
  --disable-features=PrivacySandboxSettings4 \
  --no-first-run \
  --disable-popup-blocking \
  --hide-crash-restore-bubble \
  --disable-infobars \
  --no-default-browser-check \
  --disable-gpu
