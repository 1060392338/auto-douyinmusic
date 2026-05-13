#!/usr/bin/env python3
"""
发布 v8 - LLM驱动发布流程
LLM分析页面状态，决定点击/填写什么
"""
import sys, time, json, requests, websocket, os, re

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
bws_url = 'http://localhost:9223'

# ── LLM 客户端 ──
from openai import OpenAI
# 从.env加载API Key
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    for line in open(env_path):
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ.setdefault(k, v)
LLM = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY', ''),
    base_url=os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
)
LLM_MODEL = 'deepseek-v4-pro'

def llm(messages, json_mode=False):
    kwargs = dict(model=LLM_MODEL, messages=messages, temperature=0.1)
    if json_mode:
        kwargs['response_format'] = {'type': 'json_object'}
    r = LLM.chat.completions.create(**kwargs)
    return r.choices[0].message.content

def get_pub_tid():
    ver = requests.get(f'{bws_url}/json/version', timeout=5).json()
    ws = websocket.create_connection(ver['webSocketDebuggerUrl'], timeout=5)
    ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    targets = json.loads(ws.recv()).get('result',{}).get('targetInfos',[])
    ws.close()
    for t in targets:
        if 'complete-publish' in t.get('url','') and t['type'] == 'page':
            return t['targetId']
    return None

def eval_t(tid, js):
    w = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
    r = json.loads(w.recv())
    w.close()
    val = r.get('result',{}).get('result',{}).get('value')
    return val if val is not None else ''

# ── 第一步：从资产页点发行全曲 ──
print(f"=== LLM发布 {song} ===\n", flush=True)

# 清理旧发布页
bws = requests.get(f'{bws_url}/json/version', timeout=5).json()['webSocketDebuggerUrl']
ws = websocket.create_connection(bws, timeout=5)
ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
targets = json.loads(ws.recv()).get('result',{}).get('targetInfos',[])
for t in targets:
    if 'complete-publish' in t.get('url',''):
        ws.send(json.dumps({'id':2,'method':'Target.closeTarget','params':{'targetId':t['targetId']}}))
        json.loads(ws.recv())
ws.close()

# 找资产页
assets_tid = None
for t in targets:
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']
        break

if not assets_tid:
    print("❌ 未找到资产页")
    sys.exit(1)

# 点发行全曲
eval_t(assets_tid, f'''
(function() {{
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for(var i=0; i<cards.length; i++) {{
        if(cards[i].textContent.includes("{song}")) {{
            var all = cards[i].querySelectorAll('*');
            for(var j=0; j<all.length; j++) {{
                if(all[j].textContent && all[j].textContent.trim() === "发行全曲") {{
                    all[j].scrollIntoView({{behavior:"instant", block:"center"}});
                    ["pointerdown","pointerup","click"].forEach(function(t) {{
                        all[j].dispatchEvent(new PointerEvent(t, {{bubbles:true, cancelable:true}}));
                    }});
                    return;
                }}
            }}
        }}
    }}
}})();
''')
time.sleep(5)

# 找发布页
pub_tid = get_pub_tid()
if not pub_tid:
    print("❌ 发布页未生成")
    sys.exit(1)
print(f"✅ 发布页 ID: {pub_tid}", flush=True)
eval_t(pub_tid, "window.onbeforeunload=null")
time.sleep(2)

# ── LLM 循环：分析页面 → 执行操作 ──
SYSTEM_PROMPT = """你是抖音音乐开放平台的自动化助手。你的任务是分析发布表单页面，决定下一步操作来推进表单到最终提交。

当前任务：发布歌曲「%s」

页面是抖音音乐发布表单（/console/complete-publish），包含三个步骤：
1. 上传作品 - 歌曲信息、音频文件、封面、词曲作者、歌词、专辑信息等
2. 授权作品 - 授权比例
3. 签署协议 - letsign电子签

回应必须是JSON格式：
{"action": "click|fill|scroll|wait|done|error",
 "target_text": "要点击的按钮文字或要填写的字段名",
 "value": "要填写的值（如果是fill动作）",
 "reason": "为什么要做这个操作"}

规则：
- 每次只做一个操作
- 先确保歌曲信息填写完整（标题、音乐类型、封面）
- 需要填写表演者/词作者/曲作者时，先文本搜索对应combobox，输入歌名后回车
- 如果已填完step1但无法推进，检查是否有错误提示
- 到授权步骤后检查授权比例
- 最后进入签署""" % song

max_steps = 20
for step in range(max_steps):
    # 获取页面文本内容
    page_text = eval_t(pub_tid, '''
    (function() {
        var sb = document.querySelector('[class*=simplebar-content]');
        if(sb) return sb.textContent.trim().substring(0, 3000);
        return document.body.textContent.substring(0, 500);
    })();
    ''')

    # 获取可见按钮
    btns = eval_t(pub_tid, '''
    JSON.stringify(Array.from(document.querySelectorAll("button")).filter(b=>b.offsetWidth>0).slice(0,20).map(b=>b.textContent.trim()).filter(t=>t))
    ''')

    # 获取步骤状态
    step_status = eval_t(pub_tid, '''
    (function() {
        var items = document.querySelectorAll('[class*=douyin-music-steps-item]');
        for(var i=0; i<items.length; i++) {
            if((items[i].className||'').includes('active')) return 'active: ' + items[i].textContent.trim();
        }
        return 'no-active-step';
    })();
    ''')

    context = f"""当前步骤状态: {step_status}
可见按钮: {btns}
页面内容(截取): {page_text[:1500]}
已执行步数: {step}"""

    # LLM决定
    resp = llm([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': context}
    ], json_mode=True)
    
    try:
        decision = json.loads(resp)
    except:
        print(f"  LLM响应解析失败: {resp[:100]}", flush=True)
        continue

    action = decision.get('action', '')
    target = decision.get('target_text', '')
    value = decision.get('value', '')
    reason = decision.get('reason', '')
    print(f"  [{step+1}] {action} '{target}' — {reason}", flush=True)

    if action == 'done':
        print("✅ LLM认为发布完成！", flush=True)
        break
    elif action == 'error':
        print(f"❌ LLM报告错误: {reason}", flush=True)
        break
    elif action == 'wait':
        time.sleep(3)
    elif action == 'scroll':
        eval_t(pub_tid, '''
        (function() {
            var sb = document.querySelector('[class*=simplebar-content-wrapper]');
            if(sb) sb.scrollTo(0, sb.scrollHeight);
            window.scrollTo(0, document.body.scrollHeight);
        })();
        ''')
        time.sleep(2)
    elif action == 'click':
        # 找到含目标文本的按钮并点击
        eval_t(pub_tid, f'''
        (function() {{
            var all = document.querySelectorAll('*');
            for(var i=all.length-1; i>=0; i--) {{
                if(all[i].textContent && all[i].textContent.trim() === '{target}') {{
                    all[i].scrollIntoView({{behavior:"instant", block:"center"}});
                    ["pointerdown","pointerup","mousedown","mouseup","click"].forEach(function(t) {{
                        all[i].dispatchEvent(new PointerEvent(t, {{bubbles:true, cancelable:true}}));
                    }});
                    return;
                }}
            }}
        }})();
        ''')
        time.sleep(3)
    elif action == 'fill':
        # 找输入框填值
        eval_t(pub_tid, f'''
        (function() {{
            var inputs = document.querySelectorAll('input, textarea');
            for(var i=0; i<inputs.length; i++) {{
                var ph = (inputs[i].placeholder || '').toLowerCase();
                var lbl = '';
                var parent = inputs[i].closest('[class*=field]') || inputs[i].parentElement;
                if(parent) lbl = (parent.textContent || '').toLowerCase();
                var target = '{target}'.toLowerCase();
                if(ph.includes(target) || lbl.includes(target)) {{
                    inputs[i].focus();
                    var s = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set || Object.getOwnPropertyDescriptor(
                        window.HTMLTextAreaElement.prototype, 'value'
                    ).set;
                    if(s) {{
                        s.call(inputs[i], '{value}');
                        inputs[i].dispatchEvent(new Event('input', {{bubbles:true}}));
                        inputs[i].dispatchEvent(new Event('change', {{bubbles:true}}));
                    }}
                    return;
                }}
            }}
        }})();
        ''')
        time.sleep(2)
    else:
        print(f"  未知动作: {action}", flush=True)

print(f"\n=== LLM发布 {song} 完成 ===", flush=True)
