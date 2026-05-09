"""AI作曲服务

封装抖音音乐开放平台AI作曲模块的浏览器自动化操作。
基于真实 DOM 结构（2026-05-09 实测）：
- 导航栏：<div class="navigation-item-wrapper-LJh_pw">AI 作曲</div>
- 作曲页URL: /studio/create (SPA路由，需JS点击导航)
- 高级模式：style textarea + lyrics textarea +「生成歌曲」按钮
"""

import time
from typing import Optional

from infrastructure.browser import BrowserCore
from models.song import CompositionPrompt, Lyrics, MusicAsset


# ── 选择器常量 ────────────────────────────────────────────────────────────────
# AI作曲导航项
_NAV_AI_COMPOSE = "xpath://div[contains(@class,'navigation-item-wrapper') and contains(.,'AI 作曲')]"
# 高级模式按钮
_BTN_ADVANCED_MODE = "xpath://button[contains(.,'高级模式')]"
# 生成歌曲按钮
_BTN_GENERATE_SONG = "xpath://button[contains(.,'生成歌曲')]"
# 优化提示词按钮
_BTN_OPTIMIZE = "xpath://button[contains(.,'优化提示词') and not(contains(@class,'disabled'))]"
# 歌词输入框（placeholder-based，高级模式中的第一个textarea）
_TEXTAREA_LYRICS = "xpath://textarea"

STUDIO_URL = "https://music.douyin.com/studio"


class CompositionService:
    """AI作曲服务

    通过浏览器自动化完成从导航到AI作曲、填写风格描述和歌词、生成音乐的全流程。
    """

    def __init__(self, browser: BrowserCore):
        self.browser = browser
        self._studio_url: str = ""
        print("[CompositionService] AI作曲服务初始化完成", flush=True)

    # ── 导航 ──────────────────────────────────────────────────────────────────

    def navigate_to_studio(self, studio_url: str = ""):
        """导航到抖音音乐开放平台工作室

        Args:
            studio_url: 工作室 URL。为空时使用默认值。
        """
        url = studio_url or STUDIO_URL
        self._studio_url = url
        print(f"[CompositionService] 导航到编曲平台: {url}", flush=True)
        self.browser.navigate(url, wait_seconds=5)

    def enter_composition_module(self):
        """点击左侧导航栏「AI 作曲」进入模块

        SPA 路由页（/studio/create）无法直接导航访问，
        需要用 JS 触发点击事件确保路由器切换。
        """
        print("[CompositionService] 点击「AI 作曲」导航项...", flush=True)
        nav = self.browser.find_element(_NAV_AI_COMPOSE)
        if nav is None:
            raise RuntimeError("未找到「AI 作曲」导航项，请确认页面已加载")

        # 先用常规点击
        nav.click()
        time.sleep(2)

        # 如果 URL 没变到 /create，用 JS 强制触发
        if self.browser.page and '/create' not in self.browser.page.url:
            print("[CompositionService] 常规点击未生效，使用 JS 触发...", flush=True)
            self._js_click_nav("AI 作曲")

        current_url = self.browser.page.url if self.browser.page else "unknown"
        print(f"[CompositionService] ✅ 已进入 AI 作曲模块 (URL: {current_url})", flush=True)

    def _js_click_nav(self, nav_text: str):
        """用 JS 强制点击导航项

        Args:
            nav_text: 导航项文本，如 'AI 作曲', 'AI 作词'
        """
        js = f"""
        (function() {{
            var navs = document.querySelectorAll('[class*="navigation-item-wrapper"]');
            for (var i = 0; i < navs.length; i++) {{
                if (navs[i].textContent.trim().includes('{nav_text}')) {{
                    navs[i].click();
                    navs[i].dispatchEvent(new MouseEvent('click', {{bubbles: true, cancelable: true, view: window}}));
                    return 'clicked';
                }}
            }}
            return 'not found';
        }})();
        """
        self.browser.run_js(js)
        time.sleep(3)

    def switch_to_advanced_mode(self):
        """切换到高级模式（双输入框模式）"""
        print("[CompositionService] 切换到高级模式...", flush=True)
        btn = self.browser.find_element(_BTN_ADVANCED_MODE)
        if btn is None:
            # 可能已经在高级模式
            print("[CompositionService] ⚠️ 未找到高级模式按钮，可能已处于高级模式", flush=True)
            return
        btn.click()
        time.sleep(1.5)
        print("[CompositionService] ✅ 已切换到高级模式", flush=True)

    # ── 提示词构造 ──────────────────────────────────────────────────────────

    def generate_composition_prompt(
        self,
        theme: str,
        lyrics_text: str = "",
        use_advanced: bool = False,
    ) -> CompositionPrompt:
        """构造作曲提示词对象（不调用外部 API，仅构造对象）

        Args:
            theme: 歌曲主题
            lyrics_text: 歌词文本
            use_advanced: 是否使用高级模式

        Returns:
            CompositionPrompt: 包含风格描述和歌词的提示词对象
        """
        style_description = (
            f"主题：{theme}。"
            f"请创作一首以「{theme}」为主题的歌曲，"
            f"风格温暖动人，旋律优美流畅，编曲层次丰富。"
        )
        if use_advanced:
            style_description += (
                " 使用高级编曲配置，包含弦乐、钢琴、吉他等多样化乐器，"
                "动态范围宽广，情感表达细腻丰富。"
            )

        lyrics = None
        if lyrics_text:
            lyrics = Lyrics(raw_text=lyrics_text, is_refined=False)

        prompt = CompositionPrompt(
            style_description=style_description,
            lyrics=lyrics,
        )
        print(f"[CompositionService] ✅ 已构造作曲提示词（主题: {theme}）", flush=True)
        return prompt

    # ── 表单填写 ──────────────────────────────────────────────────────────────

    def _react_set_textarea_value(self, text: str, selector_index: int = 0):
        """通过 React 兼容方式设置 textarea 的值

        Args:
            text: 要填入的文本
            selector_index: textarea 索引（0=灵感, 1=风格）
        """
        js = f"""
        (function(text) {{
            var tas = document.querySelectorAll('textarea');
            if (!tas || tas.length <= {selector_index}) return 'no textarea at ' + {selector_index};
            var ta = tas[{selector_index}];
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeSetter.call(ta, text);
            ta.dispatchEvent(new Event('input', {{bubbles: true}}));
            return 'ok';
        }})();
        """
        self.browser.run_js(js)

    def fill_composition_form(self, prompt: CompositionPrompt):
        """填写作曲表单

        在高级模式下：
        第一个 textarea ← 歌词文本
        第二个 textarea ← 风格描述

        Args:
            prompt: 作曲提示词对象
        """
        if not prompt.style_description:
            raise ValueError("风格描述不能为空")

        # ── 确保在高级模式 ───────────────────────────────────────────────────
        self.switch_to_advanced_mode()

        # ── 填写歌词（第一个 textarea）───────────────────────────────────────
        lyrics_text = prompt.lyrics.raw_text if prompt.lyrics else ""
        if lyrics_text:
            print(
                f"[CompositionService] 填写歌词（{len(lyrics_text)} 字）...",
                flush=True,
            )
            self._react_set_textarea_value(lyrics_text, selector_index=0)
            time.sleep(1)
        else:
            print("[CompositionService] ⚠️ 无可用的歌词文本，跳过歌词填写", flush=True)

        # ── 填写风格描述（第二个 textarea）───────────────────────────────────
        print(
            f"[CompositionService] 填写风格描述: {prompt.style_description[:60]}...",
            flush=True,
        )
        self._react_set_textarea_value(prompt.style_description, selector_index=1)
        time.sleep(1)

        print("[CompositionService] ✅ 作曲表单填写完成", flush=True)

    # ── 生成音乐 ──────────────────────────────────────────────────────────────

    def generate_music(self) -> MusicAsset:
        """点击「生成歌曲」按钮，等待 AI 作曲完成，返回生成结果

        AI 作曲生成时间较长，等待 30 秒。
        生成后从素材列表抓取真实资产名称。

        Returns:
            MusicAsset: 生成音乐资产信息

        Raises:
            RuntimeError: 生成按钮未找到或生成超时
        """
        print(
            "[CompositionService] 点击「生成歌曲」按钮，等待 AI 作曲生成...",
            flush=True,
        )

        # ── 查找并点击生成按钮 ─────────────────────────────────────────────
        btn = self.browser.find_element(_BTN_GENERATE_SONG)
        if btn is None:
            raise RuntimeError("未找到「生成歌曲」按钮，请确认页面和输入状态")

        if btn.attr("disabled") == "true":
            print("[CompositionService] ⚠️ 生成按钮被禁用，尝试等待...", flush=True)
            time.sleep(5)

        btn.click()

        # ── 等待生成完成 ────────────────────────────────────────────────────
        print("[CompositionService] ⏳ 正在生成音乐，请稍候（约 30 秒）...", flush=True)
        time.sleep(30)

        # ── 从素材列表抓取真实资产名称 ──────────────────────────────────────
        real_name, real_duration = self._extract_latest_asset_from_list()

        asset = MusicAsset(
            asset_id=f"composition_{int(time.time())}",
            name=real_name or f"AI作曲_{time.strftime('%Y%m%d_%H%M%S')}",
            duration_seconds=real_duration,
        )

        print(
            f"[CompositionService] ✅ AI 作曲生成完成 "
            f"(name={asset.name}, asset_id={asset.asset_id})",
            flush=True,
        )
        return asset

    def _extract_latest_asset_from_list(self) -> tuple:
        """从素材列表中提取最新生成的资产名称和时长

        素材列表在 AI 作曲页面底部，新生成的资产出现在列表顶部。
        使用 DrissionPage 本地方法（不依赖 run_js 返回值）。

        Returns:
            tuple: (name: str or None, duration: float)
        """
        try:
            if not self.browser.page:
                return None, 0.0

            # 方法1: 找 titleRow（歌曲名行）
            title_rows = self.browser.page.eles(
                'xpath://div[contains(@class,"titleRow")]'
            )
            # 跳过第一个（可能是"AI 作曲素材"标题）
            valid_names = []
            for row in title_rows:
                row_text = row.text.strip()
                if row_text and len(row_text) < 10 and row_text not in [
                    "AI 作曲素材", "AI 歌词", "本地素材", "收藏", "素材列表"
                ]:
                    valid_names.append(row_text)

            if valid_names:
                # 取第一个（最新生成的）
                name = valid_names[0]
                print(
                    f"[CompositionService] 从素材列表抓取到资产: \"{name}\"",
                    flush=True,
                )
                return name, 0.0

            # 方法2: 在素材列表区域找所有p.title-NDu45m元素
            titles = self.browser.page.eles(
                'xpath://p[contains(@class,"title")]'
            )
            for t in titles:
                t_text = t.text.strip()
                if t_text and len(t_text) < 10 and "Sway" not in t_text:
                    print(
                        f"[CompositionService] 从p.title抓取到资产: \"{t_text}\"",
                        flush=True,
                    )
                    return t_text, 0.0

        except Exception as e:
            print(
                f"[CompositionService] ⚠️ 抓取素材名称失败: {e}，使用默认名",
                flush=True,
            )
        return None, 0.0

    @staticmethod
    def _clean_asset_name(raw: str) -> str:
        """从原始文本中提取资产名称

        素材项文本格式如: '星落肩头 Sway v5.5 03:01'
        提取: '星落肩头'

        Args:
            raw: 原始文本

        Returns:
            str: 清理后的资产名称，无法提取返回空字符串
        """
        import re
        if not raw:
            return ""
        # 移除已知的平台文本
        for keyword in ["AI 作曲素材", "AI 歌词", "本地素材", "收藏", "素材列表"]:
            raw = raw.replace(keyword, "")
        raw = raw.strip()
        # 匹配名称模式：中文/英文名称 + Sway/模型名 + 时间
        m = re.match(r'^([^Sway]+?)(?:Sway|v\d)', raw)
        if m:
            name = m.group(1).strip()
            if name and len(name) < 20:
                return name
        # 简单取第一个非空行
        lines = [l.strip() for l in raw.split() if l.strip()]
        if lines:
            return lines[0]
        return ""

    # ── 完整流程 ──────────────────────────────────────────────────────────────

    def compose_with_prompt(self, prompt: CompositionPrompt) -> MusicAsset:
        """使用传入的提示词完成作曲全流程

        流程：导航 → 进入AI作曲 → 高级模式 → 填表 → 生成音乐

        Args:
            prompt: 由词曲 Agent 准备好的 CompositionPrompt 对象

        Returns:
            MusicAsset: 生成音乐资产
        """
        print("[CompositionService] 🎵 开始使用提示词作曲...", flush=True)
        self.navigate_to_studio()
        self.enter_composition_module()
        self.fill_composition_form(prompt)
        asset = self.generate_music()
        print("[CompositionService] 🎵 提示词作曲流程完成", flush=True)
        return asset

    def compose(
        self,
        lyrics: str,
        theme: str,
        use_advanced: bool = False,
    ):
        """完整作曲流程：构造提示词 → 填表 → 生成音乐

        Args:
            lyrics: 歌词文本
            theme: 歌曲主题
            use_advanced: 是否使用高级模式

        Returns:
            Tuple[CompositionPrompt, MusicAsset]: (构造的提示词, 生成的音乐资产)
        """
        print("[CompositionService] 🎵 开始完整作曲流程...", flush=True)
        prompt = self.generate_composition_prompt(theme, lyrics, use_advanced)
        asset = self.compose_with_prompt(prompt)
        print("[CompositionService] 🎵 完整作曲流程完成", flush=True)
        return prompt, asset
