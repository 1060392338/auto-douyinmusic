"""快速测试DrissionPage连接"""
from DrissionPage import ChromiumPage
import time
P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(2)
for _ in range(5):
    try: P.handle_alert(accept=True); time.sleep(0.3)
    except: break
print("URL:", P.url)
print("Title:", P.title)
print("CONNECT_OK")
