"""导出5首剩余歌曲 - 端口9222 - 逐首运行"""
import sys, time, subprocess

SONGS = ["杂乱思绪", "无章", "无序歌", "星落肩头", "空白页"]

for i, song in enumerate(SONGS):
    print(f"\n{'='*60}")
    print(f"[{i+1}/5] 🎵 {song}")
    print(f"{'='*60}", flush=True)
    
    result = subprocess.run(
        ["python3", "-c", f"""
import sys, time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')

def js(code, d=None):
    for _ in range(2):
        try: return P.run_js(code)
        except:
            try: P.handle_alert(accept=True)
            except: pass
            time.sleep(1)
    return d

for _ in range(3):
    try: P.handle_alert(accept=True); time.sleep(0.3)
    except: break

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create'")
time.sleep(8)

song = '{song}'
print(f'=== 导出 {{song}} ===', flush=True)

# 1. 点素材
code = 'var items=document.querySelectorAll(\\'[class*=\"titleRow\"]\\');for(var i=0;i<items.length;i++){{if(items[i].textContent.includes(\"{song}\")){{[\"pointerdown\",\"pointerup\",\"mousedown\",\"mouseup\",\"click\"].forEach(function(t){{items[i].dispatchEvent(new PointerEvent(t,{{bubbles:true,cancelable:true}}))}});return \"clicked\"}}}}return \"not found\"'
r = P.run_js('(' + code + ')()')
print(f'1. 素材: {{r}}', flush=True)
time.sleep(3)

# 2. AI编辑
P.run_js('document.querySelectorAll(\\'button[class*=\"aiEditButton\"]\\').forEach(b=>{{b.dispatchEvent(new MouseEvent(\"click\",{{bubbles:!0,cancelable:!0,view:window,button:0}}))}})')
time.sleep(3)
print('2. AI编辑 OK', flush=True)

# 3. 去AI编辑器
P.run_js('document.querySelector(\\'button[class*=\"primaryBtn\"]\\')?.scrollIntoView({{behavior:\"instant\",block:\"center\"}})')
time.sleep(1)
for att in range(3):
    P.run_js('document.querySelectorAll(\\'button[class*=\"primaryBtn\"]\\').forEach(b=>{{b.focus();[\"pointerdown\",\"pointerup\",\"mousedown\",\"mouseup\",\"click\"].forEach(t=>{{b.dispatchEvent(new PointerEvent(t,{{bubbles:!0,cancelable:!0}}))}})}})')
    time.sleep(6)
    if 'playground' in P.url: break
    print(f'  重试...', flush=True)
P.run_js('window.onbeforeunload=null;window.alert=function(){{}}')
print(f'3. 编辑器: {{"OK" if \"playground\" in P.url else \"FAIL\"}}', flush=True)

# 4. 等加载
time.sleep(12)

# 5. 点导出
P.run_js('document.querySelectorAll(\\'button.semi-button-secondary\\').forEach(b=>{{if(b.textContent.trim()===\"导出\"){{[\"mousedown\",\"mouseup\",\"click\"].forEach(t=>{{b.dispatchEvent(new MouseEvent(t,{{bubbles:!0,cancelable:!0,view:window,button:0}}))}})}}}})')
time.sleep(5)

has = P.run_js('return document.body.textContent.includes(\"并轨导出\")')
if not has:
    print('  再点导出...', flush=True)
    P.run_js('document.querySelectorAll(\\'button.semi-button-secondary\\').forEach(b=>{{if(b.textContent.trim()===\"导出\")b.dispatchEvent(new MouseEvent(\"click\",{{bubbles:!0,cancelable:!0}}))}})')
    time.sleep(5)
    has = P.run_js('return document.body.textContent.includes(\"并轨导出\")')
print(f'5. 弹窗: {{\"OK\" if has else \"FAIL\"}}', flush=True)

if has:
    # 6. 改歌名
    P.run_js('var inps=document.querySelectorAll(\"input\");for(var i=0;i<inps.length;i++){{if(inps[i].value.includes(\"新项目\")){{inps[i].disabled=false;inps[i].removeAttribute(\"disabled\");Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,\"value\").set.call(inps[i],\"{song}\");inps[i].dispatchEvent(new Event(\"input\",{{bubbles:!0}}));inps[i].dispatchEvent(new Event(\"change\",{{bubbles:!0}}))}}}}')
    print('6. 改歌名 OK', flush=True)
    time.sleep(1)
    
    # 7. 确认导出
    P.run_js('document.querySelectorAll(\\'button.semi-button\\').forEach(b=>{{var t=b.textContent.trim();if(t===\"导出\"||t===\"并轨导出\"||t===\"确认导出\"){{[\"mousedown\",\"mouseup\",\"click\"].forEach(tt=>{{b.dispatchEvent(new MouseEvent(tt,{{bubbles:!0,cancelable:!0,view:window,button:0}}))}})}}}})')
    print('7. 确认导出...', flush=True)
    
    for j in range(40):
        time.sleep(3)
        if 'assets' in P.url:
            print(f'✅ 导出完成!', flush=True)
            break
        if j % 5 == 0:
            print(f'   导出中... ({{j*3}}s)', flush=True)
    else:
        print(f'⏰ 超时 URL: {{P.url[:60]}}', flush=True)

# 验证
P.run_js('window.onbeforeunload=null;window.location.href=\"https://music.douyin.com/studio/assets\"')
time.sleep(5)
ok = P.run_js('return document.body.textContent.includes(\"{song}\")')
print(f'结果: {{\"✅\" if ok else \"❌\"}} {{song}}', flush=True)
"""],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    print(result.stdout)
    if result.stderr:
        # 过滤无害警告
        for line in result.stderr.split('\n'):
            if 'NotOpenSSL' not in line and 'urllib3' not in line and 'warnings.warn' not in line and 'Saving session' not in line:
                print(f"  stderr: {line}")

print("\n全部完成！")
