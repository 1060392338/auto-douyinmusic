"""切换到已打开的发布表单标签页"""
import time, json, requests

# 用 CDP 直接交互
WS_URL = "ws://localhost:9223/devtools/browser/300513dd-ad24-468d-bf85-0f325ed18d21"

# 找发布页面的 target ID
resp = requests.get('http://localhost:9223/json').json()
publish_target = None
assets_target = None
for p in resp:
    if 'complete-publish' in p.get('url', ''):
        publish_target = p['id']
        print(f"找到发布页: {p['url'][:80]}", flush=True)
    if 'studio/assets' in p.get('url', ''):
        assets_target = p['id']
        print(f"找到资产页: {p['url'][:60]}", flush=True)

if not publish_target:
    print("❌ 发布页不存在", flush=True)
else:
    # 用 CDP 切换到发布页并检查状态
    from DrissionPage import ChromiumPage
    P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
    time.sleep(1)
    
    # 切换到发布页
    try:
        P.run_cdp('Target.activateTarget', targetId=publish_target)
        time.sleep(3)
        print(f"当前URL: {P.url}", flush=True)
    except Exception as e:
        print(f"切换失败: {e}", flush=True)
    
    # 检查是否有弹窗
    try:
        has_dialog = P.run_cdp('Page.getJavaScriptDialogInfo')
        print(f"弹窗信息: {has_dialog}", flush=True)
        if has_dialog.get('hasDialog'):
            P.run_cdp('Page.handleJavaScriptDialog', accept=True)
            print("已处理弹窗", flush=True)
            time.sleep(2)
    except Exception as e:
        print(f"弹窗检查失败: {e}", flush=True)
    
    # 获取页面文本
    try:
        body = P.ele('tag:body').text
        print(f"发布页文本 (len={len(body)}):", flush=True)
        print(body[:2000], flush=True)
    except Exception as e:
        print(f"获取文本失败: {e}", flush=True)
