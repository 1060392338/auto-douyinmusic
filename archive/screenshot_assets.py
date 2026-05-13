"""截图确认资产页状态"""
import time, shutil
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/asset/music';")
time.sleep(8)

# 截图
P.get_screenshot('/tmp/douyin_assets.png')
shutil.copy('/tmp/douyin_assets.png', '/Users/mac/.hermes/cache/screenshots/douyin_assets.png')
print(f"Screenshot saved", flush=True)
print(f"URL: {P.url}", flush=True)
print(f"Text length: {len(P.ele('tag:body').text)}", flush=True)
