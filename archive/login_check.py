"""用验证码登录抖音音乐开放平台"""
import time, shutil
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 先导航到创作实验室触发登录弹窗
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(6)

print(f"URL: {P.url}", flush=True)
body = P.ele('tag:body').text
print(f"Text length: {len(body)}", flush=True)

# 检查登录状态
if 'AI 作词' in body or 'AI 作曲' in body or 'AI 编辑器' in body:
    print("✅ 已登录!", flush=True)
    # 直接去资产页
    P.run_js("window.location.href='https://music.douyin.com/asset/music';")
    time.sleep(5)
    body2 = P.ele('tag:body').text
    print(f"资产页 Text length: {len(body2)}", flush=True)
    if '蝉声漫旧夏' in body2:
        print("✅ 蝉声漫旧夏 在资产页找到", flush=True)
        # 找发行相关
        for kw in ['发行全曲', '已发布', '审核中', '发行成功', '已发行']:
            if kw in body2:
                print(f"✅ 关键词: {kw}", flush=True)
    else:
        print("❌ 蝉声漫旧夏 不在资产页", flush=True)
        # 列出歌曲
        lines = body2.split('\n')
        songs = [l.strip() for l in lines if 2 <= len(l.strip()) <= 8 and not l.strip().startswith(('0','1','2','3','4','5','6','7','8','9','/'))]
        if songs:
            print(f"可能的歌曲: {songs[:20]}", flush=True)
else:
    print("❌ 未登录，需要登录", flush=True)
    # 截图看当前状态
    P.get_screenshot('/tmp/douyin_login_state.png')
    shutil.copy('/tmp/douyin_login_state.png', '/Users/mac/.hermes/cache/screenshots/douyin_login_state.png')
    print("截图已保存", flush=True)
    # 检测登录弹窗
    if '登录创作实验室' in body or '扫码登录' in body:
        print("检测到登录弹窗", flush=True)
        # 切换到验证码登录tab
        tabs = P.eles('xpath://span[contains(.,"验证码登录")]')
        if tabs:
            tabs[0].click()
            time.sleep(2)
            print("已点击验证码登录", flush=True)
            # 输入手机号
            phone_input = P.ele('css:input[placeholder="请输入手机号"]', timeout=3)
            if phone_input:
                phone_input.input('17620417470')
                time.sleep(1)
                print("已输入手机号", flush=True)
                # 点击获取验证码
                get_code = P.ele('xpath://span[contains(text(),"获取")]', timeout=3)
                if get_code:
                    get_code.click()
                    print("已点击获取验证码，等待用户输入...", flush=True)
                    P.get_screenshot('/tmp/douyin_after_click.png')
                    shutil.copy('/tmp/douyin_after_click.png', '/Users/mac/.hermes/cache/screenshots/douyin_after_click.png')
        else:
            print("未找到验证码登录tab", flush=True)
            # 尝试直接找手机号输入框
            phone_input = P.ele('css:input[placeholder="请输入手机号"]', timeout=2)
            if phone_input:
                print("找到手机号输入框（可能在验证码tab）", flush=True)
            else:
                print("完全没找到手机号输入框，可能是扫码页面", flush=True)
