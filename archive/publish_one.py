#!/usr/bin/env python3
"""
发布一首歌曲：资产页 → 发行全曲 → Step1下一步 → Step2无主页链接 → 下一步 → Step3批量签署 → 验证码
用法: python3 publish_one.py <歌名>
端口 9222，登录态在 data/douyin_music/default/chrome_data
"""
import sys, time, os
from DrissionPage import ChromiumPage, ChromiumOptions

PAGE = None
CDP_PORT = 9222
USER_DATA = os.path.expanduser("~/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data")

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def init_browser():
    global PAGE
    co = ChromiumOptions()
    co.set_local_port(CDP_PORT)
    co.set_user_data_path(USER_DATA)
    co.set_argument("--window-position=-32000,-32000")
    co.set_argument("--window-size=1920,1080")
    PAGE = ChromiumPage(co)
    log(f"已连接 端口{CDP_PORT}")

def go(url, wait=3):
    PAGE.get(url)
    time.sleep(wait)
    try: PAGE.wait.load_complete()
    except: pass
    log(f"导航: {PAGE.title}")

def dismiss():
    for t in ["离开", "取消"]:
        try: PAGE.ele(f"text:{t}", timeout=1).click(); time.sleep(0.5)
        except: pass

def click_txt(text, w=1):
    try:
        el = PAGE.ele(f"text:{text}", timeout=3)
        if el: el.click(); time.sleep(w); log(f"点击: {text}"); return True
    except: pass
    return False

def cdp_click(el):
    r = el.rect
    cx, cy = r['left']+r['width']/2, r['top']+r['height']/2
    PAGE.run_cdp(f"Input.dispatchMouseEvent({{type:'mousePressed',x:{cx},y:{cy},button:'left',clickCount:1}})")
    PAGE.run_cdp(f"Input.dispatchMouseEvent({{type:'mouseReleased',x:{cx},y:{cy},button:'left',clickCount:1}})")
    log(f"CDP点击 ({cx:.0f},{cy:.0f})")

def step1():
    log("--- Step1: 下一步 ---")
    time.sleep(2); dismiss()
    return click_txt("下一步", 3)

def step2():
    log("--- Step2: 无主页链接 ---")
    time.sleep(2); dismiss()
    for txt in ["有主页链接", "请选择", "主页链接"]:
        try: PAGE.ele(f"text:{txt}", timeout=2).click(); time.sleep(1); break
        except: continue
    for sel in [".OuY5i", "text:无主页链接"]:
        try: PAGE.ele(sel, timeout=2).click(); time.sleep(1); log("✅ 无主页链接"); break
        except: continue
    return click_txt("下一步", 3)

def step3():
    log("--- Step3: 批量签署 ---")
    time.sleep(3); dismiss()
    click_txt("批量签署", 2)
    time.sleep(2)
    log("--- 发送验证码 ---")
    for txt in ["发送验证码", "获取验证码"]:
        if click_txt(txt, 1): log("✅ 验证码已发送"); return True
    try: PAGE.ele(".ds-captcha-next__form-send", timeout=2).click(); log("✅ 验证码已发送(sel)"); return True
    except: pass
    return False

def publish(song):
    log(f"{'='*50}\n🎵 {song}\n{'='*50}")
    go("https://music.douyin.com/creation/song-management", 5)
    time.sleep(3)

    # 找卡片
    cards = PAGE.eles("[class*='song']", timeout=5)
    if not cards: cards = PAGE.eles("[class*='Song']", timeout=3)
    if not cards: cards = PAGE.eles("[class*='ListItem']", timeout=3)
    log(f"卡片: {len(cards) if cards else 0}")

    found = False
    if cards:
        for card in cards:
            try:
                if song not in (card.text or ""): continue
                log(f"找到: {song}")
                for el in card.eles("tag:button") + card.eles("tag:a") + card.eles("tag:span"):
                    if "发行" in (el.text or ""):
                        cdp_click(el); found = True; time.sleep(3); break
                if found: break
            except: continue

    if not found:
        # fallback: CDP 搜文本
        try:
            js = f"document.body.innerText.indexOf('{song}')"
            PAGE.run_cdp(f"Runtime.evaluate({{expression:'{js}'}})")
            log(f"文本搜索完成，但没找到可点击的发行按钮")
        except: pass
        return False

    time.sleep(2)
    tabs = PAGE.get_tabs(); log(f"标签页: {len(tabs)}")
    step1(); step2(); step3()

    try: PAGE.screenshot(path=f"/tmp/pub_{song}.png"); log(f"截图: /tmp/pub_{song}.png")
    except: pass
    log(f"📱 验证码已发送 -> /tmp/pub_{song}.png")
    return True

if __name__ == "__main__":
    song = sys.argv[1] if len(sys.argv) > 1 else "空白页"
    init_browser()
    try: publish(song)
    except Exception as e: log(f"❌ {e}"); import traceback; traceback.print_exc()
    log("脚本结束，浏览器未关闭")
