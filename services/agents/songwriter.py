"""词曲 Agent。

抖音AI词曲作者，按蓝图创作歌词→去AI味→生成作曲提示词→驱动浏览器。
"""

from services.agents.base import BaseAgent
from infrastructure.browser import BrowserCore
from models.song import CompositionPrompt, Lyrics
from services.lyrics_service import LyricsService
from services.composition_service import CompositionService


SONGWRITER_PROMPT = """你是抖音AI词曲作者，精通歌词创作和音乐制作。

## 角色定位
- 你是一位专业的歌词作者和作曲人，擅长将歌曲蓝图转化为完整的歌词
- 你懂得如何去除AI生成的痕迹，让歌词听起来像人类创作
- 你能够为歌词生成专业的作曲风格描述，指导AI作曲

## 输出要求
当你被要求创作歌词时，请严格按照以下JSON格式输出（不要包含任何额外解释）：
{
    "lyrics_text": "完整的歌词文本，包含段落标记如【主歌1】、【副歌】等",
    "structure_notes": "歌词结构说明",
    "refined_version": "去除AI味后的精炼版本，语言更自然、押韵更和谐"
}

如果只需要精炼版本，请返回 refined_version 字段的内容。"""


class SongwriterAgent(BaseAgent):
    """抖音AI词曲作者 Agent。

    负责：LLM创作歌词 → 去除AI味 → 生成作曲提示词 → 驱动浏览器执行。
    """

    def __init__(self, browser: BrowserCore, llm=None):
        """初始化词曲 Agent。

        Args:
            browser: BrowserCore 实例（需已调用 launch() 启动浏览器）
            llm: LLM 客户端实例。若为 None，使用默认 LLMClient() (DeepSeek)。
        """
        super().__init__(
            name="Songwriter",
            system_prompt=SONGWRITER_PROMPT,
            llm=llm,
        )
        self.lyrics_svc = LyricsService(browser)
        self.composition_svc = CompositionService(browser)
        print("[SongwriterAgent] 词曲 Agent 初始化完成", flush=True)

    def create_lyrics(self, blueprint: dict) -> str:
        """LLM创作歌词，要求JSON输出，返回精炼版本。

        Args:
            blueprint: 歌曲设计蓝图字典，包含 lyrics_theme、genre、mood 等字段。

        Returns:
            str: 精炼后的歌词文本（refined_version），若没有则返回原始 lyrics_text。
        """
        theme = blueprint.get("lyrics_theme", "未指定主题")
        genre = blueprint.get("genre", "流行")
        mood = blueprint.get("mood", "温暖")
        title_hint = blueprint.get("title_hint", "")

        print(f"[SongwriterAgent] 🎤 开始创作歌词 - 主题: {theme}", flush=True)

        user_prompt = f"""请根据以下歌曲蓝图创作歌词。

歌曲蓝图：
- 标题提示：{title_hint}
- 风格：{genre}
- 情感氛围：{mood}
- 歌词主题：{theme}
- 推荐乐器：{blueprint.get('instruments', [])}
- 歌曲结构：{blueprint.get('structure', [])}

创作要求：
1. 歌词要贴合「{theme}」主题，富有画面感和故事性
2. 段落结构清晰（主歌、副歌、桥段等）
3. 押韵自然，朗朗上口
4. 符合 {genre} 风格的特点
5. refined_version 要去除AI味，让语言更自然、更有情感温度

请严格按照JSON格式输出：{{"lyrics_text": "...", "structure_notes": "...", "refined_version": "..."}}"""

        response = self._call_llm(user_prompt)
        parsed = self._parse_json(response)

        # 优先返回精炼版本，其次返回原始歌词文本
        refined = parsed.get("refined_version", "").strip()
        if refined:
            print(
                f"[SongwriterAgent] ✅ 歌词创作完成（精炼版本，{len(refined)} 字）",
                flush=True,
            )
            return refined

        lyrics_text = parsed.get("lyrics_text", "").strip()
        if lyrics_text:
            print(
                f"[SongwriterAgent] ✅ 歌词创作完成（原始版本，{len(lyrics_text)} 字）",
                flush=True,
            )
            return lyrics_text

        # 兜底：直接返回 LLM 原始输出
        print("[SongwriterAgent] ⚠️ 未能解析JSON，返回原始LLM输出", flush=True)
        return response.strip()

    def generate_style_prompt(self, blueprint: dict, lyrics_text: str) -> str:
        """用DeepSeek生成专业作曲风格描述。

        包含：乐器及演奏方式、节奏速度、段落情感递进、编曲变化。
        直接返回文本（不是JSON）。

        Args:
            blueprint: 歌曲设计蓝图字典。
            lyrics_text: 歌词文本。

        Returns:
            str: 专业作曲风格描述文本。
        """
        print("[SongwriterAgent] 🎵 开始生成作曲风格描述...", flush=True)

        genre = blueprint.get("genre", "流行")
        bpm = blueprint.get("bpm", 120)
        key = blueprint.get("key", "C大调")
        mood = blueprint.get("mood", "温暖")
        instruments = blueprint.get("instruments", [])
        style_desc = blueprint.get("style_description", "")

        user_prompt = f"""请根据以下歌曲蓝图和歌词，生成一份专业、详细的作曲风格描述。

歌曲蓝图：
- 风格：{genre}
- BPM：{bpm}
- 调式：{key}
- 情感氛围：{mood}
- 推荐乐器：{instruments}
- 风格描述参考：{style_desc}

歌词：
{lyrics_text}

请生成一份完整的作曲风格描述，包含以下要素（直接输出文本，不要JSON）：

1. 【乐器及演奏方式】推荐使用的乐器组合，以及每种乐器的演奏方式
   （如钢琴分解和弦、弦乐长音铺底、电吉他扫弦等）

2. 【节奏速度】基于BPM {bpm} 的节奏型描述，包括鼓点模式、节奏变化等

3. 【段落情感递进】根据歌词不同段落（主歌→副歌→桥段等），描述情感如何层层递进

4. 【编曲变化】整体编曲的起伏设计，包括引入、高潮、收尾的编曲层次变化

请确保描述专业、具体、可落地，直接输出文本内容，不要JSON格式。"""

        response = self._call_llm(user_prompt, temperature=0.5)
        style_prompt = response.strip()
        print(
            f"[SongwriterAgent] ✅ 作曲风格描述生成完成（{len(style_prompt)} 字）",
            flush=True,
        )
        return style_prompt

    def execute_lyrics_in_browser(self, lyrics_theme: str) -> str:
        """浏览器执行作词。

        Args:
            lyrics_theme: 歌词主题/灵感提示词。

        Returns:
            str: 浏览器生成的歌词文本。
        """
        print(
            f"[SongwriterAgent] 🌐 浏览器执行作词 - 主题: {lyrics_theme}",
            flush=True,
        )
        result = self.lyrics_svc.create_lyrics(lyrics_theme)
        lyrics_text = result.raw_text if hasattr(result, "raw_text") else str(result)
        print(
            f"[SongwriterAgent] ✅ 浏览器作词完成（{len(lyrics_text)} 字）",
            flush=True,
        )
        return lyrics_text

    def execute_composition_in_browser(
        self, style_prompt: str, lyrics_text: str
    ) -> str:
        """浏览器执行作曲。

        构造 CompositionPrompt，调用 compose_with_prompt()。

        Args:
            style_prompt: 专业作曲风格描述。
            lyrics_text: 歌词文本。

        Returns:
            str: 生成音乐的 asset_id。
        """
        print("[SongwriterAgent] 🌐 浏览器执行作曲...", flush=True)

        lyrics_obj = Lyrics(raw_text=lyrics_text, is_refined=False)
        prompt = CompositionPrompt(
            style_description=style_prompt,
            lyrics=lyrics_obj,
        )

        print(
            "[SongwriterAgent] 🎵 构造作曲提示词，调用 compose_with_prompt()...",
            flush=True,
        )
        asset = self.composition_svc.compose_with_prompt(prompt)
        asset_id = asset.asset_id
        print(
            f"[SongwriterAgent] ✅ 浏览器作曲完成 (asset_id: {asset_id})",
            flush=True,
        )
        return asset_id

    def create_song(self, blueprint: dict) -> dict:
        """完整词曲创作流程。

        流程：LLM写歌词 → LLM生成风格描述 → 浏览器作曲

        Args:
            blueprint: 歌曲设计蓝图字典。

        Returns:
            dict: {
                "lyrics_text": str,      # LLM创作的歌词文本
                "style_prompt": str,     # 生成的作曲风格描述
                "asset_id": str,         # 作曲生成的资产ID
                "blueprint": dict        # 原始蓝图
            }
        """
        print(f"\n{'='*60}", flush=True)
        print("  [SongwriterAgent] 🎬 开始完整词曲创作流程", flush=True)
        print(f"{'='*60}", flush=True)

        # Step 1: LLM创作歌词（DeepSeek Pro）
        print(f"\n{'─'*40}", flush=True)
        print("  Step 1/3: LLM创作歌词 (DeepSeek Pro)", flush=True)
        print(f"{'─'*40}", flush=True)
        lyrics_text = self.create_lyrics(blueprint)

        # Step 2: LLM生成作曲风格描述
        print(f"\n{'─'*40}", flush=True)
        print("  Step 2/3: LLM生成作曲风格描述", flush=True)
        print(f"{'─'*40}", flush=True)
        style_prompt = self.generate_style_prompt(blueprint, lyrics_text)

        # Step 3: 浏览器执行作曲（使用Step 1 LLM生成的歌词）
        print(f"\n{'─'*40}", flush=True)
        print("  Step 3/3: 浏览器执行作曲", flush=True)
        print(f"{'─'*40}", flush=True)
        asset_id = self.execute_composition_in_browser(style_prompt, lyrics_text)

        result = {
            "lyrics_text": lyrics_text,
            "style_prompt": style_prompt,
            "asset_id": asset_id,
            "blueprint": blueprint,
        }

        print(f"\n{'='*60}", flush=True)
        print("  [SongwriterAgent] ✅ 完整词曲创作流程完成", flush=True)
        print(f"  歌词长度: {len(lyrics_text)} 字", flush=True)
        print(f"  风格描述: {len(style_prompt)} 字", flush=True)
        print(f"  资产ID: {asset_id}", flush=True)
        print(f"{'='*60}", flush=True)

        return result
