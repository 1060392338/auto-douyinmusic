"""点击发行全曲 - 全新连接"""
import time
from DrissionPage import ChromiumPage

print("连接 Chrome...", flush=True)
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
print("✅ 已连接", flush=True)

# 导航到资产页
print("导航到资产页...", flush=True)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)
print(f"URL: {P.url}", flush=True)

body = P.ele('tag:body').text
print(f"文本长度: {len(body)}", flush=True)

# 检查登录状态
if '登录' in body and ('扫码' in body or '手机号' in body):
    print("❌ 未登录", flush=True)
else:
    print("✅ 已登录", flush=True)
    
    # 找蝉声漫旧夏的发行全曲
    has_song = '蝉声漫旧夏' in body
    has_publish = '发行全曲' in body
    print(f"有蝉声漫旧夏: {has_song}, 有发行全曲: {has_publish}", flush=True)
    
    if has_song and has_publish:
        # 点击发行全曲
        P.run_js("""
(function() {
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent && all[i].textContent.trim() === '发行全曲') {
            var p = all[i].parentElement;
            while (p) {
                if (p.textContent.indexOf('蝉声漫旧夏') >= 0) {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                        all[i].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                    });
                    return;
                }
                p = p.parentElement;
            }
        }
    }
})();
""")
        time.sleep(5)
        print(f"点击后URL: {P.url}", flush=True)
        body2 = P.ele('tag:body').text
        print(f"页面文本 (前2000):", flush=True)
        print(body2[:2000], flush=True)
        
        if 'complete-publish' in P.url or 'console' in P.url:
            print("✅ 进入发布表单!", flush=True)
        elif '下一步' in body2 or '歌曲信息' in body2:
            print("✅ 可能进入了发布表单", flush=True)
        else:
            print("❌ 未进入发布表单", flush=True)
    else:
        print("❌ 资产页内容:", flush=True)
        print(body[:1500], flush=True)
