"""深度探查资产页"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 导航到资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/asset/music';")
time.sleep(10)  # 让 SPA 完全渲染

print(f"URL: {P.url}", flush=True)

# 用 JS 获取完整的 body innerHTML 和 outerHTML
js_result = P.run_js("""
(function() {
    return JSON.stringify({
        htmlLen: document.body.innerHTML.length,
        textLen: document.body.innerText.length,
        text: document.body.innerText.substring(0, 5000),
        htmlSample: document.body.innerHTML.substring(0, 3000)
    });
})();
""")
print(f"JS result: {js_result}", flush=True)

# 检查是否有特定元素
for sel in ['[class*="assetItemWrapper"]', '[class*="assetInfo"]', '[class*="issuedDetail"]', 
            '[class*="empty"]', '[class*="loading"]', '[class*="noData"]', 'button', 'img']:
    els = P.eles(sel)
    print(f"选择器 {sel}: 找到 {len(els)} 个元素", flush=True)
    if els and len(els) <= 5:
        for e in els:
            try:
                html = e.outer_html[:200]
                print(f"  -> {html}", flush=True)
            except:
                pass

# 滚动到底部
P.run_js("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# 再次检查
body = P.ele('tag:body').text
print(f"滚动后 text length: {len(body)}", flush=True)

# 检查发布状态
for kw in ['蝉声漫旧夏', '发行全曲', '已发行', '审核中', '发布']:
    if kw in body:
        print(f"✅ 找到: {kw}", flush=True)
    else:
        print(f"❌ 没有: {kw}", flush=True)
        
# 检查所有 asset 卡片
cards = P.eles('xpath://div[contains(@class,"assetItemWrapper")]')
print(f"\n资产卡片数: {len(cards)}", flush=True)
for card in cards:
    print(f"卡片: {card.text[:200]}", flush=True)
