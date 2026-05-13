#!/usr/bin/env python3
"""
全流程：AI作曲（短提示→快速生成）→ 导出 → 发布
"""
import sys, time, os, signal

from DrissionPage import ChromiumPage

# 超短歌词+风格，加速AI生成
SONG_LYRICS = """[主歌]
风吹过的夏天
[副歌]
回忆那么甜"""

SONG_STYLE = "温柔的民谣，慢节奏"

def _cleanup(signum, frame):
    os.system("lsof -ti :9223 | xargs kill -9 2>/dev/null")
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(2)

def handle_alerts():
    for _ in range(5):
        try: P.handle_alert(accept=True); time.sleep(0.3)
        except: break

def js(code):
    for _ in range(3):
        try: return P.run_js(code)
        except:
            handle_alerts()
            time.sleep(1)
    return None

handle_alerts()
time.sleep(1)

# ══════════════════════════════════════════════════════
# PHASE 1: AI作曲
# ══════════════════════════════════════════════════════
print("\n🎵 [Phase 1] AI作曲", flush=True)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create';")
time.sleep(6)
print(f"  URL: {P.url[:60]}", flush=True)

# 高级模式
body = P.ele("tag:body").text
if "高级模式" in body:
    P.run_js("""document.querySelectorAll('button').forEach(b=>{if(b.textContent.trim()==='高级模式'){b.dispatchEvent(new PointerEvent('click',{bubbles:!0,cancelable:!0}))}})""")
    time.sleep(2)
    print("  高级模式✅", flush=True)

# 填歌词 (第一个textarea)
lyrics_esc = SONG_LYRICS.replace("\\","\\\\").replace("'","\\'").replace("\n","\\n")
js(f"""var tas=document.querySelectorAll('textarea');if(tas.length>0){{var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;s.call(tas[0],'{lyrics_esc}');tas[0].dispatchEvent(new Event('input',{{bubbles:!0}}))}}""")
print("  歌词✅", flush=True)

# 填风格 (第二个textarea)
style_esc = SONG_STYLE.replace("'","\\'")
js(f"""var tas=document.querySelectorAll('textarea');if(tas.length>1){{var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;s.call(tas[1],'{style_esc}');tas[1].dispatchEvent(new Event('input',{{bubbles:!0}}))}}""")
print("  风格✅", flush=True)

# 生成
P.run_js("""document.querySelectorAll('button').forEach(b=>{if(b.textContent.trim()==='生成歌曲'&&!b.disabled){b.dispatchEvent(new PointerEvent('click',{bubbles:!0,cancelable:!0}))}})""")
print("  等待生成...", flush=True)

# 等生成 - 轮询"生成中"消失
gen_ok = False
start = time.time()
while time.time() - start < 300:  # 最长5分
    time.sleep(3)
    try:
        body = P.ele("tag:body").text
        if "生成中" not in body and time.time() - start > 20:
            gen_ok = True
            break
    except:
        try:
            P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
            time.sleep(3)
        except:
            pass
    if int(time.time() - start) % 30 == 0:
        print(f"   生成中... ({int(time.time()-start)}s)", flush=True)

elapsed = int(time.time() - start)
print(f"   {'生成完成' if gen_ok else '超时'} ({elapsed}s)", flush=True)

if gen_ok:
    time.sleep(3)
    # 从页面提取新歌名
    body = P.ele("tag:body").text
    known = ["缓歌寄意","杂乱思绪","无章","无序歌","星落肩头","空白页",
             "纸鸢远","夏蝉语","迷音","巷尾琴音","木吉他叙旧","吉他与诗","欢歌寄意",
             "首页","素材","我的资产","自由创作","AI 作词","AI 作曲","AI 编辑器","知识库"]
    new_song = None
    # 找素材列表中的歌名（在"Sway v5.5"之前的2-5字名字）
    words = body.replace("Sway v5.5","|").split("|")
    for chunk in words:
        for line in chunk.strip().split("\n"):
            line = line.strip()
            if line not in known and 2 <= len(line) <= 6 and not any(c.isdigit() for c in line):
                new_song = line
                break
        if new_song:
            break
    if not new_song:
        new_song = "新歌_" + str(int(time.time()) % 10000)
    print(f"  新歌: {new_song}", flush=True)
else:
    # 生成超时，用素材列表第一个未导出的
    new_song = "新歌_fallback"
    print("  用fallback歌名", flush=True)

P.get_screenshot(path="/tmp/full_phase1.png")

# ══════════════════════════════════════════════════════
# PHASE 2: 导出
# ══════════════════════════════════════════════════════
print(f"\n📤 [Phase 2] 导出", flush=True)

if not gen_ok:
    print("  生成失败，跳过导出", flush=True)
else:
    P.run_js(f"""(function(){{var items=document.querySelectorAll('[class*="titleRow"]');for(var i=0;i<items.length;i++){{if(items[i].textContent.includes("{new_song}")){{["pointerdown","pointerup","mousedown","mouseup","click"].forEach(function(t){{items[i].dispatchEvent(new PointerEvent(t,{{bubbles:!0,cancelable:!0}}))}})}}}}}})()""")
    time.sleep(3)
    print("  素材✅", flush=True)

    js("""document.querySelectorAll('button[class*="aiEditButton"]').forEach(b=>{b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0,view:window,button:0}))})""")
    time.sleep(3)

    js("""document.querySelector('button[class*="primaryBtn"]')?.scrollIntoView({behavior:"instant",block:"center"})""")
    time.sleep(1)
    nav_ok = False
    for _ in range(3):
        js("""document.querySelectorAll('button[class*="primaryBtn"]').forEach(b=>{b.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new PointerEvent(t,{bubbles:!0,cancelable:!0}))})})""")
        time.sleep(6)
        if "playground" in P.url:
            nav_ok = True
            break
    if nav_ok:
        print("  编辑器✅", flush=True)
    else:
        print(f"  导航失败({P.url[:50]})", flush=True)

    if nav_ok:
        time.sleep(10)
        # 导出
        js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出'){['mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new MouseEvent(t,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
        time.sleep(5)
        body = P.ele("tag:body").text
        has_dlg = "并轨导出" in body
        if not has_dlg:
            js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出')b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0}))})""")
            time.sleep(5)
            body = P.ele("tag:body").text
            has_dlg = "并轨导出" in body

        if has_dlg:
            print("  弹窗✅", flush=True)
            js(f"""document.querySelectorAll('input').forEach(inp=>{{if(inp.value.includes('新项目')){{inp.disabled=false;inp.removeAttribute('disabled');Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(inp,'{new_song}');inp.dispatchEvent(new Event('input',{{bubbles:!0}}));inp.dispatchEvent(new Event('change',{{bubbles:!0}}))}}}})""")
            time.sleep(1)
            js("""document.querySelectorAll('button.semi-button').forEach(b=>{const t=b.textContent.trim();if(t==='导出'||t==='并轨导出'){['mousedown','mouseup','click'].forEach(tt=>{b.dispatchEvent(new MouseEvent(tt,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
            
            print("  等待导出...", flush=True)
            for i in range(30):
                time.sleep(3)
                if "assets" in P.url:
                    break
                if i % 5 == 0:
                    print(f"   导出中... ({i*3}s)", flush=True)
            print(f"  资产页: {'✅' if 'assets' in P.url else '❌'}", flush=True)
        else:
            print("  ❌ 弹窗未出现", flush=True)

# ══════════════════════════════════════════════════════
# PHASE 3: 验证
# ══════════════════════════════════════════════════════
print(f"\n🔍 [Phase 3] 验证", flush=True)
time.sleep(3)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)
body = P.ele("tag:body").text
in_assets = new_song in body if gen_ok else False
print(f"  {new_song}: {'✅' if in_assets else '❌'}", flush=True)
print(f"  发行全曲: {'✅' if '发行全曲' in body else '❌'}", flush=True)

print(f"\n{'='*50}", flush=True)
print(f"全流程结束", flush=True)
print(f"歌曲: {new_song}", flush=True)
print(f"导出: {'✅' if in_assets else '❌'}", flush=True)
print(f"{'='*50}", flush=True)
