"""AI编辑器服务

基于 2026-05-09 实测验证的完整导出流程：
1. 在作曲页点击素材列表中的歌曲
2. 详情面板 → 点击「AI 编辑」按钮（弹窗触发）
3. 点击「去 AI 编辑器」按钮（SPA导航到编辑器，歌曲已加载）
4. 点击导出按钮（必须点内层<span>非<button>本身）
5. 导出弹窗 → 点击「导出」确认按钮（JS全事件链）
6. 等待导出完成 → 自动跳转到「我的资产」

关键发现：
- 编辑器素材Tab只支持本地文件上传，不显示AI作曲素材
- 导出按钮需点击data-audio-control-bar-button-type=export的内层span
- 项目名称为React受控组件，DOM value setter不更新内部状态
- 导出对话框的"歌曲名"input为disabled，无法编辑
"""

import os
import time
from typing import Optional

from infrastructure.browser import BrowserCore
from models.song import MusicAsset, Song


# ── 选择器常量 ────────────────────────────────────────────────────────────────
_COMPOSE_URL = "https://music.douyin.com/studio/create"

# 导出按钮：必须点击内层<span>，不能点<button>本身
# data-audio-control-bar-button-type 属性唯一标识导出按钮
_BTN_EXPORT_SPAN = (
    'xpath://button[@data-audio-control-bar-button-type="export"]'
    '//span[contains(.,"导出")]'
)
# 导出确认按钮（对话框中的primary按钮）
_BTN_CONFIRM_EXPORT = (
    'xpath://button[contains(@class,"semi-button-primary")'
    ' and contains(.,"导出")]'
)
# 保存按钮
_BTN_SAVE = "xpath://button[contains(.,'保存')]"
# 保存并返回（beforeunload对话框）
_BTN_LEAVE = "xpath://button[contains(.,'离开') or contains(.,'退出')]"

# 我的资产页
_ASSETS_URL = "https://music.douyin.com/studio/assets"
# 三点菜单图标（下拉菜单触发）
_MENU_MORE_ICON = 'xpath://*[@data-dropdown-trigger-id and contains(@class,"menuMoreWrapper")]//*[name()="svg"]'
# 重命名选项
_BTN_RENAME = "xpath://*[contains(.,'重命名') and not(ancestor::*[contains(@class,'assetItemWrapper')])]"
# 确定按钮
_BTN_CONFIRM = "xpath://button[contains(.,'确定')]"
# 取消按钮
_BTN_CANCEL = "xpath://button[contains(.,'取消')]"


class EditorService:
    """AI编辑器服务

    通过浏览器自动化完成歌曲的编辑器加载、导出和重命名。
    不再使用编辑器内的素材Tab（该Tab仅支持本地文件上传）。
    """

    def __init__(self, browser: BrowserCore):
        self.browser = browser
        print("[EditorService] AI编辑器服务初始化完成", flush=True)

    # ── 编辑器入口：从作曲页通过素材详情进入 ────────────────────────────────

    def enter_editor_via_song(self, song_name: str):
        """从作曲页加载歌曲到编辑器

        正确路径（2026-05-09 实测）：
        作曲页（/studio/create）→ 点素材列表中的歌曲 → 详情面板
        → 点「AI 编辑」(popup触发) → 点「去 AI 编辑器」(SPA导航)

        Args:
            song_name: 素材列表中的歌曲名称（如"缓歌寄意"）

        Raises:
            RuntimeError: 任一环节失败
        """
        self._disable_beforeunload()
        print(f"[EditorService] 加载歌曲到编辑器: {song_name}", flush=True)

        # 1. 确保在作曲页
        if self.browser.page and '/studio/create' not in self.browser.page.url:
            self._navigate_to_compose_page()
        time.sleep(1)

        # 2. 点击素材列表中的歌曲
        print(f"[EditorService] 点击素材: {song_name}", flush=True)
        song_el = self.browser.find_element(
            f'xpath://div[contains(@class,"titleRow") and contains(.,"{song_name}")]',
        )
        if not song_el:
            raise RuntimeError(f"未找到素材: {song_name}")
        song_el.click()
        time.sleep(1.5)

        # 3. 点击AI 编辑按钮（popup触发）
        print("[EditorService] 点击「AI 编辑」...", flush=True)
        self._js_click_button_by_text("AI 编辑")
        time.sleep(1.5)

        # 4. 点击去AI 编辑器按钮（SPA导航）
        print("[EditorService] 点击「去 AI 编辑器」...", flush=True)
        self._js_click_button_by_text("去 AI 编辑器")
        time.sleep(5)

        # 验证是否进入编辑器
        if not (self.browser.page and 'playground' in self.browser.page.url):
            raise RuntimeError("未能进入编辑器页面")
        print("[EditorService] ✅ 歌曲已加载到编辑器", flush=True)

    # ── 项目重命名 ────────────────────────────────────────────────────────

    def rename_project(self, new_name: str):
        """重命名编辑器项目

        注意：JS的nativeSetter只改DOM显示值，不影响React内部状态。
        导出对话框读取的是React内部状态，导出后歌曲名仍为"新项目"。
        目前方案：导出后在「我的资产」页通过重命名修正。

        Args:
            new_name: 新名称
        """
        print(f"[EditorService] 重命名项目为: {new_name}", flush=True)
        self.browser.run_js("""
        document.querySelectorAll('input').forEach(function(inp) {
            if (inp.value === '新项目') {
                var s = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                s.call(inp, arguments[0]);
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                inp.dispatchEvent(new Event('change', {bubbles: true}));
            }
        });
        """, new_name)
        time.sleep(0.5)

    # ── 导出 ──────────────────────────────────────────────────────────────

    def export_song(
        self,
        song_name: str,
        export_mode: str = "并轨导出",
    ) -> bool:
        """导出歌曲到「我的资产」

        流程：禁用beforeunload → 点导出按钮内层span → 等弹窗
        → 确认导出（JS全事件链）→ 等跳转到资产页

        Args:
            song_name: 歌曲名（仅用于日志，导出名取React内部状态）
            export_mode: 导出模式，默认"并轨导出"

        Returns:
            bool: 导出是否成功（是否跳转到资产页）
        """
        print(f"[EditorService] 导出歌曲: {song_name}", flush=True)
        self._disable_beforeunload()

        # 1. 点击导出按钮（JS全事件链，比DrissionPage .click()可靠）
        print("[EditorService] 点击导出按钮...", flush=True)
        self._js_click_export_button()
        time.sleep(3)

        # 2. 确认弹窗已打开
        body = self.browser.page.ele('tag:body').text if self.browser.page else ""
        if '并轨导出' not in body and '轨道合并' not in body:
            print("[EditorService] ⚠️ 导出弹窗未检测到，尝试JS点击...", flush=True)
            self._js_click_button_by_text("导出")
            time.sleep(3)
            body = self.browser.page.ele('tag:body').text if self.browser.page else ""
            if '并轨导出' not in body:
                raise RuntimeError("导出弹窗未能打开")

        print("[EditorService] ✅ 导出弹窗已打开", flush=True)

        # 3. 修改导出对话框中禁用的歌名 input（2026-05-09 实测方案）
        # 必须启用disabled input，用nativeSetter改值，再dispatch事件
        print(f"[EditorService] 设置歌曲名: {song_name}", flush=True)
        self.browser.run_js("""
        document.querySelectorAll('input').forEach(function(inp) {
            if (inp.value === '新项目') {
                // 1. 启用禁用状态
                inp.disabled = false;
                inp.removeAttribute('disabled');
                // 2. 用 nativeSetter 改 React 内部值
                var s = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                s.call(inp, arguments[0]);
                // 3. 触发 React 事件
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                inp.dispatchEvent(new Event('change', {bubbles: true}));
            }
        });
        """, song_name)
        time.sleep(0.5)
        print("[EditorService] ✅ 歌曲名已设置", flush=True)

        # 4. 点击确认导出按钮
        print("[EditorService] 确认导出...", flush=True)
        confirmed = self._js_click_primary_export()
        if not confirmed:
            # 兜底：用find_element点
            confirm_btn = self.browser.find_element(_BTN_CONFIRM_EXPORT)
            if confirm_btn:
                confirm_btn.click()
                time.sleep(1)
        time.sleep(6)

        # 4. 等待导出完成（轮询"导出中"消失/URL跳转）
        for i in range(30):
            if not self.browser.page:
                time.sleep(3)
                continue
            body = self.browser.page.ele('tag:body').text
            if '导出中' not in body:
                time.sleep(2)
                break
            time.sleep(3)
        else:
            print("[EditorService] ⚠️ 导出监控超时", flush=True)

        url = self.browser.page.url if self.browser.page else "unknown"
        print(f"[EditorService] 导出完成. URL: {url}", flush=True)
        return 'assets' in url

    def _js_click_primary_export(self) -> bool:
        """用JS全事件链点击导出弹窗中的primary按钮"""
        self.browser.run_js("""
        document.querySelectorAll('button').forEach(function(b) {
            var t = b.textContent.trim();
            var c = b.className || '';
            if (t === '导出' && c.indexOf('primary') >= 0) {
                ['mousedown','mouseup','click'].forEach(function(type) {
                    b.dispatchEvent(new MouseEvent(type, {
                        bubbles: true, cancelable: true, view: window, button: 0
                    }));
                });
            }
        });
        """)
        return True

    def _js_click_export_button(self):
        """用JS全事件链点击导出按钮（data-audio-control-bar-button-type=export）"""
        self.browser.run_js("""
        var btn = document.querySelector(
            "[data-audio-control-bar-button-type='export']"
        );
        if (btn) {
            ['mousedown','mouseup','click'].forEach(function(type) {
                btn.dispatchEvent(new MouseEvent(type, {
                    bubbles: true, cancelable: true, view: window, button: 0
                }));
            });
        }
        """)

    # ── 我的资产操作 ──────────────────────────────────────────────────────

    def rename_asset_in_assets(self, old_name: str = "新项目", new_name: str = ""):
        """在「我的资产」页重命名作品

        通过三点菜单→重命名→输入新名称→确定 完成。

        Args:
            old_name: 当前名称（默认"新项目"）
            new_name: 新名称
        """
        if not new_name:
            return
        print(f"[EditorService] 重命名作品: {old_name} → {new_name}", flush=True)

        if not (self.browser.page and 'assets' in self.browser.page.url):
            self._navigate_to_assets_page()

        # 找到新增的作品卡片（有发行全曲标记的）
        cards = self.browser.page.eles(
            'xpath://div[contains(@class,"assetItemWrapper")]'
        ) if self.browser.page else []
        target_card = None
        for card in cards:
            card_text = card.text if hasattr(card, 'text') else ''
            if old_name in card_text and '发行全曲' in card_text:
                target_card = card
                break

        if not target_card:
            print("[EditorService] ⚠️ 未找到可重命名的作品", flush=True)
            return

        # 点击三点菜单图标
        menu_icon = target_card.ele(
            'xpath:.//*[@data-dropdown-trigger-id and contains(@class,"menuMoreWrapper")]//*[name()="svg"]'
        ) if hasattr(target_card, 'ele') else None
        if menu_icon:
            menu_icon.click()
            time.sleep(1.5)

        # 点击重命名
        self._js_click_element_by_text("重命名")
        time.sleep(1.5)

        # 填写新名称
        name_inputs = self.browser.page.eles('tag:input') if self.browser.page else []
        for inp in name_inputs:
            ph = (inp.attr('placeholder') or '').lower()
            if '名称' in ph or '项目' in ph or '重命名' in ph:
                inp.input(new_name)
                time.sleep(0.5)
                break

        # 点击确定
        confirm_btn = self.browser.find_element(_BTN_CONFIRM)
        if confirm_btn:
            confirm_btn.click()
            time.sleep(1)
            print(f"[EditorService] ✅ 已重命名为: {new_name}", flush=True)

    # ── 私有方法 ──────────────────────────────────────────────────────────

    def _disable_beforeunload(self):
        """禁用页面离开提示（beforeunload事件）"""
        try:
            self.browser.run_js("window.onbeforeunload = null;")
        except Exception:
            pass

    def _navigate_to_compose_page(self):
        """导航到作曲页（处理beforeunload弹窗）"""
        self._disable_beforeunload()
        try:
            self.browser.page.run_js(
                'window.location.href = "https://music.douyin.com/studio/create";'
            ) if self.browser.page else None
        except Exception:
            self.browser.navigate(
                "https://music.douyin.com/studio/create",
                wait_seconds=5,
            )
        # 处理可能残留的弹窗
        self._dismiss_alert()
        time.sleep(3)

    def _navigate_to_assets_page(self):
        """导航到「我的资产」页"""
        self._disable_beforeunload()
        try:
            self.browser.page.run_js(
                'window.location.href = "https://music.douyin.com/studio/assets";'
            ) if self.browser.page else None
        except Exception:
            self.browser.navigate(
                "https://music.douyin.com/studio/assets",
                wait_seconds=5,
            )
        self._dismiss_alert()
        time.sleep(3)

    def _dismiss_alert(self):
        """消除JS弹窗"""
        for _ in range(3):
            try:
                self.browser.page.run_cdp(
                    'Page.handleJavaScriptDialog', accept=True
                )
                time.sleep(0.5)
            except Exception:
                return

    def _js_click_button_by_text(self, text: str):
        """用JS dispatchEvent点击包含指定文本的按钮"""
        js = f"""
        document.querySelectorAll('button').forEach(function(b) {{
            if (b.textContent.trim() === '{text}') {{
                b.dispatchEvent(new MouseEvent('click', {{
                    bubbles: true, cancelable: true, view: window, button: 0
                }}));
            }}
        }});
        """
        self.browser.run_js(js)

    @staticmethod
    def _js_click_element_by_text(text: str) -> str:
        """生成JS：点击包含指定文本的元素"""
        return f"""
        document.querySelectorAll('button, div, span, a').forEach(function(el) {{
            if (el.textContent.trim() === '{text}') {{
                el.dispatchEvent(new MouseEvent('click', {{
                    bubbles: true, cancelable: true, view: window, button: 0
                }}));
            }}
        }});
        """

    # ── 完整流程（PublisherAgent 调用入口） ──────────────────────────────

    def edit_and_export(
        self,
        song,
        export_mode: str = "并轨导出",
    ) -> str:
        """完整编辑器流程：加载歌曲 → 导出到资产页

        注意：React 状态同步问题已解决（2026-05-09 实测）：
        导出对话框打开后，先启用禁用的input，用 nativeSetter 改值，
        再 dispatch React 事件，确保导出名正确。

        Args:
            song: Song 对象（需包含 title 和 music_assets）
            export_mode: 导出模式

        Returns:
            str: 资产页 URL（非下载路径，因为导出保存到平台资产而非本地）
        """
        song_name = song.title or "未命名歌曲"
        asset_name = (
            song.music_assets[0].name if song.music_assets else song_name
        )
        print(
            f"[EditorService] 🎵 完整编辑导出流程: {song_name}",
            flush=True,
        )

        # 1. 通过作曲页素材加载歌曲到编辑器
        self.enter_editor_via_song(asset_name or song_name)

        # 2. 尝试重命名项目（仅改变DOM显示，不影响React状态）
        self.rename_project(song_name)

        # 3. 导出
        success = self.export_song(song_name, export_mode)

        if success:
            assets_url = "https://music.douyin.com/studio/assets"
            print(
                f"[EditorService] ✅ 导出成功，作品在: {assets_url}",
                flush=True,
            )
            return assets_url
        else:
            error_msg = "导出失败，请检查浏览器状态"
            print(f"[EditorService] ❌ {error_msg}", flush=True)
            raise RuntimeError(error_msg)

    # ── 保留的旧方法（兼容清除引用） ──────────────────────────────────────

    def enter_editor(self):
        """[已废弃] 请使用 enter_editor_via_song() """
        raise NotImplementedError(
            "enter_editor() 已废弃，请使用 enter_editor_via_song(song_name)"
        )

    def add_music_asset(self, asset):
        """[已废弃] 编辑器素材Tab只支持本地文件上传，不支持AI作曲素材"""
        raise NotImplementedError(
            "add_music_asset() 已废弃: 编辑器素材Tab只支持本地文件上传\n"
            "正确路径: enter_editor_via_song(song_name) → 歌曲自动加载"
        )
