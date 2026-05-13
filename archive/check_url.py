"""检查当前页面状态"""
from DrissionPage import ChromiumPage
import time
P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(2)
for _ in range(5):
    try: P.handle_alert(accept=True); time.sleep(0.3)
    except: break
try:
    print("URL:", P.url)
except:
    print("URL: ERROR")
try:
    print("Title:", P.title)
except:
    print("Title: ERROR")
