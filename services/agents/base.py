"""AI Agent 基类。

所有 AI Agent 的基类，封装了 LLM 调用和 JSON 解析的通用逻辑。
"""

import json
import re
from typing import Optional

from infrastructure.llm_client import LLMClient


class BaseAgent:
    """所有 AI Agent 的基类。

    Attributes:
        name: Agent 名称，用于日志/调试标识。
        system_prompt: 系统提示词，定义 Agent 的角色和行为。
        llm: LLM 客户端实例。
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: Optional[LLMClient] = None,
    ):
        """初始化 BaseAgent。

        Args:
            name: Agent 名称。
            system_prompt: 系统提示词。
            llm: LLM 客户端实例。若为 None，则使用默认的 LLMClient() (DeepSeek)。
        """
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm if llm is not None else LLMClient()

    def _call_llm(self, user_prompt: str, temperature: float = 0.7) -> str:
        """调用 LLM 进行对话。

        Args:
            user_prompt: 用户提示词。
            temperature: 采样温度，默认 0.7。

        Returns:
            LLM 回复的文本内容。
        """
        return self.llm.chat(self.system_prompt, user_prompt, temperature)

    def _parse_json(self, text: str) -> dict:
        """带修复功能的 JSON 解析。

        处理以下常见 LLM 输出问题：
        1. ```json ... ``` 代码块包裹
        2. {{ }} 双大括号包裹（去掉外层括号）
        3. 尾部多余逗号（如 {"a": 1,} → {"a": 1}）
        4. 所有修复均失败时返回 {"raw": text, "decision": "error"} 兜底

        Args:
            text: 原始 LLM 输出文本。

        Returns:
            解析后的字典。若全部修复失败，返回错误兜底字典。
        """
        if not text or not isinstance(text, str):
            return {"raw": str(text) if text is not None else "", "decision": "error"}

        # 1. 尝试直接解析
        candidate = text.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # 2. 移除 ```json ... ``` 代码块包裹
        code_block_pattern = re.compile(
            r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL | re.IGNORECASE
        )
        m = code_block_pattern.match(candidate)
        if m:
            candidate = m.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 3. 处理 {{ }} 双大括号（LLM 有时会输出双大括号包裹的 JSON）
        if candidate.startswith("{{") and candidate.endswith("}}"):
            inner = candidate[2:-2].strip()
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                candidate = inner  # 继续尝试修复

        # 4. 处理尾部多余逗号（常见于 LLM 生成的 JSON）
        stripped = re.sub(r",\s*}", "}", candidate)
        stripped = re.sub(r",\s*]", "]", stripped)
        if stripped != candidate:
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                candidate = stripped

        # 5. 综合修复：先去掉代码块，再去掉双大括号，再去除尾部逗号
        #    部分 LLM 输出可能同时存在多种问题
        candidate = text.strip()
        m = code_block_pattern.match(candidate)
        if m:
            candidate = m.group(1).strip()
        if candidate.startswith("{{") and candidate.endswith("}}"):
            candidate = candidate[2:-2].strip()
        candidate = re.sub(r",\s*}", "}", candidate)
        candidate = re.sub(r",\s*]", "]", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # 6. 所有修复失败，返回兜底字典
        return {"raw": text, "decision": "error"}
