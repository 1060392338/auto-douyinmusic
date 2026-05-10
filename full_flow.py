#!/usr/bin/env python3
"""
全流程：AI作曲 → 导出 → 发布
基于 export_v5.py 验证过的选择器和事件链
"""
import sys, time, os, signal, json

from DrissionPage import ChromiumPage

# ── 配置 ──
SONG_LYRICS = sys.argv[1] if len(sys.argv) > 1 else ""
SONG_STYLE = sys.argv[2] if len(sys.argv) > 2 else ""
# 默认值
if not SONG_LYRICS:
    SONG_LYRICS = """[Verse]
窗外的雨 敲打着昨天
你的影子 还留在房间
翻开那本 泛黄的相片
回忆停在 那个夏天

[Chorus]
风轻轻吹过 我们走过的路
带着年少时 没说完的倾诉
如果时光 能够倒流
我会紧紧握住你的手

[Verse 2]
街角的灯 照亮了孤单
你的笑容 在脑海盘旋
也许有些 话不需要说完
就让思念 随风飘散

[Bridge]
如果明天 还能再相见
我会把故事 都讲给你听
那些从前 最美的画面
永远留在 心间

[Final Chorus]
风轻轻吹过 我们走过的路
带着年少时 没说完的倾诉
如果时光 能够倒流
我会紧紧 握住你的手
直到最后"""

if not SONG_STYLE:
    SONG_STYLE = "温柔的民谣风格，使用木吉他为主伴奏，节奏舒缓，情感细腻，适合静静聆听"

# ── 信号处理 ──
def _cleanup(signum, frame):
    print("\n⚠️ 收到信号，清理 Chrome...", flush=True)
    os.system("lsof -ti :9223 | xargs kill -9 2>/dev/null")
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(1)

# ── 工具函数 ──
def handle_alerts():
    for _ in range(5):
        try:
            P.handle_alert(accept=True)
            time.sleep(0.3)
        except:
            break

def js(code, d=None):
    for _ in range(3):
        try:
            return P.run_js(code)
        except:
            handle_alerts()
            time.sleep(1)
    return d

def safe_click(el_selector_js):
    """全事件链点击：先滚到可见，再pointer+click"""
    js(f"""
    (function() {{
        function doClick(el) {{
            if(!el) return;
            el.scrollIntoView({{behavior:"instant", block:"center"}});
            el.focus();
            ["pointerdown","pointerup","mousedown","mouseup","click"].forEach(function(t) {{
                el.dispatchEvent(new PointerEvent(t, {{bubbles:true, cancelable:true}}));
            }});
        }}
        {el_selector_js}
    }})();
    """)
    time.sleep(1)

# 清除弹窗
handle_alerts()
time.sleep(1)

# ══════════════════════════════════════════════════════
# PHASE 1: AI作曲
# ══════════════════════════════════════════════════════
print("\n🎵 [Phase 1] AI作曲", flush=True)

# 1. 导航到作曲页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create';")
time.sleep(6)
print(f"  URL: {P.url[:60]}", flush=True)

# 2. 确认高级模式
body = P.ele("tag:body").text
if "高级模式" in body:
    print("  切换高级模式...", flush=True)
    safe_click("""
    var btns = document.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='高级模式'){doClick(btns[i]);break;}}
    """)
    time.sleep(2)
    print("  已切换高级模式✅", flush=True)

# 3. 填歌词（第一个textarea - 灵感/歌词输入）
print("  填写歌词...", flush=True)
ta = P.eles("tag:textarea")
print(f"  找到 textarea: {len(ta)}个", flush=True)
if len(ta) >= 1:
    # 用JS native setter写歌词
    lyrics_escaped = SONG_LYRICS.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    js(f"""
    (function() {{
        var tas = document.querySelectorAll('textarea');
        if(tas.length>0){{
            var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
            s.call(tas[0],'{lyrics_escaped}');
            tas[0].dispatchEvent(new Event('input',{{bubbles:true}}));
        }}
    }})();
    """)
    time.sleep(1)
    print("  歌词已填写✅", flush=True)

# 4. 填风格描述（第二个textarea）
if len(ta) >= 2:
    print("  填写风格描述...", flush=True)
    style_escaped = SONG_STYLE.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    js(f"""
    (function() {{
        var tas = document.querySelectorAll('textarea');
        if(tas.length>1){{
            var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
            s.call(tas[1],'{style_escaped}');
            tas[1].dispatchEvent(new Event('input',{{bubbles:true}}));
        }}
    }})();
    """)
    time.sleep(1)
    print("  风格已填写✅", flush=True)

# 5. 点生成歌曲
print("  点击生成歌曲...", flush=True)
safe_click("""
var btns = document.querySelectorAll('button');
for(var i=0;i<btns.length;i++){
    if(btns[i].textContent.trim()==='生成歌曲' && !btns[i].disabled){
        doClick(btns[i]);break;
    }
}
""")

# 6. 等待生成完成（显示"生成中 X/4"，然后消失）
print("  等待AI生成歌曲...", flush=True)
gen_completed = False
for i in range(80):  # 最长4分钟
    time.sleep(3)
    try:
        body = P.ele("tag:body").text
    except:
        print(f"   页面断连，尝试恢复... ({i*3}s)", flush=True)
        try:
            P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
            time.sleep(2)
            body = P.ele("tag:body").text
        except:
            print("   恢复失败，但继续...", flush=True)
            body = ""
    if "生成中" in body:
        if i % 5 == 0:
            print(f"   生成中... ({i*3}s)", flush=True)
    else:
        gen_completed = True
        print(f"   生成完成! ({i*3}s)", flush=True)
        break

if not gen_completed:
    print("   ⏰ 生成超时，继续尝试后续步骤...", flush=True)

time.sleep(5)

# 7. 读取新生成的歌曲名称
body = P.ele("tag:body").text
# 找歌名：在素材列表中找第一个未导出的歌名
known = ["缓歌寄意","杂乱思绪","无章","无序歌","星落肩头","空白页",
         "纸鸢远","夏蝉语","迷音","巷尾琴音","木吉他叙旧","吉他与诗","欢歌寄意"]
all_songs_in_page = []
for line in body.split("\n"):
    line = line.strip()
    if line and line not in known and "Sway" not in line and ":" not in line and len(line) >= 2 and len(line) <= 8:
        all_songs_in_page.append(line)
        if line not in known:
            new_song = line
            break
else:
    # fallback: 取第一个不认识的2-5字的名字
    parts = body.split("Sway v5.5")
    for p in parts:
        lines = p.strip().split("\n")
        for l in lines:
            l = l.strip()
            if l and l not in known and len(l) >= 2 and len(l) <= 6:
                new_song = l
                break
        if 'new_song' in dir():
            break

try:
    new_song
except NameError:
    new_song = "新歌"

print(f"\n🎵 新歌名: {new_song}", flush=True)
P.get_screenshot(path="/tmp/phase1_done.png")

# ══════════════════════════════════════════════════════
# PHASE 2: 导出到资产
# ══════════════════════════════════════════════════════
print(f"\n📤 [Phase 2] 导出 {new_song}", flush=True)

# 复用 export_v5.py 逻辑
P.run_js(f'''
(function() {{var items=document.querySelectorAll('[class*="titleRow"]');for(var i=0;i<items.length;i++){{if(items[i].textContent.includes("{new_song}")){{["pointerdown","pointerup","mousedown","mouseup","click"].forEach(function(t){{items[i].dispatchEvent(new PointerEvent(t,{{bubbles:true,cancelable:true}}))}});}}}}}})()
''')
time.sleep(3)
print("  素材✅", flush=True)

# AI编辑
js("""document.querySelectorAll('button[class*="aiEditButton"]').forEach(b=>{b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0,view:window,button:0}))})""")
time.sleep(3)

# 去AI编辑器
print("  去AI编辑器...", flush=True)
js("""document.querySelector('button[class*="primaryBtn"]')?.scrollIntoView({behavior:"instant",block:"center"})""")
time.sleep(1)
for _ in range(3):
    js("""document.querySelectorAll('button[class*="primaryBtn"]').forEach(b=>{b.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new PointerEvent(t,{bubbles:!0,cancelable:!0}))})})""")
    time.sleep(6)
    if "playground" in P.url:
        break
if "playground" in P.url:
    print(f"  编辑器✅", flush=True)
else:
    print(f"  ⚠️ 导航失败 URL: {P.url[:60]}", flush=True)

# 等待编辑器加载
js("window.onbeforeunload=null;window.alert=function(){}")
time.sleep(8)

# 导出
print("  点击导出...", flush=True)
js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出'){['mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new MouseEvent(t,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
time.sleep(5)

# 检查弹窗
body = P.ele("tag:body").text
has_dialog = "并轨导出" in body
if not has_dialog:
    print("  重试导出...", flush=True)
    js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出')b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0}))})""")
    time.sleep(5)
    body = P.ele("tag:body").text
    has_dialog = "并轨导出" in body

if has_dialog:
    print("  弹窗✅ 改歌名...", flush=True)
    js(f"""document.querySelectorAll('input').forEach(inp=>{{if(inp.value.includes('新项目')){{inp.disabled=false;inp.removeAttribute('disabled');Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(inp,'{new_song}');inp.dispatchEvent(new Event('input',{{bubbles:!0}}));inp.dispatchEvent(new Event('change',{{bubbles:!0}}))}}}})""")
    time.sleep(1)
    
    print("  确认导出...", flush=True)
    js("""document.querySelectorAll('button.semi-button').forEach(b=>{const t=b.textContent.trim();if(t==='导出'||t==='并轨导出'||t==='确认导出'){['mousedown','mouseup','click'].forEach(tt=>{b.dispatchEvent(new MouseEvent(tt,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
    
    print("  等待导出...", flush=True)
    for i in range(30):
        time.sleep(3)
        if "assets" in P.url:
            print(f"  导出完成! 跳转到资产页", flush=True)
            break
        if i % 5 == 0:
            print(f"   导出中... ({i*3}s)", flush=True)
else:
    print("  ❌ 导出弹窗未出现", flush=True)

# ══════════════════════════════════════════════════════
# PHASE 3: 验证
# ══════════════════════════════════════════════════════
print(f"\n🔍 [Phase 3] 验证", flush=True)
time.sleep(3)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(5)

body = P.ele("tag:body").text
in_assets = new_song in body
print(f"  资产页有 {new_song}: {'✅' if in_assets else '❌'}", flush=True)
print(f"  有发行全曲: {'✅' if '发行全曲' in body else '❌'}", flush=True)

if not in_assets:
    P.get_screenshot(path="/tmp/publish_fail.png")
    print("  截图在 /tmp/publish_fail.png", flush=True)

print(f"\n{'='*50}", flush=True)
print(f"全流程结束", flush=True)
print(f"歌曲: {new_song}", flush=True)
print(f"导出: {'✅' if in_assets else '❌'}", flush=True)
print(f"{'='*50}", flush=True)
