"""检查页面底部 + 滚动到合同区"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)

# 获取完整页面文本
body = P.ele('tag:body').text
print(f"总文本长度: {len(body)}", flush=True)
print(f"最后1000字:", flush=True)
print(body[-1000:], flush=True)

# 检查是否有iframe
pages = requests.get('http://localhost:9223/json').json()
for p in pages:
    url = p.get('url', '')
    if 'letsign' in url or 'summon' in url:
        print(f"合同页: {url[:100]}", flush=True)

# 检查是否有签署协议弹窗
print("\n搜索关键文本:", flush=True)
for kw in ['批量签署', '意愿认证', '获取验证码', '合同签署', '电子签', 'letSign', '签署协议（1）', '已签署']:
    found = kw in body
    print(f"  {kw}: {'✅' if found else '❌'}", flush=True)

# 滚动到底部
P.run_js("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# 再次检查
body2 = P.ele('tag:body').text
if body2 != body:
    print(f"\n滚动后文本变了! 新长度: {len(body2)}", flush=True)
    print(f"滚动后底部1000字:", flush=True)
    print(body2[-1000:], flush=True)

# 截个图
P.get_screenshot('/tmp/douyin_publish_bottom.png')
import shutil
shutil.copy('/tmp/douyin_publish_bottom.png', '/Users/mac/.hermes/cache/screenshots/douyin_publish_bottom.png')
print("\n截图已保存", flush=True)
