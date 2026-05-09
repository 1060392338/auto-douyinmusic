"""采集工具服务。

封装对抖音音乐热歌榜的网页采集逻辑。
使用 BrowserCore 进行页面导航和数据提取。
"""

import time
from typing import Optional

from infrastructure.browser import BrowserCore


class CollectorService:
    """采集工具服务。

    负责导航到抖音音乐平台，尝试提取热歌榜数据。
    页面结构未知时优雅降级，不抛出异常。

    Attributes:
        browser: BrowserCore 实例，提供浏览器操控能力。
    """

    def __init__(self, browser: BrowserCore):
        """初始化 CollectorService。

        Args:
            browser: BrowserCore 实例，需已调用 launch() 或外部管理生命周期。
        """
        self.browser = browser

    # ── 公开方法 ────────────────────────────────────────────────────────────────

    def fetch_trending_chart(self, limit: int = 10) -> list[dict]:
        """采集抖音音乐热歌榜数据。

        导航到 https://music.douyin.com，尝试查找热歌榜区域并提取歌曲信息。
        每个元素包含 title, artist, genre, bpm, structure, mood, lyrics_snippet。
        采集失败时打印警告并返回空列表。

        Args:
            limit: 最多返回的歌曲数量，默认 10。

        Returns:
            list[dict]: 歌曲信息列表。采集失败则返回 []。
        """
        print("[CollectorService] 开始采集抖音音乐热歌榜...", flush=True)

        try:
            # 导航到抖音音乐首页
            self.browser.navigate("https://music.douyin.com", wait_seconds=5)

            # 等待页面充分加载
            time.sleep(2)

            # 尝试提取热歌榜数据
            songs = self._extract_trending_songs(limit)

            if not songs:
                # 主要提取方法失败，尝试备用提取
                songs = self._extract_trending_songs_fallback(limit)

            if songs:
                print(
                    f"[CollectorService] ✅ 成功采集 {len(songs)} 首热歌",
                    flush=True,
                )
                return songs[:limit]
            else:
                print(
                    "[CollectorService] ⚠️ 未找到热歌榜数据，页面结构可能已变更",
                    flush=True,
                )
                return []

        except Exception as e:
            print(
                f"[CollectorService] ⚠️ 采集热歌榜失败: {type(e).__name__}: {e}",
                flush=True,
            )
            return []

    # ── 提取方法 ────────────────────────────────────────────────────────────────

    def _extract_trending_songs(self, limit: int) -> list[dict]:
        """尝试从页面提取热歌榜数据（主方法）。

        尝试多种常见选择器来定位歌曲列表容器。

        Args:
            limit: 最多返回的歌曲数量。

        Returns:
            list[dict]: 提取到的歌曲列表，可能为空。
        """
        songs = []

        # 尝试多种可能的歌曲列表容器选择器
        container_selectors = [
            ".song-list",                    # 通用 class
            ".trending-list",                # 热歌榜 class
            ".hot-list",                     # 热门榜单 class
            ".music-list",                  # 音乐列表
            "[class*='song']",              # 含 song 的 class
            "[class*='trend']",             # 含 trend 的 class
            "[class*='hot']",               # 含 hot 的 class
            "[class*='rank']",              # 含 rank 的 class
            ".rank-list",                   # 榜单列表
            ".chart-list",                  # 榜单
        ]

        for selector in container_selectors:
            try:
                container = self.browser.find_element(selector)
                if container is not None:
                    songs = self._parse_song_items(container, limit)
                    if songs:
                        print(
                            f"[CollectorService] 使用选择器 '{selector}' 找到 {len(songs)} 首歌曲",
                            flush=True,
                        )
                        return songs
            except Exception:
                continue

        # 尝试通过页面中的所有链接/卡片元素来解析
        try:
            songs = self._parse_from_all_elements(limit)
            if songs:
                return songs
        except Exception:
            pass

        return songs

    def _extract_trending_songs_fallback(self, limit: int) -> list[dict]:
        """备用提取方法：通过 JavaScript 获取页面文本内容并尝试解析。

        Args:
            limit: 最多返回的歌曲数量。

        Returns:
            list[dict]: 提取到的歌曲列表，可能为空。
        """
        try:
            # 获取页面主要内容区域的文本
            body_text_js = "document.body.innerText.substring(0, 5000)"
            page_text = self.browser.run_js(body_text_js)

            if page_text:
                print(
                    f"[CollectorService] 备用提取获取到页面文本 ({len(page_text)} 字符)",
                    flush=True,
                )

            # 尝试从文本中解析歌曲标题和艺人
            songs = self._parse_text_for_songs(page_text, limit)
            if songs:
                print(
                    f"[CollectorService] 备用提取解析到 {len(songs)} 首歌曲",
                    flush=True,
                )
                return songs
        except Exception as e:
            print(
                f"[CollectorService] 备用提取失败: {type(e).__name__}: {e}",
                flush=True,
            )

        return []

    # ── 解析逻辑 ────────────────────────────────────────────────────────────────

    def _parse_song_items(self, container, limit: int) -> list[dict]:
        """从列表容器元素中解析出歌曲项列表。

        Args:
            container: 列表容器的页面元素。
            limit: 最多返回的歌曲数量。

        Returns:
            list[dict]: 解析后的歌曲列表。
        """
        songs = []
        try:
            # 尝试获取容器中的所有列表项
            items = container.eles("tag:li") or container.eles("tag:div")
            for item in items[:limit]:
                song = self._parse_single_item(item)
                if song and song.get("title"):
                    songs.append(song)
        except Exception:
            pass
        return songs

    def _parse_single_item(self, item) -> Optional[dict]:
        """从单个列表项元素中提取歌曲信息。

        Args:
            item: 单个歌曲列表项的页面元素。

        Returns:
            Optional[dict]: 歌曲信息字典，提取失败返回 None。
        """
        try:
            # 尝试获取标题和艺人文本
            title = self._safe_get_text(item, ".song-title, .song-name, "
                                          "h3, h4, [class*='title'], "
                                          "[class*='name'], a")
            artist = self._safe_get_text(item, ".artist, .singer, "
                                          ".author, [class*='artist'], "
                                          "[class*='singer'], "
                                          "[class*='author'], span")
        except Exception:
            return None

        if not title:
            return None

        # 构造标准格式的歌曲信息
        return {
            "title": title,
            "artist": artist or "未知艺人",
            "genre": "",       # 页面通常不直接展示流派
            "bpm": "",         # 页面通常不直接展示 BPM
            "structure": "",   # 页面通常不直接展示结构
            "mood": "",        # 页面通常不直接展示情感
            "lyrics_snippet": "",  # 页面通常不直接展示歌词片段
        }

    def _parse_from_all_elements(self, limit: int) -> list[dict]:
        """遍历页面所有链接元素，尝试提取歌曲信息。

        兜底方法：当所有结构化选择器都失效时使用。

        Args:
            limit: 最多返回的歌曲数量。

        Returns:
            list[dict]: 提取到的歌曲列表。
        """
        songs = []
        try:
            # 查找所有可能包含歌曲信息的链接
            links = self.browser.find_elements("a[href*='song'], "
                                                "a[href*='music'], "
                                                "a[href*='detail']")
            for link in links[:limit]:
                try:
                    text = link.text.strip()
                    if text and len(text) > 1:
                        songs.append({
                            "title": text,
                            "artist": "",
                            "genre": "",
                            "bpm": "",
                            "structure": "",
                            "mood": "",
                            "lyrics_snippet": "",
                        })
                except Exception:
                    continue
        except Exception:
            pass
        return songs

    def _parse_text_for_songs(self, page_text: str, limit: int) -> list[dict]:
        """从页面纯文本中尝试解析歌曲标题。

        使用简单的启发式规则从文本中提取可能的歌曲信息。

        Args:
            page_text: 页面的纯文本内容。
            limit: 最多返回的歌曲数量。

        Returns:
            list[dict]: 提取到的歌曲列表。
        """
        songs = []
        if not page_text:
            return songs

        lines = page_text.split("\n")
        for line in lines:
            line = line.strip()
            # 跳过空行和长度过短/过长的行
            if not line or len(line) < 2 or len(line) > 100:
                continue

            # 按常见分隔符尝试拆分艺人 - 歌曲
            for sep in [" - ", " – ", " — ", " · "]:
                if sep in line:
                    parts = line.split(sep, 1)
                    artist_part = parts[0].strip()
                    title_part = parts[1].strip()
                    if title_part and len(title_part) >= 2:
                        songs.append({
                            "title": title_part,
                            "artist": artist_part,
                            "genre": "",
                            "bpm": "",
                            "structure": "",
                            "mood": "",
                            "lyrics_snippet": "",
                        })
                        break

            if len(songs) >= limit:
                break

        # 如果上一步没找到，尝试把所有看起来像标题的短文本作为歌曲名
        if not songs:
            for line in lines:
                line = line.strip()
                # 2~30 个字符的非空行可能是歌曲标题
                if 2 <= len(line) <= 30 and self._looks_like_song_title(line):
                    songs.append({
                        "title": line,
                        "artist": "",
                        "genre": "",
                        "bpm": "",
                        "structure": "",
                        "mood": "",
                        "lyrics_snippet": "",
                    })
                    if len(songs) >= limit:
                        break

        return songs

    @staticmethod
    def _looks_like_song_title(text: str) -> bool:
        """启发式判断文本是否可能为歌曲标题。

        Args:
            text: 待判断的文本。

        Returns:
            bool: True 表示看起来像歌曲标题。
        """
        # 排除明显不是歌曲标题的行
        skip_keywords = [
            "首页", "热歌", "榜单", "搜索", "登录", "注册", "下载",
            "推荐", "歌单", "歌手", "我的", "设置", "关于",
            "抖音", "音乐", "热门", "排行", "更多",
        ]
        lower = text.lower()
        for kw in skip_keywords:
            if kw in lower or kw in text:
                return False

        # 排除纯数字、纯 URL 等
        if text.isdigit():
            return False
        if text.startswith("http"):
            return False
        if len(text) <= 1:
            return False

        return True

    @staticmethod
    def _safe_get_text(element, selector: str) -> str:
        """安全地从元素中提取文本。

        Args:
            element: 页面元素。
            selector: CSS 选择器。

        Returns:
            str: 提取到的文本，失败时返回空字符串。
        """
        try:
            sub = element.ele(selector)
            if sub is not None:
                return sub.text.strip()
        except Exception:
            pass
        return ""
