"""带重试的页面检查"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")

# 等待 body 可用
body = None
for _ in range(10):
    time.sleep(2)
    try:
        body = P.ele('tag:body', timeout=3)
        if body and len(body.text) > 100:
            break
    except:
        continue

if not body or len(body.text) < 100:
    print("❌ 页面加载失败", flush=True)
else:
    text = body.text
    print(f"文本长度: {len(text)}", flush=True)
    print(f"底部800字:", flush=True)
    print(text[-800:], flush=True)
    
    # 搜索关键文本
    print("\n搜索:", flush=True)
    for kw in ['批量签署', '意愿认证', '获取验证码', '合同签署', '电子签', 
               'letSign', '签署协议（1）', '已签署', '下一步', '上一步',
               '授权信息', '授权比例', '签约']:
        found = kw in text
        print(f"  {kw}: {'✅' if found else '❌'}", flush=True)

# 检查所有页面
pages = requests.get('http://localhost:9223/json').json()
print(f"\n所有页面 ({len(pages)}):", flush=True)
for p in pages:
    url = p.get('url', '')
    print(f"  {p['title'][:30]} | {url[:80]}", flush=True)
