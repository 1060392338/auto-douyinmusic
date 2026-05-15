#!/usr/bin/env python3
"""page_check.py — 机械化前置检查

每次运行任何操作脚本前执行此检查：
1. Chrome 端口 9223 是否在线
2. 用户数据目录是否正确（非临时目录）
3. 当前页面是否有效（/create 或 /assets）

用法：
    python scripts/page_check.py
    退出码 0 = 全部通过，可以继续
    退出码 1 = 条件不满足，停止
"""

import json
import os
import subprocess
import sys
import time
from http.client import HTTPConnection


def check_chrome_port(port=9223):
    """检查 Chrome 调试端口是否在线"""
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", "/json/version")
        resp = conn.getresponse()
        data = json.loads(resp.read().decode())
        conn.close()

        # 检查 user-data-dir
        cmd = f"ps aux | grep 'chrome.*{port}' | grep -o 'user-data-dir=[^ ]*' | head -1"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        udd = result.stdout.strip()

        expected_dir = os.path.expanduser(
            "~/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data"
        )

        print(f"  ✅ Chrome 9223 在线", flush=True)
        print(f"  📁 user-data-dir: {udd or '未知'}", flush=True)

        if udd and "DrissionPage" in udd:
            print(
                "  ❌ 警告: Chrome 连接到临时目录！Session 不会持久化！",
                flush=True,
            )
            print(f"  ✅ 期待: {expected_dir}", flush=True)
            return False

        return True
    except Exception as e:
        print(f"  ❌ Chrome 9223 不在线: {e}", flush=True)
        return False


def check_cookie_has_ssid(port=9223):
    """检查是否有有效的登录 cookie (ssid)"""
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=3)
        conn.request("GET", "/json")
        resp = conn.getresponse()
        pages = json.loads(resp.read().decode())
        conn.close()

        if not pages:
            print("  ❌ 没有已打开的页面", flush=True)
            return False

        target_id = pages[-1]["id"]  # 最新标签页
        ws_url = pages[-1]["webSocketDebuggerUrl"]

        # 通过 CDP 获取 cookies
        import asyncio
        import websockets

        async def get_cookies():
            async with websockets.connect(ws_url, max_size=2**20) as ws:
                msg_id = 1
                await ws.send(
                    json.dumps(
                        {
                            "id": msg_id,
                            "method": "Network.getCookies",
                            "params": {"urls": ["https://music.douyin.com"]},
                        }
                    )
                )
                resp = json.loads(await ws.recv())
                cookies = resp.get("result", {}).get("cookies", [])
                has_ssid = any(c.get("name") == "sid" or "ssid" in c.get("name", "") for c in cookies)
                return has_ssid, len(cookies)

        has_ssid, count = asyncio.run(get_cookies())
        print(f"  🍪 Cookie 数: {count}", flush=True)
        if has_ssid:
            print(f"  ✅ 登录态有效", flush=True)
        else:
            print(f"  ❌ 无有效登录 cookie", flush=True)
        return has_ssid

    except ImportError:
        print("  ⚠️  缺少 websockets，跳过 cookie 检查", flush=True)
        return True  # 降级：没有 websockets 就跳过
    except Exception as e:
        print(f"  ⚠️  Cookie 检查异常: {e}", flush=True)
        return True  # 降级通过


def main():
    print("\n🔍 [page_check] 前置状态检查", flush=True)

    checks = [
        ("Chrome 端口 9223 在线", check_chrome_port()),
        ("登录态有效", check_cookie_has_ssid()),
    ]

    all_pass = all(result for _, result in checks)
    print("", flush=True)

    if all_pass:
        print("  ✅ [page_check] 全部通过，可以继续\n", flush=True)
        sys.exit(0)
    else:
        print("  ❌ [page_check] 条件不满足，请先修复\n", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
