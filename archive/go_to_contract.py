import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 滚动到底部
P.run_js('window.scrollTo(0, document.body.scrollHeight);')
time.sleep(3)

# 点底部可见的下一步
P.run_js("""
(function(){
    var btns = document.querySelectorAll('button');
    var last = null;
    for(var i=0; i<btns.length; i++){
        if(btns[i].textContent.trim() === '\u4e0b\u4e00\u6b65' && btns[i].offsetParent !== null){
            last = btns[i];
        }
    }
    if(last){
        last.scrollIntoView({behavior:'instant', block:'center'});
        last.click();
    }
})();
""")
time.sleep(5)
print('URL:', P.url[:80])

# 看看有没有letsign
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
    print('进入letsign:', P.title[:40])
    
    # 批量签署
    P.run_js("""
    (function(){
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++){
            if(btns[i].textContent.trim() === '\u6279\u91cf\u7b7e\u7f72'){
                btns[i].scrollIntoView({behavior:'instant', block:'center'});
                btns[i].click();
                return;
            }
        }
    })();
    """)
    time.sleep(3)
    
    # 获取验证码
    P.run_js("""
    (function(){
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++){
            if(btns[i].textContent.trim() === '\u83b7\u53d6\u9a8c\u8bc1\u7801'){
                btns[i].scrollIntoView({behavior:'instant', block:'center'});
                btns[i].click();
                return;
            }
        }
    })();
    """)
    time.sleep(2)
    print('=' * 40)
    print('验证码已发送！陛下请发给我！')
    print('=' * 40)
else:
    print('❌ 未找到letsign')
    for t in targets.get('targetInfos', []):
        if t.get('type') == 'page':
            print(f'  page: {t.get("url","")[:80]}')
