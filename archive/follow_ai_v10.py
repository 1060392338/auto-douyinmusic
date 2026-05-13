"""通过已发布文章找相关作者并关注"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 去头条搜索AI热点文章
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/search/?keyword=AI+大模型';")
time.sleep(8)

text = P.ele('tag:body', timeout=5).text
print(f"搜索页文本: {len(text)}字", flush=True)

# 找所有文章中的作者名和关注按钮  
P.run_js("""
// 检查页面所有元素的文本内容
var results = [];
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if ((t === '关注' || t === '+关注') && el.offsetParent !== null) {
        var rect = el.getBoundingClientRect();
        results.push({
            tag: el.tagName,
            text: t,
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            w: Math.round(rect.width),
            h: Math.round(rect.height),
            visible: rect.width > 0 && rect.height > 0 && rect.y > 50,
            parentText: (el.parentElement.textContent || '').substring(0, 50)
        });
    }
});
return JSON.stringify(results);
""")
time.sleep(2)

# 执行 JS 找关注按钮
result = P.run_js("""
(function() {
    var btns = [];
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if ((t === '关注' || t === '+ 关注') && el.offsetParent !== null) {
            var rect = el.getBoundingClientRect();
            if (rect.y > 60 && rect.width > 0) {
                btns.push({tag: el.tagName, cls: (el.className||'').substring(0,50), text: t, y: rect.y});
            }
        }
    });
    return JSON.stringify(btns);
})();
""")
print(f"\n关注按钮: {result}", flush=True)

# 如果没有找到，看看页面结构
if not result or (isinstance(result, str) and (result == 'None' or result == '[]')):
    print("\n未找到关注按钮，检查页面元素...", flush=True)
    # 看所有按钮
    btns = P.eles('tag:button')
    for b in btns:
        t = b.text.strip()
        if t:
            print(f"  按钮: '{t}' html={b.outer_html[:100]}", flush=True)

print("\n✅ 完成", flush=True)
