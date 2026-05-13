"""音乐创作 Pipeline

实现完整的 AI 音乐创作工作流：
1. 启动/连接浏览器并确保登录态
2. 调用 OrchestratorAgent 执行全流程（数据收集 → 创意策划 → 词曲创作 → 制作发行）
3. 清理浏览器资源
"""

from typing import Optional

from infrastructure.browser import BrowserCore
from infrastructure.llm_client import LLMClient
from models.config import load_config
from pipelines import register
from pipelines.base import BasePipeline
from services.agents.orchestrator import OrchestratorAgent


@register("music_creation")
class MusicCreationPipeline(BasePipeline):
    """音乐创作 Pipeline。

    统筹浏览器启动、登录验证和完整创作工作流。
    使用多模型配置：
    - main_llm (deepseek-v4-pro): 主控 OrchestratorAgent
    - sub_llm (deepseek-v4-flash): 子 Agent（Collector/CreativeDirector/Songwriter）
    - pub_llm (deepseek-v4-pro): 专用发布 PublisherAgent
    """

    def __init__(self, tenant):
        """初始化 MusicCreationPipeline。

        Args:
            tenant: TenantConfig 实例，从 tenant.platform_config 读取浏览器配置。
        """
        super().__init__(tenant)
        pc = tenant.platform_config  # 注意不是 platform_config_obj！
        self.browser = BrowserCore(
            user_data_dir=f"data/douyin_music/default/{pc.chrome_data}",
            port=9223,
        )
        # 从 config.yaml 获取 LLM 配置
        raw_config = load_config()
        llm_cfg = raw_config.get("global", {}).get("llm", {})
        main_cfg = raw_config.get("global", {}).get("llm_main_agent", {})
        pub_cfg = raw_config.get("global", {}).get("llm_publisher", llm_cfg)  # 默认复用 llm
        self.llm = LLMClient(**llm_cfg)  # deepseek-v4-flash for sub-agents
        self.main_llm = LLMClient(**main_cfg)  # deepseek-v4-pro for orchestrator
        self.pub_llm = LLMClient(**pub_cfg)  # deepseek-v4-pro for publisher
        self.orchestrator = OrchestratorAgent(
            self.browser,
            self.main_llm,
            sub_llm=self.llm,
            pub_llm=self.pub_llm,
        )

    def _ensure_logged_in(self):
        """确保浏览器已登录抖音音乐创作平台。

        启动浏览器，导航到工作室页面，检查登录态。
        如果未登录，等待用户扫码登录。
        超时或失败会抛出 RuntimeError。

        Raises:
            RuntimeError: 浏览器未启动或登录失败/超时时抛出。
        """
        self.browser.launch()
        self.browser.navigate("https://music.douyin.com/studio")
        if not self.browser.check_logged_in(self.browser.page.url):
            if not self.browser.wait_for_login():
                raise RuntimeError("登录失败")

    def run(self, resume_blueprint: Optional[dict] = None) -> dict:
        """执行完整的音乐创作工作流。

        流程：
        1. 确保浏览器启动并登录
        2. 调用 OrchestratorAgent 执行 4 阶段工作流
        3. 清理浏览器资源

        Args:
            resume_blueprint: 若提供则跳过 Phase 1&2，直接从 Phase 3 开始。

        Returns:
            dict: 工作流执行结果，包含各阶段输出和错误信息。
        """
        self._ensure_logged_in()
        result = self.orchestrator.run_full_workflow(
            resume_blueprint=resume_blueprint,
        )
        self.browser.cleanup()
        return result
