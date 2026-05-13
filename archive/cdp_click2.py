import time, json
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
print("URL:", P.url[:60])

# 获取发行全曲的坐标并存入document.title
P.run_js("""
(function(){
    var cards = document.querySelectorAll("[class*='assetItemWrapper']");
    for(var i=0; i<cards.length; i++){
        if(cards[i].textContent.indexOf('蝉声漫旧夏')>=0){
            var all = cards[i].querySelectorAll('*');
            for(var j=0; j<all.length; j++){
                if(all[j].textContent.trim()==='发行全曲'){
                    var r = all[j].getBoundingClientRect();
                    document.title = JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                    console.log("found:", r.left, r.top, r.width, r.height);
                    return;
                }
            }
        }
    }
    document.title = 'NOT_FOUND';
})();
""")
time.sleep(1)
pos_str = P.title
print("坐标:", pos_str)

if pos_str and pos_str != 'NOT_FOUND':
    pos = json.loads(pos_str)
    mx, my = pos['x'], pos['y']
    print(f"点击坐标: ({mx}, {my})")
    
    # CDP双击确保SPA响应
    for _ in range(2):
        P.run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=mx, y=my, button='left', clickCount=1)
        time.sleep(0.05)
        P.run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=mx, y=my, button='left', clickCount=1)
        time.sleep(0.05)
    time.sleep(5)
    print("点击后URL:", P.url[:80])
    
    # 如果没反应，用scrollIntoView后再点一次
    if 'complete-publish' not in P.url:
        print("再次点击(强刷)...")
        P.run_js("""
        (function(){
            var cards = document.querySelectorAll("[class*='assetItemWrapper']");
            for(var i=0; i<cards.length; i++){
                if(cards[i].textContent.indexOf('蝉声漫旧夏')>=0){
                    cards[i].scrollIntoView({behavior:'instant', block:'center'});
                    var all = cards[i].querySelectorAll('*');
                    for(var j=0; j<all.length; j++){
                        if(all[j].textContent.trim()==='发行全曲'){
                            var r = all[j].getBoundingClientRect();
                            document.title = JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                            return;
                        }
                    }
                }
            }
        })();
        """)
        time.sleep(2)
        pos2 = P.title
        print("新坐标:", pos2)
        if pos2 and pos2 != 'NOT_FOUND':
            pos = json.loads(pos2)
            mx, my = pos['x'], pos['y']
            for _ in range(3):
                P.run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=mx, y=my, button='left', clickCount=1)
                time.sleep(0.1)
                P.run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=mx, y=my, button='left', clickCount=1)
                time.sleep(0.1)
            time.sleep(5)
            print("最终URL:", P.url[:80])
else:
    print("发行全曲不在视口，先滚动")
