"""创意总监 Agent。

音乐创意总监角色，根据灵感生成歌曲设计方案（蓝图），并对蓝图进行质量审核。
"""

from services.agents.base import BaseAgent


CREATIVE_DIRECTOR_PROMPT = """你是抖音音乐平台的AI音乐创意总监，拥有10年专业经验。

## 角色与能力
- 你是一位资深的音乐创意总监，精通各类音乐风格（民谣、流行、电子、嘻哈、R&B、摇滚、国风等）
- 你擅长根据灵感快速生成完整、专业的歌曲设计方案
- 你对市场趋势有敏锐洞察，知道什么样的歌曲在抖音平台容易走红

## 输出要求
当你被要求生成歌曲蓝图时，请严格按照以下JSON格式输出（不要添加任何额外字段）：

{
    "title_hint": "歌曲标题建议（简洁有记忆点）",
    "genre": "音乐风格",
    "bpm": 节拍数（整数）,
    "key": "调式（如 C大调、Am小调）",
    "mood": "情感氛围描述",
    "instruments": ["乐器1", "乐器2", ...],
    "structure": ["段落1", "段落2", ...],
    "lyrics_theme": "歌词主题描述（要有画面感）",
    "style_description": "具体的风格描述（包含编曲特点、声音设计等）",
    "reference_emotion": "参考情感/情绪"
}

请确保你的输出专业、具体、有创意。"""


class CreativeDirectorAgent(BaseAgent):
    """音乐创意总监 Agent。

    负责根据灵感生成歌曲设计方案（蓝图），并对已有蓝图进行质量审核。
    """

    def __init__(self, llm=None):
        """初始化 CreativeDirectorAgent。

        Args:
            llm: LLM 客户端实例。若为 None，使用默认 LLMClient() (DeepSeek)。
        """
        super().__init__(
            name="CreativeDirector",
            system_prompt=CREATIVE_DIRECTOR_PROMPT,
            llm=llm,
        )

    def generate_blueprint(self, user_input: str = "") -> dict:
        """根据灵感生成歌曲设计方案蓝图。

        Args:
            user_input: 用户提供的灵感描述。若为空字符串，使用默认灵感：
                        "创作一首关于爱情遗憾的伤感民谣歌曲"

        Returns:
            包含歌曲设计蓝图的字典，字段包括：
            title_hint, genre, bpm, key, mood, instruments,
            structure, lyrics_theme, style_description, reference_emotion
        """
        if not user_input or not user_input.strip():
            user_input = "创作一首关于爱情遗憾的伤感民谣歌曲"

        user_prompt = f"""请根据以下灵感，生成一份完整的歌曲设计方案蓝图。

灵感描述：{user_input}

要求：
1. 选择适合AI生成的音乐风格（现代且可落地）
2. 设计清晰、合理的歌曲结构（如 intro, verse, chorus, bridge, outro 等）
3. 歌词主题要有画面感和故事性
4. 风格描述要具体，包含编曲特点、乐器搭配、声音设计方向
5. BPM和调式要符合所选风格的特征
6. 最终输出严格遵循系统提示词中要求的JSON格式

请直接输出JSON，不要包含任何额外解释。"""

        response = self._call_llm(user_prompt)
        return self._parse_json(response)

    def review_blueprint(self, blueprint: dict) -> dict:
        """审核歌曲设计方案蓝图的质量。

        检查维度：
        - 风格描述是否够具体（编曲特点、声音设计方向）
        - 乐器搭配是否合理（符合所选风格）
        - 歌词主题是否有画面感
        - 歌曲结构是否完整清晰
        - BPM 和调式是否符合风格特征

        Args:
            blueprint: 歌曲设计蓝图字典。

        Returns:
            审核结果字典，包含：
            - decision: "approve" 或 "revise"
            - reason: 审核结论的简要理由
            - suggestions: 改进建议列表
        """
        blueprint_str = str(blueprint)

        user_prompt = f"""请审核以下歌曲设计方案蓝图的质量。

蓝图内容：
{blueprint_str}

审核检查点：
1. 风格描述是否够具体？（有没有编曲特点、声音设计方向）
2. 乐器搭配是否合理？（是否符合所选风格）
3. 歌词主题是否有画面感和故事性？
4. 歌曲结构是否完整清晰？（intro, verse, chorus, bridge, outro 等是否合理）
5. BPM和调式是否符合所选风格特征？

请按以下JSON格式输出审核结果：
{{
    "decision": "approve" 或 "revise",
    "reason": "审核结论的简要理由",
    "suggestions": ["建议1", "建议2", ...]
}}

注意：
- 如果蓝图质量较高（至少4项检查点通过），decision 设为 "approve"
- 如果蓝图存在明显问题（2项及以上检查点不通过），decision 设为 "revise"
- 请给出具体、可操作的建议"""

        response = self._call_llm(user_prompt, temperature=0.3)
        return self._parse_json(response)
