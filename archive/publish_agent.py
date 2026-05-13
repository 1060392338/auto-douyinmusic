#!/usr/bin/env python3
"""抖音音乐全曲发布 Agent v2 - 学到的坑都修了"""
import time, json, os, sys, requests
from DrissionPage import ChromiumPage, ChromiumOptions

PORT = 9223
DATA = os.path.expanduser("~/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data")
URL_ASSETS = "https://music.douyin.com/studio/assets"
URL_PUBLISH_BASE = "https://music.douyin.com/console/complete-publish"

class Publisher:
    def __init__(self):
        co = ChromiumOptions()
        co.set_argument(f'--remote-debugging-port={PORT}')
        co.set_argument('--user-data-dir', DATA)
        co.set_argument('--remote-allow-origins', '*')
        co.set_argument('--window-position', '-32000,-32000')
        co.set_argument('--no-first-run')
        co.set_argument('--disable-popup-blocking')
        self.page = ChromiumPage(addr_or_opts=co)
        time.sleep(2)

    def cdp_click(self, x, y):
        self.page.run_cdp("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
        time.sleep(0.03)
        self.page.run_cdp("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)

    def find_and_cdp_click(self, text):
        """找到可见按钮的坐标并用CDP点击"""
        self.page.run_js('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(0.5)
        js = """
            var btns = document.querySelectorAll('button');
            for (var i=0; i<btns.length; i++) {
                if ((btns[i].textContent||'').trim() === '%s') {
                    var r = btns[i].getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) {
                        return JSON.stringify({x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)});
                    }
                }
            }
            return 'null';
        """ % text
        c = json.loads(self.page.run_js(js))
        if c:
            self.cdp_click(c['x'], c['y'])
            return True
        return False

    def dismiss_alert(self):
        try:
            self.page.handle_alert(accept=True)
        except: pass

    def go_assets(self):
        self.dismiss_alert()
        self.page.get(URL_ASSETS)
        time.sleep(4)
        if '登录创作实验室' in self.page('tag:body').text:
            print("❌ 未登录!")
            return False
        print("✅ 已进入资产页")
        return True

    def click_publish_btn(self):
        # Try take over existing publish tab
        try:
            resp = requests.get(f"http://127.0.0.1:{PORT}/json", timeout=2)
            for t in resp.json():
                if 'complete-publish' in t.get('url',''):
                    requests.get(f"http://127.0.0.1:{PORT}/json/activate/{t['id']}", timeout=2)
                    time.sleep(2)
                    print("复用发布页")
                    return True
        except: pass

        # Scroll to make cards visible
        self.page.run_js('window.scrollTo(0, 200)')
        time.sleep(1)

        # Click first 发行全曲 via coordinate click on the card
        js = """
            var cards = document.querySelectorAll('[class*=assetItemWrapper]');
            if (cards.length) {
                cards[0].scrollIntoView({block:'center'});
                var r=cards[0].getBoundingClientRect();
                return JSON.stringify({x:Math.round(r.left+r.width*0.8), y:Math.round(r.top+r.height/2)});
            }
            return 'null';
        """
        c = json.loads(self.page.run_js(js))
        print(f"卡片坐标: {c}")
        if c:
            self.cdp_click(c['x'], c['y'])
            time.sleep(5)
            url = self.page.run_js('return window.location.href')
            if 'complete-publish' in url:
                print("已进入发布页")
                return True
            else:
                # Try again with the text div element directly
                self.page.run_js("""
                    var all = document.querySelectorAll('div');
                    for (var i=0; i<all.length; i++) {
                        if ((all[i].textContent||'').trim() === '发行全曲') {
                            all[i].scrollIntoView({block:'center'});
                            all[i].click();
                            return;
                        }
                    }
                """)
                time.sleep(5)
                url = self.page.run_js('return window.location.href')
                if 'complete-publish' in url:
                    print("已进入发布页(div click)")
                    return True
        
        print(f"最终URL: {self.page.run_js('return window.location.href')}")
        return False

    def step1_to_step2(self):
        if not self.find_and_cdp_click('下一步'):
            print("Step1→Step2 失败")
            return False
        time.sleep(4)
        print("Step1→Step2 ✅")
        return True

    def step2_select_no_link(self):
        self.page.run_js('window.scrollTo(0, document.body.scrollHeight * 0.6)')
        time.sleep(1)
        # Click select
        self.page.run_js("""
            var s=document.querySelectorAll('.semi-select');
            for(var i=0;i<s.length;i++){if((s[i].textContent||'').indexOf('有主页链接')>=0){s[i].scrollIntoView({block:'center'});s[i].click();}}
        """)
        time.sleep(2)
        # Click 无主页链接
        r = self.page.run_js("""
            var d=document.querySelectorAll('.semi-portal div,.semi-popover div');
            for(var i=0;i<d.length;i++){if((d[i].textContent||'').trim()==='无主页链接'){d[i].dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));d[i].dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));d[i].dispatchEvent(new MouseEvent('click',{bubbles:true}));return'ok';}}
            return'nf';
        """)
        print(f"无主页链接: {r}")
        time.sleep(1)
        if '无主页链接' not in self.page('tag:body').text:
            return False
        # Click 下一步
        if not self.find_and_cdp_click('下一步'):
            return False
        time.sleep(4)
        print("Step2→Step3 ✅")
        return True

    def step3_sign(self):
        # Check for letsign tab
        try:
            resp = requests.get(f"http://127.0.0.1:{PORT}/json", timeout=2)
            for t in resp.json():
                if 'letsign' in t.get('url',''):
                    requests.get(f"http://127.0.0.1:{PORT}/json/activate/{t['id']}", timeout=2)
                    time.sleep(3)
                    print(f"letsign: {t['url'][:80]}")
                    return "letsign_tab"
        except: pass
        if '协议签署' in self.page('tag:body').text:
            return "签署页"
        return None

    def send_code_in_letsign(self):
        """在 letsign 标签页点批量签署+发验证码"""
        from DrissionPage import Chromium
        b = Chromium(PORT)
        tabs = b.get_tabs()
        print(f"tabs: {len(tabs)}")
        for t in tabs:
            url = t.run_js('return window.location.href')
            print(f"  {url[:60]}")
        b.quit()
        return "tab_listed"

    def close(self):
        self.page.quit()


def run():
    p = Publisher()
    if not p.go_assets():
        p.close()
        return False
    if not p.click_publish_btn():
        p.close()
        return False
    if not p.step1_to_step2():
        p.close()
        return False
    if not p.step2_select_no_link():
        p.close()
        return False
    
    result = p.step3_sign()
    print(f"Step3 status: {result}")
    
    if result == "letsign_tab":
        p.send_code_in_letsign()
    
    p.close()
    return True

if __name__ == "__main__":
    run()
