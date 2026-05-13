try:
    import time
    from DrissionPage import ChromiumPage
    P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
    time.sleep(2)
    
    # 查找蝉声漫旧夏卡片中"发行全曲"的位置
    x, y = P.run_js("""
    (function(){
        var cards = document.querySelectorAll("[class*='assetItemWrapper']");
        for(var i=0; i<cards.length; i++){
            if(cards[i].textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f')>=0){
                var all = cards[i].querySelectorAll('*');
                for(var j=0; j<all.length; j++){
                    if(all[j].textContent.trim()==='\u53d1\u884c\u5168\u66f2'){
                        var r = all[j].getBoundingClientRect();
                        return JSON.stringify({x: r.left + r.width/2, y: r.top + r.height/2, w: r.width, h: r.height});
                    }
                }
            }
        }
        return 'not found';
    })();
    """)
    print(f"位置: {x}")
    
    if x and x != 'not found' and x != 'None':
        import json
        pos = json.loads(x)
        mx, my = int(pos['x']), int(pos['y'])
        print(f"坐标: ({mx}, {my}) 大小: {pos['w']}x{pos['h']}")
        
        # 用CDP精确点击
        P.run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=mx, y=my, button='left', clickCount=1)
        time.sleep(0.1)
        P.run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=mx, y=my, button='left', clickCount=1)
        time.sleep(0.5)
        P.run_cdp('Input.dispatchMouseEvent', type='mousePressed', x=mx, y=my, button='left', clickCount=1)
        time.sleep(0.1)
        P.run_cdp('Input.dispatchMouseEvent', type='mouseReleased', x=mx, y=my, button='left', clickCount=1)
        time.sleep(4)
        
        print(f"点击后URL: {P.url[:80]}")
    else:
        print("x为空:", x)
except Exception as e:
    print(f"错误: {e}")
