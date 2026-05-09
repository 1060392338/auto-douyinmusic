"""LLM 客户端封装

基于 openai 包，统一对接 DeepSeek、OpenAI 以及兼容 OpenAI 接口的自定义服务（豆包等）。
API 密钥从环境变量读取，provider 和 model 等配置可由调用方传入，便于从 config.yaml 切换。
"""

import os
from typing import Optional

from openai import OpenAI


class LLMClient:
    """统一的 LLM 调用客户端。

    支持一键切换 provider/model，只需在实例化时传入不同参数即可。

    Attributes:
        provider: 服务提供商，如 "deepseek"、"openai" 或自定义名称。
        model: 模型名称，如 "deepseek-chat"、"gpt-4o" 等。
        temperature: 默认采样温度 (0.0 ~ 2.0)。
        max_tokens: 最大生成 token 数。
        client: OpenAI 客户端实例。
    """

    def __init__(
        self,
        provider: str = "deepseek",
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 3000,
    ):
        """初始化 LLM 客户端。

        Args:
            provider: 服务提供商，决定 base_url 和 api_key 来源。
            model: 模型名称，传递给 API 的 model 参数。
            temperature: 默认采样温度。
            max_tokens: 最大生成 token 数。
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = self._build_client()

    def _build_client(self) -> OpenAI:
        """根据 provider 构建 OpenAI 客户端。

        Provider 映射规则：
          - "deepseek": base_url=https://api.deepseek.com，api_key 从 DEEPSEEK_API_KEY 读取
          - "openai"  : base_url 使用默认值，api_key 从 OPENAI_API_KEY 读取
          - 其他      : base_url 从 LLM_BASE_URL 读取，api_key 从 LLM_API_KEY 读取

        Returns:
            OpenAI 客户端实例。

        Raises:
            ValueError: 缺少必要的 API 密钥或 base_url。
        """
        provider = self.provider

        if provider == "deepseek":
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError(
                    "环境变量 DEEPSEEK_API_KEY 未设置，无法初始化 DeepSeek 客户端"
                )
            return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "环境变量 OPENAI_API_KEY 未设置，无法初始化 OpenAI 客户端"
                )
            return OpenAI(api_key=api_key)

        else:
            # 自定义 provider（豆包等），兼容 OpenAI 接口
            api_key = os.environ.get("LLM_API_KEY")
            base_url = os.environ.get("LLM_BASE_URL")
            if not api_key:
                raise ValueError(
                    f"环境变量 LLM_API_KEY 未设置，无法初始化自定义 provider '{provider}'"
                )
            if not base_url:
                raise ValueError(
                    f"环境变量 LLM_BASE_URL 未设置，无法初始化自定义 provider '{provider}'"
                )
            return OpenAI(api_key=api_key, base_url=base_url)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> str:
        """统一的 LLM 对话接口。

        Args:
            system_prompt: 系统提示词，用于设定角色和行为。
            user_prompt: 用户提示词，即本次请求的实际指令/问题。
            temperature: 可选，覆盖实例化时设置的默认 temperature。

        Returns:
            模型回复的文本内容。

        Raises:
            openai.APIError: API 调用失败时抛出。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content
