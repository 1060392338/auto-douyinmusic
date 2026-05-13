#!/usr/bin/env python3
"""从资产页发歌：蝉声漫旧夏 → 预填表单 → 下一步 → 艺人链接 → 下一步 → 签署 → 等验证码"""
import time, sys
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)
print(f"1. 资产页: {P.url[:60]}")

# --- 点击发行全曲 ---
P.run_js("""
(function(){
    var cards = document.querySelectorAll("[class*='assetItemWrapper']");
    for(var i=0; i<cards.length; i++){
        if(cards[i].textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f')>=0){
            var all = cards[i].querySelectorAll('*');
            for(var j=0; j<all.length; j++){
                if(all[j].textContent.trim()==='\u53d1\u884c\u5168\u66f2'){
                    all[j].scrollIntoView({behavior:'instant', block:'center'});
                    setTimeout(function(){ all[j].click(); }, 200);
                    return;
                }
            }
        }
    }
})();
""")
time.sleep(6)
print(f"2. 发布表单: {P.url[:80]}")
print("   URL中是否包含complete-publish:", 'complete-publish' in P.url)

if 'complete-publish' not in P.url:
    # 点击没生效，用另一个方法
    print("   点击失效! 用XPath重试...")
    P.run_js("""
    (function(){
        var xpath = \"//*[contains(text(),'\u8749\u58f0\u6f2b\u65e7\u590f')]//*[text()='\u53d1\u884c\u5168\u66f2']\";
        var result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        var el = result.singleNodeValue;
        if(el){
            el.scrollIntoView({behavior:'instant', block:'center'});
            setTimeout(function(){ el.click(); }, 200);
        }
    })();
    """)
    time.sleep(6)
    print(f"   重试后: {P.url[:80]}")
    
if 'complete-publish' not in P.url:
    print("❌ 还是没进入发布表单，退出")
    sys.exit(1)

print("✅ 进入发布表单，信息应该已预填！")

# --- 下一步（到艺人信息/授权） ---
P.run_js("""
(function(){
    var btns = document.querySelectorAll('button');
    for(var i=0; i<btns.length; i++){
        if(btns[i].textContent.trim()==='\u4e0b\u4e00\u6b65'){
            var r = btns[i].getBoundingClientRect();
            if(r.width>0 && r.height>0 && r.top>0){
                btns[i].scrollIntoView({behavior:'instant', block:'center'});
                btns[i].click();
                return;
            }
        }
    }
})();
""")
time.sleep(5)
print(f"3. 下一步后: {P.url[:80]}")

# --- 艺人信息 - 选"无主页链接" ---
time.sleep(2)
P.run_js("""
(function(){
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++){
        if(all[i].textContent && all[i].textContent.trim() === '\u65e0\u4e3b\u9875\u94fe\u63a5'){
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].click();
            return;
        }
    }
})();
""")
time.sleep(2)
print("4. 已选无主页链接")

# --- 到底部点下一步（到合同） ---
P.run_js("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

P.run_js("""
(function(){
    var btns = document.querySelectorAll('button');
    var last = null;
    for(var i=0; i<btns.length; i++){
        if(btns[i].textContent.trim()==='\u4e0b\u4e00\u6b65') last = btns[i];
    }
    if(last){
        last.scrollIntoView({behavior:'instant', block:'center'});
        last.click();
    }
})();
""")
time.sleep(5)
print(f"5. 底部下一步后: {P.url[:80]}")

# --- 找letsign ---
P.run_js("""
(function(){
    var iframes = document.querySelectorAll('iframe');
    for(var i=0; i<iframes.length; i++){
        var s = iframes[i].src || '';
        if(s.indexOf('letsign')>=0){
            window.open(s);
            return;
        }
    }
})();
""")
time.sleep(5)

# 切到letsign
targets = P.run_cdp('Target.getTargets')
letsign_id = None
for t in targets.get('targetInfos', []):
    url = t.get('url','')
    if 'letsign.com/v2/open/sign' in url and t.get('type') == 'page':
        letsign_id = t['targetId']
        break

if letsign_id:
    P.run_cdp('Target.activateTarget', targetId=letsign_id)
    time.sleep(4)
    print(f"6. letsign页: {P.title[:40]}")
    
    # 取消全选（如果有checkbox选中）
    time.sleep(1)
    
    # 点批量签署
    P.run_js("""
    (function(){
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++){
            if(btns[i].textContent.trim()==='\u6279\u91cf\u7b7e\u7f72'){
                btns[i].scrollIntoView({behavior:'instant', block:'center'});
                btns[i].click();
                return;
            }
        }
    })();
    """)
    time.sleep(3)
    print("7. 已点批量签署")
    
    # 点获取验证码
    P.run_js("""
    (function(){
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++){
            if(btns[i].textContent.trim()==='\u83b7\u53d6\u9a8c\u8bc1\u7801'){
                btns[i].scrollIntoView({behavior:'instant', block:'center'});
                btns[i].click();
                return;
            }
        }
    })();
    """)
    time.sleep(2)
    print("=" * 40)
    print("STEP 8: 等待验证码...")
    print("=" * 40)
    print("陛下，验证码已发送手机，请查收后发给我！")
else:
    print("❌ 找不到letsign页面")
    # 看看有哪些页面
    for t in targets.get('targetInfos', []):
        if t.get('type') == 'page':
            print(f"  page: {t.get('url','')[:80]}")
