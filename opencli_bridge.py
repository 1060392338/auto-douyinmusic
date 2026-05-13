"""
OpenCLI Bridge — Python 封装层，通过 subprocess 调用 opencli browser 命令。

用途: 替代 DrissionPage/CDP，用 OpenCLI 驱动浏览器自动化。
React 受控组件通过 eval + 原生 DOM API 绕过。
"""

import subprocess
import json
import time
import re
from typing import Optional


class OpenCLIBridge:
    """opencli browser 命令桥接"""

    def __init__(self, session: str = "dm", window: str = "background"):
        self.session = session
        self.window = window

    def _run(self, *args) -> dict:
        """执行 opencli browser 命令，返回 JSON"""
        cmd = ["opencli", "browser", "--session", self.session]
        if self.window:
            cmd.extend(["--window", self.window])
        cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"error": result.stderr.strip(), "stdout": result.stdout.strip()}
        stdout = result.stdout.strip()
        # opencli 有时在 JSON 前输出 "URL:" 行，需要跳过
        if stdout.startswith("URL:"):
            stdout = stdout.split("\n", 1)[-1].strip()
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"raw": stdout}

    # ── 页面操作 ────────────────────────────────────

    def open(self, url: str) -> dict:
        return self._run("open", url)

    def state(self) -> dict:
        """获取页面状态（含交互元素索引）"""
        return self._run("state")

    def screenshot(self, path: str = None) -> dict:
        args = ["screenshot"]
        if path:
            args.append(path)
        return self._run(*args)

    def back(self) -> dict:
        return self._run("back")

    # ── 交互操作 ────────────────────────────────────

    def click(self, index: int) -> dict:
        """点击元素（按 state 返回的索引）"""
        return self._run("click", str(index))

    def native_click(self, selector: str) -> dict:
        """原生 JS click（用于 React 按钮）"""
        js = f"(function(){{document.querySelector({json.dumps(selector)}).click();return 'clicked'}})()"
        return self._run("eval", js)

    def type_text(self, index: int, text: str) -> dict:
        """opencli 内置 type"""
        return self._run("type", str(index), text)

    def native_type(self, selector: str, text: str) -> dict:
        """原生 JS 注入文本（用于 React textarea/input）"""
        js = f"""
(() => {{
const el = document.querySelector({json.dumps(selector)});
const ns = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype, 'value'
)?.set || Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value'
)?.set;
ns.call(el, {json.dumps(text)});
el.dispatchEvent(new Event('input', {{bubbles: true}}));
el.dispatchEvent(new Event('change', {{bubbles: true}}));
return 'typed ' + el.value.length;
}})()
"""
        return self._run("eval", js)

    def eval(self, js: str) -> dict:
        return self._run("eval", js)

    def fill(self, index: int, text: str) -> dict:
        """opencli 内置 fill（设置值并验证）"""
        return self._run("fill", str(index), text)

    def scroll(self, direction: str = "down") -> dict:
        return self._run("scroll", direction)

    def hover(self, index: int) -> dict:
        return self._run("hover", str(index))

    def keys(self, key: str) -> dict:
        return self._run("keys", key)

    # ── 等待 ────────────────────────────────────────

    def wait_time(self, seconds: int) -> dict:
        return self._run("wait", "time", str(seconds))

    def wait_selector(self, css: str) -> dict:
        return self._run("wait", "selector", css)

    def wait_text(self, text: str) -> dict:
        return self._run("wait", "text", text)

    # ── 页面属性 ────────────────────────────────────

    def get_url(self) -> str:
        result = self._run("get", "url")
        if "raw" in result:
            return result["raw"]
        return result.get("url", "")

    def get_title(self) -> str:
        result = self._run("get", "title")
        if "raw" in result:
            return result["raw"]
        return result.get("title", "")

    def extract(self) -> dict:
        """提取页面内容为 markdown"""
        return self._run("extract")

    def console(self) -> dict:
        """读取浏览器控制台消息"""
        return self._run("console")

    def network(self) -> dict:
        """捕获网络请求"""
        return self._run("network")

    # ── 标签管理 ────────────────────────────────────

    def tab_list(self) -> dict:
        return self._run("tab", "list")

    def tab_new(self, url: str = None) -> dict:
        args = ["tab", "new"]
        if url:
            args.append(url)
        return self._run(*args)

    def close(self) -> dict:
        return self._run("close")


def find_in_state(state: dict, test_id: str = None, text: str = None, 
                  role: str = None, tag: str = None) -> list[dict]:
    """在 state 返回的 data 中搜索匹配的元素。
    
    返回匹配的元素信息列表，每项含 {index, tag, text, ...}
    注意：state['data'] 是原始文本，需要解析。
    """
    data = state.get("data", "")
    if not data:
        return []
    
    results = []
    # 解析 [N]<element ...> 模式
    pattern = re.compile(r'\[(\d+)\]<(button|div|span|input|textarea|a|select|img|p|label)\b([^>]*)>')
    for m in pattern.finditer(data):
        idx = int(m.group(1))
        elem_tag = m.group(2)
        attrs = m.group(3)
        
        match = True
        if test_id and f'data-testid={test_id}' not in attrs:
            match = False
        if role and f'role={role}' not in attrs:
            match = False
        if tag and elem_tag != tag:
            match = False
        if text:
            # 找元素后面的文本内容
            remaining = data[m.end():]
            text_match = re.search(r'([^<\n]{0,50})', remaining)
            if text_match:
                element_text = text_match.group(1).strip()
                if text not in element_text:
                    match = False
            else:
                match = False
        
        if match:
            results.append({"index": idx, "tag": elem_tag, "attrs": attrs})
    
    return results
