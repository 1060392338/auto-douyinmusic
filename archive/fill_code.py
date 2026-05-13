#!/usr/bin/env python3
"""填入验证码并确认签署"""
import time, os
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 切到letsign页面
targets = P.run_cdp('Target.getTargets')
for t in targets.get('targetInfos', []):
    url = t.get('url', '')
    if 'letsign.com/v2/open/sign' in url and t.get('type') == 'page':
        P.run_cdp('Target.activateTarget', targetId=t['targetId'])
        break
time.sleep(2)

# 填入验证码
P.run_js("""
(function() {
    var inps = document.querySelectorAll('input');
    for (var i = 0; i < inps.length; i++) {
        if (inps[i].placeholder && inps[i].placeholder.indexOf('验证码') >= 0) {
            var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            setter.call(inps[i], '847786');
            inps[i].dispatchEvent(new Event('input', {bubbles: true}));
            inps[i].dispatchEvent(new Event('change', {bubbles: true}));
            return;
        }
    }
})();
""")
time.sleep(2)
print('✅ 已填入验证码')

# 点击"确定"
P.run_js("""
(function() {
    var btns = document.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
        if (btns[i].textContent.trim() === '\u786e\u5b9a') {
            btns[i].scrollIntoView({behavior:'instant', block:'center'});
            ['mousedown','mouseup','click'].forEach(function(ev) {
                btns[i].dispatchEvent(new MouseEvent(ev, {
                    bubbles: true, cancelable: true, view: window, button: 0
                }));
            });
            return;
        }
    }
})();
""")
time.sleep(4)
print('✅ 已点击「确定」')

# 看结果
print('URL:', P.url)
print('Title:', P.title)
body = P.ele('tag:body').text

if '签署成功' in body or '已完成' in body:
    print('🎉 签署成功！')
elif '错误' in body:
    print('❌ 签署失败')
else:
    print('页面状态:', body[-300:])
