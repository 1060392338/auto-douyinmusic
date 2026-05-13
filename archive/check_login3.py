"""检查登录态 - 用 P.get 代替 P.run_js"""
from DrissionPage import ChromiumPage
import time
P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(2)
# 清除弹窗
for _ in range(5):
    try: P.handle_alert(accept=True); time.sleep(0.3)
    except: break
# 直接导航
P.get("https://music.douyin.com/studio", timeout=10)
time.sleep(6)
body = P.ele("tag:body").text
if "AI 作词" in body:
    print("LOGIN_OK")
else:
    print("LOGIN_FAIL")
    print(body[:200])
