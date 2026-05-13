#!/usr/bin/env python3
"""检查发布表单"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
print("URL:", P.url)
time.sleep(2)

# 用原生方法获取页面文本
body = P.ele('tag:body')
text = body.text
print("=== 页面文本 ===")
print(text[:800])

print("\n=== 所有按钮 ===")
for b in P.eles('tag:button'):
    t = b.text.strip()
    if t:
        print(f"  [{t}]")

print("\n=== 所有input ===")
for i, inp in enumerate(P.eles('tag:input')):
    pl = inp.attr('placeholder') or ''
    typ = inp.attr('type') or ''
    name = inp.attr('name') or ''
    if pl or name:
        print(f"  [{i}] type={typ} placeholder={pl} name={name}")

print("\n=== 所有textarea ===")
for i, ta in enumerate(P.eles('tag:textarea')):
    pl = ta.attr('placeholder') or ''
    print(f"  [{i}] placeholder={pl}")
