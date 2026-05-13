"""CDP 作曲：灵感生成一首歌"""
import sys, time, json
sys.path.insert(0, '.')
from export_cdp import CDPClient

cdp = CDPClient(auto_navigate=True)
print("✅ CDP 已连接", flush=True)

prompt = "深夜的爵士酒吧，萨克斯慵懒低吟，钢琴轻柔点缀，微醺的氛围"

# Step 1: 输入灵感
print(f"📝 输入灵感: {prompt[:40]}...", flush=True)
cdp.eval(f'''
(() => {{
    const el = document.querySelector('textarea[placeholder*="灵感"]');
    const ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
    ns.call(el, {json.dumps(prompt)});
    el.dispatchEvent(new Event("input", {{bubbles: true}}));
    el.dispatchEvent(new Event("change", {{bubbles: true}}));
    return "typed " + el.value.length;
}})()
''')
time.sleep(2)

# Step 2: 检查生成按钮
btn_state = cdp.eval(
    'document.querySelector("[data-testid=create-song-button]").getAttribute("aria-disabled")'
)
disabled = btn_state.get("value", "true")
print(f"   按钮状态: disabled={disabled}", flush=True)

if disabled == "true":
    print("❌ 生成按钮未激活", flush=True)
    cdp.close()
    sys.exit(1)

# Step 3: 点击生成
print("🎹 点击生成...", flush=True)
cdp.eval('document.querySelector("[data-testid=create-song-button]").click(); "clicked"')

# Step 4: 等待生成完成
print("⏳ 等待生成...", flush=True)
for i in range(24):
    time.sleep(5)
    try:
        status = cdp.eval('''
        (() => {
            const el = [...document.querySelectorAll("[role=button]")]
                .find(b => b.textContent.includes("AI 作曲"));
            const parent = el?.closest("div")?.parentElement;
            const text = parent?.textContent || "";
            return text.includes("生成中") ? "生成中" : "done";
        })()
        ''')
        s = status.get("value", "?")
        if s == "done":
            print(f"   ✅ 生成完成 ({i*5+5}s)", flush=True)
            break
        if i % 3 == 0:
            print(f"   ... {s} ({i*5+5}s)", flush=True)
    except Exception as e:
        if i % 3 == 0:
            print(f"   ... 异常: {e} ({i*5+5}s)", flush=True)
else:
    print("⚠️ 生成超时", flush=True)

# Step 5: 获取新歌
time.sleep(3)
songs = cdp.eval('''
JSON.stringify(
    [...document.querySelectorAll('[class*="libraryItem"] p')]
        .map(p => p.textContent.trim())
        .filter(n => n.length > 1 && n.length < 20)
        .slice(-10)
)
''')
raw = songs.get("value", "[]")
new_songs = json.loads(raw) if isinstance(raw, str) else (raw or [])
print(f"\n📊 素材列表最新 10 首:", flush=True)
for s in new_songs:
    print(f"   - {s}", flush=True)

cdp.close()
