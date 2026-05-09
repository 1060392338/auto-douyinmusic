"""浏览器核心模块

封装 DrissionPage 浏览器控制，提供浏览器启动、导航、JS执行等基础功能。
不依赖业务配置模块（models.config），是纯粹的基础设施层。
"""

import os
import socket
import time
from typing import List, Optional

from DrissionPage.errors import ElementNotFoundError

from DrissionPage import ChromiumPage, ChromiumOptions


class BrowserCore:
    """浏览器核心控制器

    封装 DrissionPage 的 ChromiumPage，管理 Chrome 实例的生命周期。
    支持连接已有 Chrome 或启动新实例，提供便捷的浏览器操作方法。
    """

    CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    def __init__(self, user_data_dir: str, port: int = 9223):
        """初始化浏览器核心

        Args:
            user_data_dir: Chrome 用户数据目录路径（自动创建如果不存在）
            port: 远程调试端口，默认 9223（与头条项目的 9222 区分）
        """
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.port = port
        self.page: Optional[ChromiumPage] = None

        # 确保用户数据目录存在
        os.makedirs(self.user_data_dir, exist_ok=True)

    # ── 锁文件清理 ──────────────────────────────────────────────────────────────

    def _cleanup_lockfiles(self):
        """清理 Chrome 残留锁文件

        在启动新 Chrome 实例前清理上次异常退出留下的锁文件，
        避免 "用户数据目录已被占用" 等启动失败错误。
        """
        lock_files = [
            "SingletonLock",
            "SingletonSocket",
            "SingletonCookie",
            os.path.join("Default", "LOCK"),
        ]
        for rel_path in lock_files:
            path = os.path.join(self.user_data_dir, rel_path)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    print(f"  [BrowserCore] 清理锁文件: {rel_path}", flush=True)
                elif os.path.isdir(path):
                    os.rmdir(path)
                    print(f"  [BrowserCore] 清理锁目录: {rel_path}", flush=True)
            except (OSError, PermissionError) as e:
                print(f"  [BrowserCore] 无法清理 {rel_path}: {e}", flush=True)

    # ── 端口检测 ────────────────────────────────────────────────────────────────

    def _is_port_in_use(self) -> bool:
        """检查调试端口是否已被占用

        Returns:
            True 表示端口已被占用（可能有 Chrome 在运行）
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", self.port)) == 0

    # ── 启动 / 连接 ─────────────────────────────────────────────────────────────

    def launch(self) -> ChromiumPage:
        """启动或连接 Chrome 浏览器

        优先尝试连接已有 Chrome 实例（port 9223），
        失败则启动新的 Chrome 实例并传入必要参数。

        Returns:
            ChromiumPage: 浏览器页面实例
        """
        # ── 先尝试连接已有 Chrome ────────────────────────────────────────────
        if self._is_port_in_use():
            print(
                f"  [BrowserCore] 检测到端口 {self.port} 已被占用，"
                f"尝试连接已有 Chrome...",
                flush=True,
            )
            try:
                self.page = ChromiumPage(addr_or_opts=f"127.0.0.1:{self.port}")
                print(
                    f"  [BrowserCore] ✅ 成功连接到已有 Chrome (端口 {self.port})",
                    flush=True,
                )
                return self.page
            except Exception as e:
                print(
                    f"  [BrowserCore] 连接已有 Chrome 失败: {e}",
                    flush=True,
                )
                print(f"  [BrowserCore] 将尝试清理并启动新的 Chrome 实例", flush=True)

        # ── 清理锁文件 ──────────────────────────────────────────────────────
        self._cleanup_lockfiles()

        # ── 配置 Chrome 启动选项 ────────────────────────────────────────────
        co = ChromiumOptions()
        co.set_browser_path(self.CHROME_PATH)
        co.set_local_port(self.port)
        co.set_user_data_path(self.user_data_dir)
        co.set_argument("--remote-debugging-port", str(self.port))
        co.set_argument("--remote-allow-origins", "*")
        co.set_argument("--no-first-run")
        co.set_argument("--no-default-browser-check")

        print(
            f"  [BrowserCore] 启动新 Chrome 实例 (端口 {self.port})...",
            flush=True,
        )
        print(
            f"  [BrowserCore] 用户数据目录: {self.user_data_dir}",
            flush=True,
        )

        self.page = ChromiumPage(addr_or_opts=co)
        print(f"  [BrowserCore] ✅ Chrome 启动完成", flush=True)
        return self.page

    # ── 页面导航 ────────────────────────────────────────────────────────────────

    def navigate(self, url: str, wait_seconds: int = 3):
        """导航到指定 URL 并等待加载

        Args:
            url: 目标网址
            wait_seconds: 加载完成后额外等待秒数（默认 3 秒）
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 launch()")

        print(f"  [BrowserCore] 导航到: {url}", flush=True)
        self.page.get(url)

        if wait_seconds > 0:
            time.sleep(wait_seconds)

    # ── 登录态检测 ──────────────────────────────────────────────────────────────

    def check_logged_in(self, url: str = "") -> bool:
        """检查当前页面是否处于登录态

        双重检测：
        1. 检查 URL 是否包含登录相关路径
        2. 检查页面上是否有登录弹窗/二维码入口（创作实验室登录）

        Returns:
            True 表示已登录，False 表示未登录
        """
        # 方法1: URL 检查
        if url:
            login_keywords = ["/auth/", "/login/", "/passport/"]
            for keyword in login_keywords:
                if keyword in url:
                    return False

        # 方法2: 页面 DOM 检查（检测登录弹窗元素）
        try:
            body_el = self.page.ele("tag:body")
            page_text = body_el.text if body_el else ""
            print(
                f"  [BrowserCore] check_logged_in DOM: "
                f"body_text_len={len(page_text)}, "
                f"preview={page_text[:100]!r}",
                flush=True,
            )
            # 如果页面上出现"登录创作实验室"、"扫码登录"等字样 → 未登录
            login_indicators = ["登录创作实验室", "扫码登录", "密码登录"]
            for indicator in login_indicators:
                if indicator in page_text:
                    print(
                        f"  [BrowserCore] check_logged_in: "
                        f"发现登录提示「{indicator}」→ 未登录",
                        flush=True,
                    )
                    return False
        except Exception as e:
            print(
                f"  [BrowserCore] check_logged_in DOM检查异常: {e}",
                flush=True,
            )

        return True

    def wait_for_login(self, timeout: int = 120) -> bool:
        """等待用户扫码登录

        轮询检查当前页面 URL，等待用户完成扫码登录。
        每 15 秒打印一次提示信息，防止后台静默。

        Args:
            timeout: 超时时间（秒，默认 120）

        Returns:
            True 表示登录成功，False 表示超时
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 launch()")

        print(
            f"  [BrowserCore] 等待扫码登录（超时 {timeout} 秒）...",
            flush=True,
        )

        start_time = time.time()
        last_print = 0.0

        while time.time() - start_time < timeout:
            current_url = self.page.url
            elapsed = int(time.time() - start_time)

            if self.check_logged_in(current_url):
                print(
                    f"  [BrowserCore] ✅ 扫码登录成功！（耗时 {elapsed} 秒）",
                    flush=True,
                )
                return True

            # 每 15 秒打印一次提示
            if elapsed - last_print >= 15:
                print(
                    f"  [BrowserCore] 等待扫码登录... 已等待 {elapsed} 秒",
                    flush=True,
                )
                last_print = elapsed

            time.sleep(1)

        print(
            f"  [BrowserCore] ❌ 扫码登录超时（{timeout} 秒）",
            flush=True,
        )
        return False

    # ── JavaScript 执行 ─────────────────────────────────────────────────────────

    def run_js(self, js_code: str, *args) -> str:
        """执行 JavaScript 代码

        Args:
            js_code: 要执行的 JavaScript 代码字符串
            *args: 传递给 JS 代码的额外参数

        Returns:
            str: JS 执行返回的结果
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 launch()")

        return self.page.run_js(js_code, *args)

    # ── 元素查找 ────────────────────────────────────────────────────────────────

    def find_element(self, selector: str):
        """查找单个页面元素

        Args:
            selector: CSS 选择器字符串

        Returns:
            ChromiumElement 或类似对象；未找到时返回 None
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 launch()")

        try:
            return self.page.ele(selector)
        except ElementNotFoundError:
            return None

    def find_elements(self, selector: str) -> list:
        """查找多个页面元素

        Args:
            selector: CSS 选择器字符串

        Returns:
            list: 匹配的元素列表（可能为空）
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 launch()")

        return self.page.eles(selector)

    # ── 清理 ────────────────────────────────────────────────────────────────────

    def cleanup(self):
        """清理浏览器资源

        断开 DrissionPage 连接，但不关闭浏览器进程。
        保留 Chrome 实例以供后续复用（持久化登录态）。
        """
        if self.page:
            try:
                # 只断开 DrissionPage 连接，不导航到 about:blank
                # 保留当前页面状态避免 SPA 会话中断
                print(
                    "  [BrowserCore] 断开 DrissionPage 连接，Chrome 进程保留",
                    flush=True,
                )
            except Exception as e:
                print(f"  [BrowserCore] 清理时出错: {e}", flush=True)
            finally:
                self.page = None
