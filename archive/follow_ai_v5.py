"""去AI账号主页关注"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 已知AI大V账号，直接访问主页
ai_accounts = [
    "AI科技评论",
    "AI大数据模型交易",
    "AI云科技",
    "量子位",
    "机器之心",
    "新智元",
    "36氪",
]

# 搜索每个账号并点进主页关注
for name in ai_accounts:
    print(f"\n=== 关注 {name} ===", flush=True)
    
    # 搜索该账号
    search_url = f'https://so.toutiao.com/search/?keyword={name}&dvpf=pc&type=user&pd=synthesis&source=search_subtab_switch'
    P.run_js(f"window.onbeforeunload=null;window.location.href='{search_url}';")
    time.sleep(6)
    
    text = P.ele('tag:body', timeout=5).text
    print(f"  搜索页文本: {len(text)}字", flush=True)
    
    if name in text:
        # 点击用户卡片
        P.run_js(f"""
        document.querySelectorAll('*').forEach(function(el) {{
            var t = (el.textContent || '').trim();
            if (t === '{name}' && el.offsetParent !== null) {{
                el.scrollIntoView({{behavior:'instant',block:'center'}});
                el.focus();
                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {{
                    el.dispatchEvent(new PointerEvent(ev, {{bubbles:true, cancelable:true}}));
                }});
            }}
        }});
        """)
        time.sleep(5)
        
        text2 = P.ele('tag:body', timeout=5).text
        print(f"  主页: {text2[:300]}", flush=True)
        
        # 关注
        if '关注' in text2:
            P.run_js("""
            document.querySelectorAll('span, div, button').forEach(function(el) {
                var t = (el.textContent || '').trim();
                if (t === '关注' && el.offsetParent !== null) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                }
            });
            """)
            time.sleep(2)
            text3 = P.ele('tag:body', timeout=5).text
            if '已关注' in text3:
                print(f"  ✅ 已关注 {name}", flush=True)
            else:
                print(f"  ❌ 关注可能未成功", flush=True)
        else:
            print(f"  ❌ 主页无关注按钮", flush=True)
    else:
        print(f"  ❌ 未找到 {name}", flush=True)
    
    time.sleep(2)

print("\n✅ 关注流程完成", flush=True)
