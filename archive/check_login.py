"""快速检查登录态"""
from DrissionPage import ChromiumPage
import time
P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(2)
for _ in range(5):
    try: P.handle_alert(accept=True); time.sleep(0.3)
    except: break
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(6)
body = P.ele("tag:body").text
print(f"登录状态: {'✅' if 'AI 作词' in body else '❌'}")
print(f"页面文本长度: {len(body)}")
