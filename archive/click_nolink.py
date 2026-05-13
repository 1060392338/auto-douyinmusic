import time, sys
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 点击"有主页链接"这个按钮/选项，切换为"无主页链接"
P.run_js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++){
        var t = all[i].textContent;
        if(t && t.trim() === '\u6709\u4e3b\u9875\u94fe\u63a5'){
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].click();
            console.log('点击了有主页链接');
            return;
        }
    }
    console.log('未找到有主页链接');
})();
""")
time.sleep(3)

# 确认已切换
P.run_js('document.title = document.body.innerText.substring(0, 2000);')
time.sleep(1)
full = P.title
idx = full.find('艺人信息补充')
if idx >= 0:
    print('艺人区:', full[idx:idx+400])
    if '\u65e0\u4e3b\u9875' in full[idx:idx+400]:
        print('✅ 已切换为无主页链接')
    else:
        print('⚠️ 可能还没切换')
else:
    print('未找到艺人区')
