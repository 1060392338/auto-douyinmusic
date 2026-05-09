"""AI作词服务

封装抖音音乐开放平台AI作词模块的浏览器操作。
基于真实 DOM 结构（2026-05-09 实测）：
- 导航栏：<div class="navigation-item-wrapper-LJh_pw">AI 作词</div>
- 聊天界面：textarea.semi-input-textarea + 发送按钮
"""

import json
import time
from typing import Optional

from infrastructure.browser import BrowserCore
from models.song import Lyrics


# ── 选择器常量 ────────────────────────────────────────────────────────────────
# AI作词导航项（左侧边栏）
_NAV_AI_LYRICS = "xpath://div[contains(@class,'navigation-item-wrapper') and contains(.,'AI 作词')]"
# 聊天输入框
_TEXTAREA_CHAT = "tag:textarea"
# 发送按钮（聊天界面）
_BTN_SEND = "xpath://button[contains(@class,'semi-chat-inputBox-sendButton') or contains(@class,'semi-chat-inputBox-sendButto')]"
# 聊天消息容器
_CONTAINER_CHAT = "xpath://div[contains(@class,'chatContent')]//div[contains(@class,'semi-chat-container')]"
# 消息气泡（AI 回复）
_MSG_AI_REPLY = "xpath://div[contains(@class,'semi-chat-content')]//div[contains(@class,'semi-chat-bubble')]"
# 去作曲按钮（歌词生成后出现）
_BTN_GO_COMPOSE = "xpath://button[contains(.,'去作曲')]"

STUDIO_URL = "https://music.douyin.com/studio"


class LyricsService:
    """AI作词服务

    通过浏览器自动化完成从导航到AI作词、输入灵感、生成歌词的完整流程。
    """

    def __init__(self, browser: BrowserCore):
        self.browser = browser
        print("[LyricsService] AI作词服务初始化完成", flush=True)

    # ── 页面操作方法 ──────────────────────────────────────────────────────────

    def navigate_to_studio(self):
        """导航到抖音音乐开放平台工作室首页"""
        print("[LyricsService] 导航到工作室页面...", flush=True)
        self.browser.navigate(STUDIO_URL, wait_seconds=3)
        print("[LyricsService] ✅ 已到达工作室页面", flush=True)

    def enter_lyrics_module(self):
        """点击左侧导航栏「AI 作词」进入模块"""
        print("[LyricsService] 点击「AI 作词」导航项...", flush=True)
        nav = self.browser.find_element(_NAV_AI_LYRICS)
        if nav is None:
            raise RuntimeError("未找到「AI 作词」导航项，请确认页面已加载")
        nav.click()
        time.sleep(2)
        print("[LyricsService] ✅ 已进入AI作词模块", flush=True)

    def _react_set_textarea_value(self, text: str):
        """通过 React 兼容方式设置 textarea 的值

        React 监听 input 事件而非直接的 value 变更（受控组件）。
        使用原生 value setter + dispatchEvent 来触发 React 状态更新。
        """
        js = """
        (function(text) {
            var ta = document.querySelector('textarea');
            if (!ta) return 'no textarea';
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeSetter.call(ta, text);
            ta.dispatchEvent(new Event('input', {bubbles: true}));
            return 'ok';
        })(arguments[0]);
        """
        self.browser.run_js(js, text)

    def input_inspiration(self, prompt: str):
        """在AI作词聊天输入框中输入灵感提示词

        Args:
            prompt: 用户提供的主题或灵感提示词
        """
        print(f"[LyricsService] 输入灵感提示词: 「{prompt}」", flush=True)

        structured_prompt = (
            f"主题：{prompt}\n\n"
            "请按以下结构生成完整歌词：\n"
            "【主歌1】\n"
            "【副歌】\n"
            "【主歌2】\n"
            "【副歌】\n"
            "【桥段】\n"
            "【副歌】\n"
            "【尾奏】\n\n"
            "要求：押韵、情感丰富、朗朗上口。"
        )

        ta = self.browser.find_element(_TEXTAREA_CHAT)
        if ta is None:
            raise RuntimeError("未找到歌词输入框")

        # React 受控组件：清空后填入
        ta.clear()
        self._react_set_textarea_value(structured_prompt)
        print("[LyricsService] ✅ 灵感提示词已填入", flush=True)

    def _click_send_and_wait(self, timeout: int = 30) -> str:
        """点击发送按钮，等待 AI 回复，返回消息文本

        发送后轮询聊天容器，检测 AI 消息气泡的出现。
        最多等待 timeout 秒。

        Args:
            timeout: 最大等待时间（秒）

        Returns:
            str: AI 回复的完整文本

        Raises:
            RuntimeError: 发送按钮不可用或超时
        """
        # ── 点击发送 ─────────────────────────────────────────────────────────
        send_btn = self.browser.find_element(_BTN_SEND)
        if send_btn is None:
            raise RuntimeError("未找到发送按钮")
        if send_btn.attr("disabled") == "true":
            raise RuntimeError("发送按钮被禁用，请检查输入是否有效")

        print("[LyricsService] 点击发送按钮，等待AI生成歌词...", flush=True)
        send_btn.click()

        # ── 轮询等待 AI 回复 ─────────────────────────────────────────────────
        poll_interval = 2
        elapsed = 0

        while elapsed < timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval
            print(
                f"[LyricsService] ⏳ 等待AI生成... ({elapsed}s/{timeout}s)",
                flush=True,
            )

            try:
                # 尝试获取 AI 回复消息
                reply = self._get_latest_ai_reply()
                if reply:
                    print(
                        f"[LyricsService] ✅ AI回复获取成功（{len(reply)} 字）",
                        flush=True,
                    )
                    return reply
            except Exception:
                pass

        raise RuntimeError(f"AI生成超时（{timeout}秒），未获取到歌词回复")

    def _get_latest_ai_reply(self) -> Optional[str]:
        """获取最新的 AI 回复消息文本

        通过 JS 遍历聊天消息气泡，获取最后一条 AI 回复。

        Returns:
            Optional[str]: 最新 AI 回复文本，无回复则返回 None
        """
        js = """
        (function() {
            // 查找所有聊天消息气泡
            var bubbles = document.querySelectorAll(
                '.semi-chat-bubble, [class*="chat-bubble"], ' +
                '.chatContent-wuQO1i .semi-chat-content [class*="bubble"]'
            );
            if (!bubbles || bubbles.length === 0) {
                // 尝试更广泛的查找
                var all = document.querySelectorAll(
                    '.semi-chat-content > div > div > div, ' +
                    '.semi-chat-container > div > div > div'
                );
                var lastText = '';
                for (var i = 0; i < all.length; i++) {
                    var t = all[i].textContent.trim();
                    if (t.length > lastText.length) lastText = t;
                }
                return lastText || null;
            }
            // 取最后一个气泡的文本
            var last = bubbles[bubbles.length - 1];
            var text = last.textContent.trim();
            return text.length > 20 ? text : null;
        })();
        """
        result = self.browser.run_js(js)
        if result and isinstance(result, str) and len(result.strip()) > 20:
            return result.strip()
        return None

    def _fallback_get_page_text(self) -> Optional[str]:
        """降级方案：获取整个页面可见文本"""
        body_text = self.browser.run_js("return document.body.innerText;")
        if body_text and len(body_text.strip()) > 50:
            return body_text.strip()
        return None

    # ── 完整流程 ──────────────────────────────────────────────────────────────

    def create_lyrics(self, theme: str) -> Lyrics:
        """一键生成AI歌词的完整流程

        流程：导航 → 进入AI作词 → 输入灵感 → 发送 → 等待回复 → 提取歌词

        Args:
            theme: 歌词主题

        Returns:
            Lyrics: 包含生成歌词文字的 Lyrics 对象
        """
        print(
            f"\n{'='*60}\n"
            f"  [LyricsService] 开始AI作词流程 - 主题: 「{theme}」\n"
            f"{'='*60}",
            flush=True,
        )

        # ── 页面导航 ─────────────────────────────────────────────────────────
        self.navigate_to_studio()
        self.enter_lyrics_module()
        self.input_inspiration(theme)

        # ── 发送并等待生成 ───────────────────────────────────────────────────
        try:
            raw_text = self._click_send_and_wait(timeout=45)
        except RuntimeError as e:
            print(f"[LyricsService] ❌ 发送生成失败: {e}", flush=True)
            # 降级：尝试获取页面文本
            raw_text = self._fallback_get_page_text() or ""
            if raw_text:
                print(
                    "[LyricsService] ⚠️ 使用 JS 降级方案获取到页面文本",
                    flush=True,
                )

        # ── 封装结果 ─────────────────────────────────────────────────────────
        lyrics = Lyrics(
            raw_text=raw_text,
            structure={},
            is_refined=False,
        )

        print(
            f"\n{'='*60}\n"
            f"  [LyricsService] ✅ AI作词流程完成\n"
            f"  歌词长度: {len(raw_text)} 字\n"
            f"{'='*60}",
            flush=True,
        )
        return lyrics
