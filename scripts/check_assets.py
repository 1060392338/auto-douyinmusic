"""检查资产页"""
import json, time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
P.get("https://music.douyin.com/studio/assets")
time.sleep(5)

r = P.run_js("""
const items = document.querySelectorAll('[class*="assetItemWrapper"]');
const res = [];
items.forEach(el => {
    const title = el.getAttribute('data-title') || '';
    const hasIssue = el.textContent.includes('发行全曲');
    const dur = (el.querySelector('[class*="assetDuration"]') || {}).textContent || '';
    const ts = (el.querySelector('[class*="assetTimestamp"]') || {}).textContent || '';
    res.push({title: title.substring(0,20), dur, ts, canIssue: hasIssue});
});
return JSON.stringify(res);
""")

items = json.loads(r) if r else []
print(f"\n资产页共 {len(items)} 首作品：")
for i, a in enumerate(items, 1):
    flag = '🔴 可发行' if a['canIssue'] else '⚪'
    print(f"  {i}. {a['title']:12s} {a['dur']} {a['ts']} {flag}")
