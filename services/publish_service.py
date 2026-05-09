"""发布服务

提供歌曲发布的完整流程管理，包括：
- 导航到创作者工作室
- 填写歌曲信息（歌名、歌词）
- 生成封面
- 选择签约模式
- 签署协议（含验证码轮询等待，半自动模式）
- 最终发布
"""

import time

from infrastructure.browser import BrowserCore
from models.song import Song, PublishInfo, Lyrics


class PublishService:
    """歌曲发布服务

    管理从创作者工作室到最终发布的完整流程。
    签署协议环节采用半自动模式，由用户在浏览器窗口手动输入验证码，
    脚本轮询检测输入后自动点击"同意"。
    """

    # ── 常量 ──────────────────────────────────────────────────────────────────

    STUDIO_URL = "https://creator.douyin.com/"

    # 选择器
    SELECTOR_PUBLISH = 'xpath://button[contains(.,"发布全曲")]'
    SELECTOR_SONG_TITLE = 'xpath://input[contains(@placeholder,"歌名")]'
    SELECTOR_LYRICS = 'xpath://textarea[contains(@placeholder,"歌词")]'
    SELECTOR_GENERATE_COVER = 'xpath://button[contains(.,"生成封面")]'
    SELECTOR_CONFIRM = 'xpath://button[contains(.,"确认")]'
    SELECTOR_VERIFICATION_CODE = 'xpath://input[contains(@placeholder,"验证码")]'
    SELECTOR_AGREE = 'xpath://button[contains(.,"同意")]'
    SELECTOR_PUBLISH_BUTTON = 'xpath://button[contains(.,"发布")]'

    # 签署协议超时设置（秒）
    SIGN_TIMEOUT = 180          # 最长等待 3 分钟
    SIGN_POLL_INTERVAL = 30     # 每 30 秒打印一次提示

    # ── 初始化 ─────────────────────────────────────────────────────────────────

    def __init__(self, browser: BrowserCore):
        """初始化发布服务

        Args:
            browser: BrowserCore 实例，需已调用 launch() 启动浏览器
        """
        self.browser = browser

    # ── 核心流程方法 ───────────────────────────────────────────────────────────

    def navigate_to_studio(self):
        """导航到抖音创作者工作室"""
        print("[PublishService] 导航到创作者工作室...", flush=True)
        self.browser.navigate(self.STUDIO_URL, wait_seconds=5)
        print("[PublishService] ✅ 已到达创作者工作室", flush=True)

    def enter_publish(self):
        """点击「发布全曲」按钮进入发布页面"""
        print("[PublishService] 点击「发布全曲」...", flush=True)
        btn = self.browser.find_element(self.SELECTOR_PUBLISH)
        if btn:
            btn.click()
            time.sleep(2)
            print("[PublishService] ✅ 已进入发布页面", flush=True)
        else:
            print(
                "[PublishService] ⚠️ 未找到「发布全曲」按钮，可能已在发布页面",
                flush=True,
            )

    def fill_song_info(self, song: Song):
        """填写歌名和歌词

        Args:
            song: 歌曲数据模型，需包含 title 和 lyrics.raw_text
        """
        # ── 填写歌名 ──────────────────────────────────────────────────────────
        if song.title:
            print(f"[PublishService] 填写歌名: {song.title}", flush=True)
            title_input = self.browser.find_element(self.SELECTOR_SONG_TITLE)
            if title_input:
                title_input.input(song.title)
                print("[PublishService] ✅ 歌名已填写", flush=True)
            else:
                print("[PublishService] ⚠️ 未找到歌名输入框", flush=True)
        else:
            print("[PublishService] ℹ️ 歌曲标题为空，跳过", flush=True)

        # ── 填写歌词 ──────────────────────────────────────────────────────────
        lyrics_text = ""
        if song.lyrics:
            lyrics_text = song.lyrics.raw_text

        if lyrics_text:
            print("[PublishService] 填写歌词...", flush=True)
            lyrics_input = self.browser.find_element(self.SELECTOR_LYRICS)
            if lyrics_input:
                lyrics_input.input(lyrics_text)
                print("[PublishService] ✅ 歌词已填写", flush=True)
            else:
                print("[PublishService] ⚠️ 未找到歌词输入框", flush=True)
        else:
            print("[PublishService] ℹ️ 无歌词内容，跳过", flush=True)

        time.sleep(1)

    def generate_cover(self, song_name: str) -> str:
        """生成歌曲封面

        点击「生成封面」按钮 → 输入歌曲名 → 点击「确认」。
        如果找不到封面生成按钮，打印警告并返回空字符串。

        Args:
            song_name: 用于生成封面的歌曲名称

        Returns:
            str: 封面图片路径（本方法暂不追踪返回值，始终返回空串）
                 空字符串表示跳过封面生成或路径不可用
        """
        print("[PublishService] 尝试生成封面...", flush=True)

        btn = self.browser.find_element(self.SELECTOR_GENERATE_COVER)
        if not btn:
            print(
                "[PublishService] ⚠️ 未找到「生成封面」按钮，跳过封面生成",
                flush=True,
            )
            return ""

        # 点击「生成封面」
        btn.click()
        time.sleep(2)
        print("[PublishService] 已点击「生成封面」，等待弹窗...", flush=True)

        # 输入歌曲名（弹窗中可能包含输入框）
        if song_name:
            # 尝试多种常见 placeholder
            name_input = (
                self.browser.find_element(
                    'xpath://input[contains(@placeholder,"歌曲名")]'
                )
                or self.browser.find_element(
                    'xpath://input[contains(@placeholder,"名称")]'
                )
                or self.browser.find_element(
                    'xpath://input[contains(@placeholder,"歌名")]'
                )
            )
            if name_input:
                name_input.input(song_name)
                print(
                    f"[PublishService] 已输入歌曲名用于封面: {song_name}",
                    flush=True,
                )
            else:
                print(
                    "[PublishService] ℹ️ 未找到封面输入框，"
                    "使用封面 AI 默认生成方式",
                    flush=True,
                )

        # 点击「确认」
        confirm_btn = self.browser.find_element(self.SELECTOR_CONFIRM)
        if confirm_btn:
            confirm_btn.click()
            time.sleep(3)
            print("[PublishService] ✅ 封面生成已确认", flush=True)
        else:
            print(
                "[PublishService] ⚠️ 未找到「确认」按钮，"
                "封面生成弹窗可能已自动关闭",
                flush=True,
            )

        return ""

    def select_contract(self, contract_type: str = "独家代理发行5年"):
        """选择签约模式

        Args:
            contract_type: 签约模式名称，默认 "独家代理发行5年"
        """
        print(f"[PublishService] 选择签约模式: {contract_type}", flush=True)

        # 先尝试精确匹配按钮
        selector = f'xpath://button[contains(text(),"{contract_type}")]'
        btn = self.browser.find_element(selector)
        if btn:
            btn.click()
            time.sleep(1)
            print(f"[PublishService] ✅ 已选择签约模式: {contract_type}", flush=True)
            return

        # 降级：尝试匹配任意包含该文本的元素
        fallback_selector = f'xpath://*[contains(text(),"{contract_type}")]'
        elem = self.browser.find_element(fallback_selector)
        if elem:
            elem.click()
            time.sleep(1)
            print(
                f"[PublishService] ✅ 已选择签约模式（通用元素匹配）: "
                f"{contract_type}",
                flush=True,
            )
            return

        print(
            f"[PublishService] ⚠️ 未找到签约模式「{contract_type}」按钮，跳过",
            flush=True,
        )

    def sign_agreement(self) -> bool:
        """签署协议（半自动模式）

        核心逻辑：
        1. 打印醒目提示，通知用户在浏览器窗口中输入手机验证码
        2. 轮询等待验证码输入（最长 3 分钟，每 30 秒打印一次提示）
        3. 检测到验证码已输入后，点击「同意」按钮

        Returns:
            bool: True 表示协议签署完成，False 表示超时未完成
        """
        print(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  请在浏览器窗口中输入手机验证码以签署协议                    ║\n"
            "║  输入后脚本将自动检测并点击「同意」                          ║\n"
            "║  最长等待时间: 3 分钟                                       ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n",
            flush=True,
        )

        start_time = time.time()
        last_print = 0.0

        while time.time() - start_time < self.SIGN_TIMEOUT:
            elapsed = int(time.time() - start_time)

            # 查找验证码输入框并检测是否已填写
            code_input = self.browser.find_element(self.SELECTOR_VERIFICATION_CODE)
            if code_input:
                # DrissionPage 中 .value 返回输入框当前值
                code_value = code_input.value
                if code_value and code_value.strip():
                    print(
                        f"[PublishService] ✅ 检测到验证码已输入"
                        f"（等待 {elapsed} 秒）",
                        flush=True,
                    )
                    time.sleep(1)  # 短暂等待确保验证码完全输入

                    # 点击「同意」按钮
                    agree_btn = self.browser.find_element(self.SELECTOR_AGREE)
                    if agree_btn:
                        agree_btn.click()
                        time.sleep(2)
                        print(
                            "[PublishService] ✅ 已点击「同意」"
                            "，协议签署完成",
                            flush=True,
                        )
                        return True
                    else:
                        print(
                            "[PublishService] ⚠️ 未找到「同意」按钮"
                            "，请手动在浏览器中点击",
                            flush=True,
                        )
                        return True  # 验证码已填，允许手动处理

            # 每 30 秒打印一次提示
            if elapsed - last_print >= self.SIGN_POLL_INTERVAL:
                remaining = self.SIGN_TIMEOUT - elapsed
                print(
                    f"[PublishService] 等待验证码输入... "
                    f"已等待 {elapsed} 秒，剩余 {remaining} 秒",
                    flush=True,
                )
                last_print = elapsed

            time.sleep(1)

        # 超时
        print(
            f"[PublishService] ❌ 等待验证码超时"
            f"（{self.SIGN_TIMEOUT} 秒），协议签署未完成",
            flush=True,
        )
        return False

    # ── 完整发布流程 ───────────────────────────────────────────────────────────

    def publish(self, song: Song) -> PublishInfo:
        """执行完整发布流程（含异常处理）

        依次执行：导航 → 进入发布 → 填写信息 → 生成封面 → 选择签约
        → 签署协议 → 点击发布。

        Args:
            song: 待发布的歌曲数据模型

        Returns:
            PublishInfo:
                - success=True  发布流程执行成功
                - success=False 发布流程发生异常，error 字段包含错误描述
        """
        publish_info = PublishInfo(
            song_title=song.title,
            lyrics_text=song.lyrics.raw_text if song.lyrics else "",
        )

        print(
            "\n"
            "══════════════════════════════════════════════════════════════\n"
            "  开始发布歌曲\n"
            f"  歌曲: {song.title}\n"
            "══════════════════════════════════════════════════════════════\n",
            flush=True,
        )

        try:
            # 1. 导航到工作室
            self.navigate_to_studio()

            # 2. 进入发布页面
            self.enter_publish()

            # 3. 填写歌曲信息（歌名 + 歌词）
            self.fill_song_info(song)

            # 4. 生成封面
            cover_path = self.generate_cover(song.title)
            if cover_path:
                publish_info.cover_image_path = cover_path

            # 5. 选择签约模式
            self.select_contract()

            # 6. 签署协议（半自动验证码）
            self.sign_agreement()

            # 7. 点击「发布」按钮
            print("[PublishService] 点击「发布」按钮...", flush=True)
            publish_btn = self.browser.find_element(self.SELECTOR_PUBLISH_BUTTON)
            if publish_btn:
                publish_btn.click()
                time.sleep(3)
                print("[PublishService] ✅ 发布请求已提交", flush=True)
                publish_info.publish_url = self.browser.page.url
                publish_info.success = True
            else:
                print(
                    "[PublishService] ⚠️ 未找到「发布」按钮"
                    "，请手动在浏览器中完成发布",
                    flush=True,
                )
                publish_info.success = False

            print(
                "\n"
                "══════════════════════════════════════════════════════════════\n"
                "  ✅ 歌曲发布流程完成\n"
                "══════════════════════════════════════════════════════════════\n",
                flush=True,
            )

        except Exception as e:
            error_msg = str(e)
            print(
                f"[PublishService] ❌ 发布流程异常: {error_msg}",
                flush=True,
            )
            publish_info.success = False
            publish_info.error = error_msg

        return publish_info
