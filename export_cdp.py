"""
export_cdp.py — 基于 CDP WebSocket 直接导出抖音音乐歌曲到资产页
替代 opencli/DrissionPage，直连 Chrome DevTools Protocol

用法:
    python export_cdp.py                    # 导出素材列表全部歌曲
    python export_cdp.py "星夜酒廊风"        # 导出指定歌曲
"""
import json, time, sys, urllib.request, signal, os
import websocket

CDP_PORT = 9223
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"

# ── 信号处理 ────────────────────────────────────────
def _cleanup(signum, frame):
    print("\n⚠️ 收到暂停信号，清理...", flush=True)
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

# ── CDP 客户端 ──────────────────────────────────────

class CDPError(Exception):
    """CDP 通用错误"""
    pass

class CDPTimeoutError(CDPError):
    """CDP 超时"""
    pass

class CDPConnectionError(CDPError):
    """CDP 连接断开"""
    pass


class CDPClient:
    """Chrome DevTools Protocol 客户端（WebSocket 直连）

    特性：
    - 自动重连（连接断开时透明恢复）
    - wait_selector / wait_text 替代盲等 sleep
    - 连接健康检查
    """

    def __init__(self, port=CDP_PORT, auto_navigate=True):
        self.port = port
        self.ws = None
        self.msg_id = 0
        self._page_id = None
        self._connect()
        if auto_navigate:
            self.navigate("https://music.douyin.com/studio/create")

    def _connect(self):
        """建立 WebSocket 连接并激活 CDP domains"""
        for attempt in range(3):
            try:
                pages = json.loads(urllib.request.urlopen(
                    urllib.request.Request(f"http://127.0.0.1:{self.port}/json"),
                    timeout=5
                ).read())
                page = next((p for p in pages if p['type'] == 'page'), pages[0])
                self._page_id = page['id']
                ws_url = page['webSocketDebuggerUrl']
                self.ws = websocket.create_connection(ws_url, timeout=15)
                self._enable_domains()
                return
            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    print(f"  ⚠️ CDP 连接失败 (尝试 {attempt+1}/3): {e}，{wait}s 后重试...", flush=True)
                    time.sleep(wait)
                else:
                    raise CDPConnectionError(f"CDP 连接失败（3次）: {e}")

    def _enable_domains(self):
        """激活 Runtime 和 Page domain"""
        self._send("Runtime.enable")
        self._recv(self.msg_id)
        self._send("Page.enable")
        self._recv(self.msg_id)

    def health_check(self) -> bool:
        """检查连接是否存活"""
        try:
            r = self._call_inner("Runtime.evaluate", {
                "expression": "1", "returnByValue": True
            })
            return r.get("result", {}).get("result", {}).get("value") == 1
        except (CDPError, websocket.WebSocketException):
            return False

    def _send(self, method, params=None):
        self.msg_id += 1
        req = {"id": self.msg_id, "method": method}
        if params:
            req["params"] = params
        self.ws.send(json.dumps(req))

    def _recv(self, target_id, timeout=8):
        """读取直到匹配 target_id 的响应，超时或断开时抛出异常"""
        self.ws.settimeout(timeout)
        for _ in range(200):
            try:
                resp = json.loads(self.ws.recv())
                if resp.get("id") == target_id:
                    return resp
            except websocket.WebSocketTimeoutException:
                raise CDPTimeoutError(f"CDP 超时: 等待 msg#{target_id}")
            except websocket.WebSocketConnectionClosedException:
                raise CDPConnectionError("CDP WebSocket 连接已断开")
            except json.JSONDecodeError:
                continue  # 跳过非 JSON 响应
        raise CDPTimeoutError(f"CDP 超时: 200 条消息未匹配 msg#{target_id}")

    def _call_inner(self, method, params=None):
        """核心调用（不含重连逻辑）"""
        mid = self.msg_id + 1
        self._send(method, params)
        return self._recv(mid)

    def call(self, method, params=None):
        """同步调用 CDP 方法，连接断开时自动重连一次"""
        try:
            if not self.health_check():
                self._reconnect()
            return self._call_inner(method, params)
        except CDPConnectionError:
            self._reconnect()
            return self._call_inner(method, params)

    def _reconnect(self):
        """重新建立 WebSocket 连接"""
        try:
            self.ws.close()
        except Exception:
            pass
        print("  🔄 CDP 重连...", flush=True)
        self._connect()

    def eval(self, js, timeout=10):
        """执行 JS 并返回结果值"""
        r = self.call("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
            "timeout": timeout * 1000
        })
        result = r.get("result", {})
        if "exceptionDetails" in result:
            exc = result["exceptionDetails"]
            return {"error": f"{exc.get('text', '')} at line {exc.get('lineNumber', '?')}"}
        return {"value": result.get("result", {}).get("value")}

    # ── 导航 ────────────────────────────────────────

    def navigate(self, url, wait_load=True):
        """导航到 URL，可选择等待 Page.loadEventFired

        Args:
            url: 目标 URL
            wait_load: 是否等待 loadEventFired 事件（默认 True）
        """
        self.eval("window.onbeforeunload=null")
        r = self.call("Page.navigate", {"url": url})
        err = r.get("result", {}).get("errorText", "")
        if err:
            print(f"  ⚠️ 导航警告: {err}", flush=True)

        if wait_load:
            # 等待 Page.loadEventFired
            for _ in range(100):
                try:
                    self.ws.settimeout(3)
                    resp = json.loads(self.ws.recv())
                    if resp.get("method") == "Page.loadEventFired":
                        break
                except websocket.WebSocketTimeoutException:
                    break  # 已超时，不再等
                except Exception:
                    pass
            time.sleep(2)  # 额外给 SPA 渲染一点时间

        self._handle_dialog()

    def get_url(self):
        r = self.eval("window.location.href")
        return r.get("value", "")

    # ── 等待 ────────────────────────────────────────

    def wait_selector(self, css, timeout=15):
        """等待 CSS 选择器匹配的元素出现"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = self.eval(f"document.querySelector({json.dumps(css)}) !== null")
            if r.get("value"):
                return True
            time.sleep(0.5)
        return False

    def wait_text(self, text, timeout=15):
        """等待页面文本出现"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = self.eval(f"document.body.textContent.includes({json.dumps(text)})")
            if r.get("value"):
                return True
            time.sleep(0.5)
        return False

    # ── 弹窗 ────────────────────────────────────────

    def _handle_dialog(self):
        """处理 alert/confirm 弹窗"""
        for _ in range(5):
            try:
                self.call("Page.handleJavaScriptDialog", {
                    "accept": True,
                    "promptText": ""
                })
                time.sleep(0.3)
            except CDPError:
                break
            except Exception:
                break

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


# ── 导出逻辑 ────────────────────────────────────────
class DouyinExportCDP:
    def __init__(self):
        self.cdp = CDPClient()

    def get_material_list(self):
        """获取素材列表中的歌曲"""
        # 确保在 create 页面
        url = self.cdp.get_url()
        if 'create' not in url:
            self.cdp.navigate("https://music.douyin.com/studio/create")
        
        songs = self.cdp.eval('''
        (function(){
            var result = [];
            var items = document.querySelectorAll('[class*="libraryItem"]');
            for (var i=0; i<items.length; i++) {
                var p = items[i].querySelector('p');
                var span = items[i].querySelector('span');
                var name = p ? p.textContent.trim() : '';
                var dur = span ? span.textContent.trim() : '';
                if (name && name.length > 1 && name.length < 20) {
                    result.push({name: name, duration: dur});
                }
            }
            return JSON.stringify(result);
        })()
        ''')
        raw = songs.get("value", "[]")
        if isinstance(raw, str):
            return json.loads(raw)
        return raw or []

    def get_asset_list(self):
        """获取资产页已有歌曲"""
        self.cdp.navigate("https://music.douyin.com/studio/assets")
        items = self.cdp.eval('''
        (function(){
            var result = [];
            var els = document.querySelectorAll('[class*="assetItem"]');
            for (var i=0; i<els.length; i++) {
                var title = els[i].getAttribute('data-title') || els[i].querySelector('p');
                if (title && title.textContent) title = title.textContent;
                result.push(String(title || '').trim());
            }
            return JSON.stringify(result);
        })()
        ''')
        raw = items.get("value", "[]")
        if isinstance(raw, str):
            return json.loads(raw)
        return raw or []

    def export_one(self, song_name):
        """导出单首歌曲（7步流程）"""
        print(f"\n{'='*50}")
        print(f"📦 导出: {song_name}")
        print(f"{'='*50}")

        # Step 1: 导航到作曲页 + 等素材列表加载 + 点素材
        print("Step 1: 作曲页 → 等素材列表 → 点素材...")
        self.cdp.navigate("https://music.douyin.com/studio/create")
        if not self.cdp.wait_selector('[class*="libraryItem"]', timeout=10):
            print("   ⚠️ 素材列表未加载，继续尝试...")
            time.sleep(3)

        clicked = self.cdp.eval(f'''
        (function(){{
            var items = document.querySelectorAll('[class*="libraryItem"]');
            for (var i=0; i<items.length; i++) {{
                var p = items[i].querySelector('p');
                if (p && p.textContent.trim() === {json.dumps(song_name)}) {{
                    items[i].dispatchEvent(new PointerEvent('click', {{bubbles: true, cancelable: true}}));
                    return 'clicked';
                }}
            }}
            // 尝试 titleRow
            var rows = document.querySelectorAll('[class*="titleRow"]');
            for (var j=0; j<rows.length; j++) {{
                if (rows[j].textContent.includes({json.dumps(song_name)})) {{
                    rows[j].dispatchEvent(new PointerEvent('click', {{bubbles: true, cancelable: true}}));
                    return 'clicked titleRow';
                }}
            }}
            return 'not found';
        }})()
        ''')
        print(f"   结果: {clicked.get('value', '?')}")
        time.sleep(2)

        # Step 2: AI 编辑
        print("Step 2: AI 编辑...")
        r = self.cdp.eval('''
        (function(){
            var btn = document.querySelector('button[class*="aiEditButton"]');
            if (btn) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window, button: 0}));
                return 'clicked';
            }
            return 'not found';
        })()
        ''')
        print(f"   结果: {r.get('value', '?')}")
        time.sleep(2)

        # Step 3: 去 AI 编辑器（带重试 + URL 轮询）
        print("Step 3: 去 AI 编辑器...")
        for attempt in range(3):
            r = self.cdp.eval('''
            (function(){
                var btn = document.querySelector('button[class*="primaryBtn"]');
                if (btn) {
                    btn.scrollIntoView({behavior: "instant", block: "center"});
                    btn.focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(t){
                        btn.dispatchEvent(new PointerEvent(t, {bubbles: true, cancelable: true}));
                    });
                    return 'clicked';
                }
                return 'not found';
            })()
            ''')
            time.sleep(5)
            url = self.cdp.get_url()
            if 'playground' in url:
                print(f"   ✅ 进入编辑器")
                break
            print(f"   重试 {attempt+1}... ({url[:50]})")
        else:
            return {"success": False, "error": "无法进入编辑器"}
        
        # 禁用 alert
        self.cdp.eval("window.onbeforeunload=null;window.alert=function(){}")

        # Step 4: 等编辑器导出按钮可用（替代盲等 10s）
        print("Step 4: 等待编辑器就绪（导出按钮可用）...")
        if not self.cdp.wait_selector('button.semi-button-secondary', timeout=20):
            print("   ⚠️ 导出按钮超时未出现，继续尝试...")

        # Step 5: 点击导出 + 等弹窗
        print("Step 5: 点击导出...")
        for attempt in range(3):
            self.cdp.eval('''
            (function(){
                var btns = document.querySelectorAll('button.semi-button-secondary');
                for (var i=0; i<btns.length; i++) {
                    if (btns[i].textContent.trim() === '导出') {
                        ['mousedown','mouseup','click'].forEach(function(t){
                            btns[i].dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true, view: window, button: 0}));
                        });
                        return;
                    }
                }
            })()
            ''')
            if self.cdp.wait_text('并轨导出', timeout=5):
                print("   ✅ 导出弹窗已打开")
                break
            print(f"   重试 {attempt+1}...")
            time.sleep(2)
        else:
            return {"success": False, "error": "导出弹窗未出现"}

        # Step 6: 改歌名 + 确认导出
        print("Step 6: 改歌名 → 确认导出...")
        self.cdp.eval(f'''
        (function(){{
            var inputs = document.querySelectorAll('input');
            for (var i=0; i<inputs.length; i++) {{
                if (inputs[i].value && inputs[i].value.includes('新项目')) {{
                    inputs[i].disabled = false;
                    inputs[i].removeAttribute('disabled');
                    var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    ns.call(inputs[i], {json.dumps(song_name)});
                    inputs[i].dispatchEvent(new Event('input', {{bubbles: true}}));
                    inputs[i].dispatchEvent(new Event('change', {{bubbles: true}}));
                    return 'renamed';
                }}
            }}
            return 'no rename needed';
        }})()
        ''')
        time.sleep(1)

        # Step 7: 确认导出
        print("Step 7: 确认导出...")
        self.cdp.eval('''
        (function(){
            var btns = document.querySelectorAll('button.semi-button');
            for (var i=0; i<btns.length; i++) {
                var t = btns[i].textContent.trim();
                if (t === '导出' || t === '并轨导出' || t === '确认导出') {
                    ['mousedown','mouseup','click'].forEach(function(tt){
                        btns[i].dispatchEvent(new MouseEvent(tt, {bubbles: true, cancelable: true, view: window, button: 0}));
                    });
                    return 'confirmed';
                }
            }
            return 'not found';
        })()
        ''')

        # Step 8: 等待跳转到资产页
        print("Step 8: 等待导出完成 → 资产页...")
        for i in range(30):
            time.sleep(3)
            url = self.cdp.get_url()
            if 'assets' in url:
                print(f"   ✅ 跳转到资产页 ({i*3+3}s)")
                break
            if i % 5 == 0:
                print(f"   ... 导出中 ({i*3+3}s, url={url[:50]})")
        else:
            print(f"   ⏰ 超时，当前 URL: {url[:60]}")

        # 验证
        time.sleep(2)
        self.cdp.navigate("https://music.douyin.com/studio/assets")
        time.sleep(3)
        has_song = self.cdp.eval(f"document.body.textContent.includes({json.dumps(song_name)})")
        ok = has_song.get("value", False)
        print(f"   验证: {'✅ 已出现在资产页' if ok else '❌ 未找到'}")

        return {"success": ok, "song": song_name}

    def export_all(self, filter_name=None):
        """批量导出素材列表中的歌曲"""
        print("📋 获取素材列表...")
        songs = self.get_material_list()
        
        # 获取已导出的（从资产页）
        print("📋 获取资产页已有...")
        existing = set(self.get_asset_list())
        
        to_export = [s for s in songs if s['name'] not in existing]
        
        if filter_name:
            to_export = [s for s in to_export if filter_name in s['name']]
        
        print(f"\n素材列表: {len(songs)} 首")
        print(f"资产页已有: {len(existing)} 首")
        print(f"待导出: {len(to_export)} 首")
        for s in to_export:
            print(f"  - {s['name']} ({s['duration']})")
        
        if not to_export:
            print("✅ 没有需要导出的歌曲")
            return {"exported": 0, "results": []}
        
        print(f"\n开始批量导出 {len(to_export)} 首...")
        results = []
        for i, song in enumerate(to_export):
            print(f"\n[{i+1}/{len(to_export)}]")
            r = self.export_one(song['name'])
            results.append(r)
            # 回到作曲页准备下一首
            if i < len(to_export) - 1:
                time.sleep(2)
        
        ok = sum(1 for r in results if r.get("success"))
        print(f"\n{'='*50}")
        print(f"📊 导出完成: {ok}/{len(results)} 成功")
        for r in results:
            flag = "✅" if r.get("success") else "❌"
            print(f"  {flag} {r.get('song', '?')}")
        
        return {"exported": ok, "results": results}


# ── CLI 入口 ────────────────────────────────────────
def main():
    exporter = DouyinExportCDP()
    
    if len(sys.argv) > 1 and sys.argv[1] not in ("--all", "-a"):
        # 导出指定歌曲
        song = sys.argv[1]
        r = exporter.export_one(song)
        print(f"\n结果: {json.dumps(r, ensure_ascii=False)}")
    else:
        # 批量导出全部
        filter_name = sys.argv[2] if len(sys.argv) > 2 else None
        exporter.export_all(filter_name)
    
    exporter.cdp.close()


if __name__ == "__main__":
    main()
