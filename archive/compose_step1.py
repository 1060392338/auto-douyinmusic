#!/usr/bin/env python3
"""Step 1: 导航到作曲页 → 填灵感 → 点击生成 → 退出"""
import time, os, signal
from DrissionPage import ChromiumPage

def cleanup(signum, frame):
    os._exit(0)
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 导航到创作页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create';")
time.sleep(5)
print(f"📍 URL: {P.url}")

# 找 textarea
ta = P.ele('tag:textarea')
if not ta:
    print("❌ 找不到 textarea")
    os._exit(1)

S = "写一首关于夏日蝉鸣和旧时光的歌，旋律轻快带点怀旧，用吉他做主伴奏"
P.run_js(f"""
(function(text) {{
    var ta = document.querySelector('textarea');
    if (!ta) return;
    var setter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    setter.call(ta, text);
    ta.dispatchEvent(new Event('input', {{bubbles: true}}));
}})('{S}');
""")
time.sleep(1)
print("✅ 已填入灵感")

# 点击生成
btn = P.ele('xpath://button[contains(@class,"semi-button-primary") and contains(.,"生成")]')
if btn:
    btn.click()
    time.sleep(2)
    print("✅ 已点击生成，AI 作曲已启动！")
else:
    print("❌ 找不到生成按钮")
    os._exit(1)

# 检查是否真的开始生成
body = P.ele('tag:body').text
if '生成中' in body:
    print("✅ 确认页面显示「生成中」，Step 1 完成！")
else:
    print("⚠️ 未看到「生成中」，可能需要检查")
