#!/usr/bin/env python3
"""删除资产页重复歌曲（同名同长，保留最新）"""
import time, json
from DrissionPage import ChromiumPage

TO_DELETE = [
    ("无章", "02:39", "2026-05-10 19:06"),
    ("无章", "02:39", "2026-05-10 09:14"),
    ("空白页", "02:43", "2026-05-10 09:36"),
    ("星落肩头", "03:01", "2026-05-10 09:34"),
    ("无序歌", "02:42", "2026-05-10 09:18"),
    ("杂乱思绪", "03:14", "2026-05-10 09:08"),
]

P = ChromiumPage(addr_or_opts="127.0.0.1:9222")

def log(msg):
    print(msg, flush=True)

for name, dur, date in TO_DELETE:
    log(f"\n🗑 {name} {dur} {date}")
    
    P.get('https://music.douyin.com/studio/assets')
    time.sleep(5)
    
    # 找这个条目
    r = P.run_cdp('Runtime.evaluate', expression=f'''
    (()=>{{
        var items = document.querySelectorAll('[class*="assetItemWrapper"]');
        for(var i=0;i<items.length;i++){{
            var t = items[i].textContent;
            if(t.includes("{name}") && t.includes("{dur}") && t.includes("{date}")){{
                var icon = items[i].querySelector('span[class*="menu-more-icon"]');
                if(icon){{
                    icon.dispatchEvent(new MouseEvent('click',{{bubbles:true,cancelable:true}}));
                    return 'menu_ok';
                }}
            }}
        }}
        return 'not_found';
    }})()
    ''')
    status = r.get('result',{}).get('value','')
    log(f'  菜单: {status}')
    if status != 'menu_ok':
        log(f'  ⚠️ 没找到，跳过')
        continue
    
    time.sleep(2)
    
    # 点删除
    P.run_cdp('Runtime.evaluate', expression='''
    (()=>{
        var all = document.querySelectorAll('*');
        for(var i=0;i<all.length;i++){
            if(all[i].offsetParent !== null && all[i].textContent.trim() === '删除'){
                all[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                return 'del_ok';
            }
        }
        return 'no_del_btn';
    })()
    ''')
    log('  删除: ok')
    time.sleep(2)
    
    # 点确定
    P.run_cdp('Runtime.evaluate', expression='''
    (()=>{
        var btns = document.querySelectorAll('button');
        for(var i=0;i<btns.length;i++){
            if(btns[i].textContent.trim() === '确定'){
                btns[i].click();
                return 'confirm_ok';
            }
        }
        return 'no_confirm';
    })()
    ''')
    log('  确认: ok')
    time.sleep(3)

log('\n✅ 全部完成！')
