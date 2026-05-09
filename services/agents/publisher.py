"""发行 Agent - 后期制作与发布

PublisherAgent 负责 AI 歌曲的后期制作（编辑导出）和发布流程。
使用 EditorService 和 PublishService 完成浏览器自动化操作。
"""

import json
import time
from typing import Optional

from infrastructure.browser import BrowserCore
from models.song import Song, Lyrics, MusicAsset
from services.agents.base import BaseAgent
from services.editor_service import EditorService
from services.publish_service import PublishService


PUBLISHER_PROMPT = """你是抖音AI音乐发行专员，负责后期制作和发布"""


class PublisherAgent(BaseAgent):
    """抖音AI音乐发行 Agent，负责后期制作和发布。

    使用 EditorService 进行音频编辑和导出，
    使用 PublishService 完成歌曲发布流程。

    Attributes:
        editor_svc: AI编辑器服务实例。
        publish_svc: 发布服务实例。
    """

    def __init__(
        self,
        browser: BrowserCore,
        llm: Optional[object] = None,
    ):
        """初始化 PublisherAgent。

        Args:
            browser: BrowserCore 实例（需已调用 launch()）。
            llm: LLM 客户端实例。若为 None，使用默认 LLMClient() (DeepSeek)。
        """
        super().__init__(
            name="PublisherAgent",
            system_prompt=PUBLISHER_PROMPT,
            llm=llm,
        )
        self.editor_svc = EditorService(browser)
        self.publish_svc = PublishService(browser)

    def produce_and_release(
        self,
        song_data: dict,
        export_mode: str = "轨道合并",
    ) -> dict:
        """执行歌曲的后期制作和发布完整流程。

        从 song_data 中提取 blueprint 和 lyrics_text，
        构造 Song 对象（含 Lyrics 和 MusicAsset），
        调用 EditorService 进行编辑导出，
        再调用 PublishService 执行发布。

        Args:
            song_data: 歌曲数据字典，包含：
                - blueprint: dict，包含 title_hint、structure、asset_id 等
                - lyrics_text: str，歌词文本
            export_mode: 导出模式，"轨道合并" 或 "母带"（默认 "轨道合并"）

        Returns:
            dict: 包含以下键：
                - song: Song 对象
                - publish_info: PublishInfo 对象或 None
                - success: bool，整体是否成功
        """
        # ── 提取数据 ──────────────────────────────────────────────────────────
        blueprint = song_data.get("blueprint", {})
        lyrics_text = song_data.get("lyrics_text", "")

        print(
            "[PublisherAgent] 开始后期制作与发布流程...",
            flush=True,
        )
        print(
            f"[PublisherAgent] blueprint 概要: "
            f"{json.dumps(blueprint, ensure_ascii=False, default=str)[:200]}",
            flush=True,
        )

        # ── 构造 Song 对象 ────────────────────────────────────────────────────
        title = blueprint.get(
            "title_hint",
            f"AI歌曲_{int(time.time())}",
        )

        # 从 blueprint 获取 structure（用于 Lyrics）
        structure = {}
        raw_structure = blueprint.get("structure")
        if raw_structure:
            if isinstance(raw_structure, str):
                try:
                    structure = json.loads(raw_structure)
                except (json.JSONDecodeError, TypeError):
                    print(
                        "[PublisherAgent] ⚠️ structure 字段 JSON 解析失败，使用空结构",
                        flush=True,
                    )
                    structure = {}
            elif isinstance(raw_structure, dict):
                structure = raw_structure

        lyrics = Lyrics(
            raw_text=lyrics_text,
            structure=structure,
            is_refined=False,
        )

        # 构造 MusicAsset（从 blueprint 或 song_data 中提取素材信息）
        asset = MusicAsset(
            asset_id=blueprint.get("asset_id") or song_data.get("asset_id", ""),
            name=blueprint.get(
                "asset_name",
                f"AI音乐_{int(time.time())}",
            ),
            duration_seconds=blueprint.get("duration_seconds", 0.0),
        )

        song = Song(
            title=title,
            lyrics=lyrics,
            music_assets=[asset],
            audio_file_path="",
            cover_image_path="",
        )

        print(
            f"[PublisherAgent] 🎵 歌曲标题: {song.title}",
            flush=True,
        )
        print(
            f"[PublisherAgent] 📝 歌词长度: {len(lyrics_text)} 字符",
            flush=True,
        )
        print(
            f"[PublisherAgent] 🎹 素材: {asset.name} ({asset.asset_id})",
            flush=True,
        )

        # ── 编辑导出 ──────────────────────────────────────────────────────────
        try:
            file_path = self.editor_svc.edit_and_export(song, export_mode)
            song.audio_file_path = file_path
            print(
                f"[PublisherAgent] ✅ 编辑导出完成: {file_path}",
                flush=True,
            )
        except Exception as e:
            print(
                f"[PublisherAgent] ❌ 编辑导出失败: {e}",
                flush=True,
            )
            return {
                "song": song,
                "publish_info": None,
                "success": False,
            }

        # ── 发布 ──────────────────────────────────────────────────────────────
        try:
            publish_info = self.publish_svc.publish(song)
            print(
                f"[PublisherAgent] ✅ 发布完成: success={publish_info.success}",
                flush=True,
            )
        except Exception as e:
            print(
                f"[PublisherAgent] ❌ 发布失败: {e}",
                flush=True,
            )
            return {
                "song": song,
                "publish_info": None,
                "success": False,
            }

        print(
            "[PublisherAgent] ✅ 后期制作与发布流程全部完成",
            flush=True,
        )
        return {
            "song": song,
            "publish_info": publish_info,
            "success": True,
        }

    def review_release(self, publish_result: dict) -> bool:
        """检查发布结果是否成功。

        Args:
            publish_result: produce_and_release 返回的结果字典。

        Returns:
            bool: 发布成功（success == True）返回 True，否则返回 False。
        """
        success = publish_result.get("success") == True
        if success:
            print(
                "[PublisherAgent] ✅ 发布结果评估: 成功",
                flush=True,
            )
        else:
            print(
                "[PublisherAgent] ❌ 发布结果评估: 失败",
                flush=True,
            )
        return success
