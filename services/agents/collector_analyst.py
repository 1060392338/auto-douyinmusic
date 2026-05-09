"""分析 Agent - 抖音爆款音乐趋势分析。

CollectorAnalystAgent 使用 CollectorService 采集热歌榜数据，
并通过 LLM 分析音乐趋势，生成结构化趋势报告。
"""

from datetime import date
from typing import Optional

from services.agents.base import BaseAgent
from services.collector_service import CollectorService


COLLECTOR_PROMPT = """你是抖音音乐平台的「爆款音乐趋势研究员」，拥有5年爆款音乐分析经验。

## 角色与能力
- 你精通抖音平台音乐流行趋势，对热歌榜数据有敏锐洞察力
- 你擅长从歌曲数据中提炼模式、发现规律、预测趋势方向
- 你熟悉各种音乐流派（民谣、流行、电子、嘻哈、R&B、摇滚、国风等）在抖音的表现特征
- 你能给出可落地的制作建议，帮助创作者打造下一首爆款

## 输出要求
当你被要求分析歌曲数据时，请严格按照以下JSON格式输出（不要添加额外字段）：

{
    "analysis_date": "YYYY-MM-DD",
    "sample_size": 0,
    "genre_distribution": {"流派名称": 占比(0~100的整数), ...},
    "bpm_range": {"min": 最小BPM, "max": 最大BPM},
    "common_structures": ["常见结构1", "常见结构2", ...],
    "top_lyrical_themes": ["主题1", "主题2", ...],
    "mood_distribution": {"情感1": 占比(0~100的整数), ...},
    "production_tips": ["制作建议1", "制作建议2", ...],
    "actionable_recommendations": ["可操作建议1", "可操作建议2", ...]
}

注意：
- genre_distribution 和 mood_distribution 中的占比总和应为 100
- 所有分析必须基于提供的歌曲数据，不要编造数据
- 当样本量不足时，如实标注并给出保守的分析结论"""


class CollectorAnalystAgent(BaseAgent):
    """抖音爆款音乐趋势分析 Agent。

    使用 CollectorService 采集热歌榜数据，通过 LLM 分析趋势模式，
    并生成结构化的趋势分析报告。

    Attributes:
        collector_service: 采集工具服务实例。
    """

    def __init__(
        self,
        collector_service: CollectorService,
        llm: Optional[object] = None,
    ):
        """初始化 CollectorAnalystAgent。

        Args:
            collector_service: CollectorService 实例，用于采集热歌榜数据。
            llm: LLM 客户端实例。若为 None，使用默认 LLMClient() (DeepSeek)。
        """
        super().__init__(
            name="CollectorAnalyst",
            system_prompt=COLLECTOR_PROMPT,
            llm=llm,
        )
        self.collector_service = collector_service

    # ── 公开方法 ────────────────────────────────────────────────────────────────

    def collect_trending_songs(self, limit: int = 10) -> list[dict]:
        """采集抖音热歌榜歌曲数据。

        委托 CollectorService 执行实际的页面采集工作。

        Args:
            limit: 最多采集的歌曲数量，默认 10。

        Returns:
            list[dict]: 歌曲信息列表，每个元素包含 title, artist 等字段。
                        采集失败时返回空列表。
        """
        print(
            f"[CollectorAnalystAgent] 开始采集热歌榜数据 (limit={limit})...",
            flush=True,
        )
        songs = self.collector_service.fetch_trending_chart(limit=limit)
        print(
            f"[CollectorAnalystAgent] 采集完成，获得 {len(songs)} 首歌曲数据",
            flush=True,
        )
        return songs

    def analyze_patterns(self, songs: list[dict]) -> dict:
        """分析歌曲数据中的趋势模式。

        将歌曲数据交给 LLM，使用 temperature=0.4 进行结构化分析。
        输出包含流派分布、BPM范围、常见结构、歌词主题、情感分布等。

        Args:
            songs: 要分析的歌曲信息列表。

        Returns:
            dict: 分析结果，包含以下字段：
                - analysis_date: 分析日期
                - sample_size: 样本数量
                - genre_distribution: 流派分布
                - bpm_range: BPM 范围
                - common_structures: 常见结构
                - top_lyrical_themes: 热门歌词主题
                - mood_distribution: 情感分布
                - production_tips: 制作建议
                - actionable_recommendations: 可操作建议
        """
        print(
            f"[CollectorAnalystAgent] 开始分析 {len(songs)} 首歌曲的趋势模式...",
            flush=True,
        )

        if not songs:
            print(
                "[CollectorAnalystAgent] ⚠️ 歌曲数据为空，返回空分析结果",
                flush=True,
            )
            return self._empty_analysis()

        # 构造歌曲数据的文本表示供 LLM 分析
        songs_text = self._format_songs_for_llm(songs)

        user_prompt = f"""请分析以下抖音热歌榜歌曲数据，识别趋势模式并给出分析报告。

歌曲数据（共 {len(songs)} 首）：
{songs_text}

请严格按 JSON 格式输出分析结果，包含：
- analysis_date: 今天的日期
- sample_size: 样本数量
- genre_distribution: 各流派占比
- bpm_range: BPM 最小值和最大值
- common_structures: 常见歌曲结构
- top_lyrical_themes: 热门歌词主题
- mood_distribution: 情感氛围分布
- production_tips: 制作建议（至少3条）
- actionable_recommendations: 可操作建议（至少3条）

注意：
- genre_distribution 和 mood_distribution 的占比总和应为 100
- 基于实际数据进行分析，不要编造"""
        response = self._call_llm(user_prompt, temperature=0.4)
        result = self._parse_json(response)

        # 如果解析结果中包含 raw 字段（解析失败），返回空分析
        if "raw" in result and "decision" in result:
            print(
                "[CollectorAnalystAgent] ⚠️ LLM 输出 JSON 解析失败，返回空分析",
                flush=True,
            )
            return self._empty_analysis()

        # 补充分析日期和样本量（防止 LLM 遗漏）
        if "analysis_date" not in result or not result["analysis_date"]:
            result["analysis_date"] = date.today().isoformat()
        if "sample_size" not in result or not result["sample_size"]:
            result["sample_size"] = len(songs)

        print(
            "[CollectorAnalystAgent] ✅ 趋势分析完成",
            flush=True,
        )
        return result

    def generate_trend_report(self) -> dict:
        """生成完整的趋势分析报告。

        采集 → 分析 的完整工作流。
        如果采集无数据或分析失败，使用 _default_report() 降级。

        Returns:
            dict: 趋势报告，包含采集和分析结果。
        """
        print(
            "[CollectorAnalystAgent] ====== 开始生成趋势报告 ======",
            flush=True,
        )

        # 1. 采集数据
        songs = self.collect_trending_songs(limit=10)

        # 2. 分析数据
        if songs:
            analysis = self.analyze_patterns(songs)
        else:
            print(
                "[CollectorAnalystAgent] ⚠️ 无歌曲数据，使用降级报告",
                flush=True,
            )
            return self._default_report()

        # 3. 构造完整报告
        report = {
            "report_type": "trend_analysis",
            "source": "douyin_music_trending_chart",
            "songs_collected": len(songs),
            "songs": songs,
            "analysis": analysis,
            "generated_at": date.today().isoformat(),
        }

        print(
            "[CollectorAnalystAgent] ✅ 趋势报告生成完成",
            flush=True,
        )
        return report

    # ── 降级方法 ────────────────────────────────────────────────────────────────

    def _default_report(self) -> dict:
        """生成降级趋势报告。

        当采集无数据或分析失败时，使用经验知识生成保守的降级报告。
        确保系统在任何情况下都能返回合理的结果。

        Returns:
            dict: 降级趋势报告。
        """
        print(
            "[CollectorAnalystAgent] 生成降级趋势报告（基于经验知识）",
            flush=True,
        )

        return {
            "report_type": "trend_analysis",
            "source": "fallback_knowledge",
            "songs_collected": 0,
            "songs": [],
            "analysis": {
                "analysis_date": date.today().isoformat(),
                "sample_size": 0,
                "genre_distribution": {
                    "流行 Pop": 35,
                    "嘻哈 Hip-Hop": 20,
                    "电子 Electronic": 15,
                    "R&B": 12,
                    "民谣 Folk": 10,
                    "国风 Chinese Style": 8,
                },
                "bpm_range": {"min": 70, "max": 140},
                "common_structures": [
                    "Intro - Verse - Chorus - Verse - Chorus - Bridge - Chorus - Outro",
                    "Verse - Chorus - Verse - Chorus - Outro",
                    "Intro - Verse - Pre-Chorus - Chorus - Verse - Chorus - Outro",
                ],
                "top_lyrical_themes": [
                    "爱情与遗憾",
                    "青春与成长",
                    "梦想与奋斗",
                    "生活感悟",
                    "友情与陪伴",
                ],
                "mood_distribution": {
                    "伤感": 30,
                    "励志": 25,
                    "欢快": 20,
                    "浪漫": 15,
                    "治愈": 10,
                },
                "production_tips": [
                    "流行歌曲建议 BPM 控制在 90-120 之间，搭配 4/4 拍",
                    "前奏控制在 8-16 秒内，快速进入主歌降低跳出率",
                    "副歌部分加入记忆点（hook），重复 2-3 次加强印象",
                    "使用干净的混音，人声靠前，适合短视频场景",
                    "结尾渐弱处理，适合短视频卡点混剪",
                ],
                "actionable_recommendations": [
                    "优先选择流行和嘻哈风格，目前在抖音平台热度最高",
                    "歌曲时长控制在 2:30-3:30，前15秒必须有亮点",
                    "歌词主题聚焦爱情和情感共鸣，易于引发用户评论互动",
                    "BPM 建议在 100-120 之间，适合舞蹈和卡点视频",
                    "副歌部分设计简单易记的旋律，降低用户翻唱门槛",
                ],
            },
            "generated_at": date.today().isoformat(),
            "is_fallback": True,
        }

    # ── 内部方法 ────────────────────────────────────────────────────────────────

    @staticmethod
    def _format_songs_for_llm(songs: list[dict]) -> str:
        """将歌曲数据格式化为 LLM 友好的文本表示。

        将结构化歌曲列表转换为易读的文本行，方便 LLM 理解。

        Args:
            songs: 歌曲信息列表。

        Returns:
            str: 格式化后的歌曲数据文本。
        """
        lines = []
        for i, song in enumerate(songs, 1):
            title = song.get("title", "未知标题")
            artist = song.get("artist", "未知艺人")
            genre = song.get("genre", "") or "未知风格"
            bpm = song.get("bpm", "") or "未知"

            lines.append(
                f"{i}. 《{title}》- {artist} | 风格: {genre} | BPM: {bpm}"
            )

        return "\n".join(lines) if lines else "（无数据）"

    @staticmethod
    def _empty_analysis() -> dict:
        """返回空数据分析结果。

        当歌曲数据为空时使用，返回基本分析框架。

        Returns:
            dict: 空分析结果。
        """
        return {
            "analysis_date": date.today().isoformat(),
            "sample_size": 0,
            "genre_distribution": {},
            "bpm_range": {"min": 0, "max": 0},
            "common_structures": [],
            "top_lyrical_themes": [],
            "mood_distribution": {},
            "production_tips": [],
            "actionable_recommendations": [],
        }
