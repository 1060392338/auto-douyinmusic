"""在资产页导航到发布页"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 切换到资产页
pages = requests.get('http://localhost:9223/json').json()
for p in pages:
    if '/studio/assets' in p.get('url', ''):
        print(f"激活资产页: {p['id']}", flush=True)
        P.run_cdp('Target.activateTarget', targetId=p['id'])
        time.sleep(2)
        break

# 关闭可能存在的弹窗
P.run_js("window.onbeforeunload=null;")

# 导航到发布页（用页面内 SPA 导航）
print("导航到发布页...", flush=True)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(8)

# 处理可能出现的弹窗
try:
    P.run_cdp('Page.handleJavaScriptDialog', accept=True)
    print("处理了弹窗", flush=True)
except:
    pass

body = P.ele('tag:body').text
print(f"发布页文本 (len={len(body)}):", flush=True)
print(body[:3000], flush=True)

for kw in ['下一步', '歌曲信息', '授权', '上传', '封面', '艺人', '蝉声漫旧夏']:
    print(f"  {kw}: {'✅' if kw in body else '❌'}", flush=True)
