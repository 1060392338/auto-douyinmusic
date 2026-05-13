#!/usr/bin/env python3
"""用原生方法获取work-id"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
print("URL:", P.url)
time.sleep(3)

# 用原生eles找资产卡片
cards = P.eles('xpath://div[contains(@class,"assetItemWrapper")]')
print(f"卡片数: {len(cards)}")

for card in cards:
    title = card.attr('data-title') or ''
    work_id = card.attr('data-work-id') or ''
    if '蝉声漫旧夏' in card.text:
        print(f"找到蝉声漫旧夏! work_id={work_id}")
        if work_id:
            url = f"https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId={work_id}"
            print(f"导航到发布页: {url[:80]}")
            P.run_js(f"window.location.href='{url}';")
            time.sleep(6)
            print("新URL:", P.url)
            break
