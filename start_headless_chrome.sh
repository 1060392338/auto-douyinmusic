#!/bin/bash
exec "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --remote-debugging-port=9223 \
  --user-data-dir="/Users/mac/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data" \
  --remote-allow-origins="*" \
  --disable-features=PrivacySandboxSettings4 \
  --no-first-run \
  --disable-popup-blocking \
  --hide-crash-restore-bubble \
  --disable-infobars \
  --no-default-browser-check
