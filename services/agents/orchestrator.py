"""主控 Agent - 音乐制作人角色。

OrchestratorAgent 统筹整个 AI 音乐创作工作流，
从数据收集、创意策划、词曲创作到制作发行，全流程管理和质量门禁。

核心设计：
  - 主控 Agent 使用 deepseek-v4-pro 模型（通过 llm 参数传入）
  - 子 Agent 使用 deepseek-chat 模型（通过 sub_llm 参数传入，更省钱）
  - 若 sub_llm 未传入，则所有子 Agent 复用主控的 llm
"""

import traceback
from typing import Optional

from infrastructure.browser import BrowserCore
from infrastructure.llm_client import LLMClient
from services.agents.base import BaseAgent
from services.agents.collector_analyst import CollectorAnalystAgent
from services.agents.creative_director import CreativeDirectorAgent
from services.agents.songwriter import SongwriterAgent
from services.agents.publisher import PublisherAgent
from services.collector_service import CollectorService


ORCHESTRATOR_PROMPT = """你是AI音乐制作人，统筹整个音乐创作工作流。

## 角色定位
- 你是一位经验丰富的音乐制作人，拥有10年行业经验
- 你负责统筹协调创作流程中的各个环节
- 你是质量门禁的把关者，确保每个环节的输出都达到专业水准
- 你根据市场趋势和数据洞察做出创作决策

## 工作职责
1. 数据分析：解读市场趋势报告，识别热门风格和创作方向
2. 创意把关：审核歌曲设计方案（蓝图），确保质量达标
3. 流程管理：协调词曲创作、制作发行各环节的有序推进
4. 质量门禁：在每个关键节点进行质量检查，不达标则要求返工

## 输出风格
- 专业、果断、有判断力
- 数据驱动决策，不凭感觉
- 对不合格的输出敢于说"不"，并给出改进方向
"""


class OrchestratorAgent(BaseAgent):
    """音乐制作人主控 Agent。

    统筹整个 AI 音乐创作工作流，从数据收集到最终发布的全流程管理。

    Attributes:
        browser: 浏览器核心实例，传递给需要浏览器的子 Agent。
        sub_llm: 子 Agent 使用的 LLM 客户端（省钱模式），
                 若为 None 则子 Agent 复用主控的 llm。
    """

    def __init__(
        self,
        browser: BrowserCore,
        llm: LLMClient,
        sub_llm: Optional[LLMClient] = None,
    ):
        """初始化 OrchestratorAgent。

        Args:
            browser: BrowserCore 实例（需已调用 launch() 启动浏览器）。
            llm: 主控 Agent 用的 LLM 客户端（deepseek-v4-pro）。
            sub_llm: 子 Agent 用的 LLM 客户端（deepseek-chat），
                     不传则全部复用 llm。
        """
        super().__init__(
            name="Orchestrator",
            system_prompt=ORCHESTRATOR_PROMPT,
            llm=llm,
        )
        self.browser = browser
        self.sub_llm = sub_llm or llm

        print("[OrchestratorAgent] 🎵 音乐制作人主控 Agent 初始化完成", flush=True)
        print(f"[OrchestratorAgent] 主控模型: {llm.model}", flush=True)
        print(f"[OrchestratorAgent] 子Agent模型: {self.sub_llm.model}", flush=True)

    # ── 公开方法 ────────────────────────────────────────────────────────────

    def run_full_workflow(
        self,
        user_input: str = "",
        resume_trend_report: Optional[dict] = None,
        resume_blueprint: Optional[dict] = None,
    ) -> dict:
        """执行完整的 AI 音乐创作工作流。

        分为 4 个阶段：
        Phase 1: 数据收集 —— 采集热歌榜数据并生成趋势报告
        Phase 2: 创意策划 —— 生成歌曲蓝图并质量审核
        Phase 3: 词曲创作 —— 根据蓝图创作歌词和作曲
        Phase 4: 制作发行 —— 后期制作并发布

        Args:
            user_input: 用户提供的灵感描述。若为空字符串，使用默认灵感。
            resume_trend_report: 若提供则跳过 Phase 1，直接使用该趋势报告。
            resume_blueprint: 若提供则跳过 Phase 2，直接使用该蓝图。

        Returns:
            dict: 工作流执行结果，包含以下字段：
                - stage: 最终完成的阶段名称
                - blueprint: 歌曲设计方案蓝图
                - trend_report: 市场趋势报告
                - song_data: 词曲创作结果
                - release_result: 制作发行结果
                - errors: 执行过程中的错误列表
        """
        print(f"\n{'='*70}", flush=True)
        print("  🎬 [OrchestratorAgent] 开始完整音乐创作工作流", flush=True)
        print(f"{'='*70}", flush=True)

        errors: list[str] = []
        stage = "init"
        blueprint = {}
        trend_report = {}
        song_data = {}
        release_result = {}

        # ── Phase 1: 数据收集 ──────────────────────────────────────────────
        if resume_trend_report:
            trend_report = resume_trend_report
            print(f"\n{'#'*70}", flush=True)
            print("  📊 Phase 1/4: 数据收集 —— [跳过] 使用已有趋势报告", flush=True)
            print(f"{'#'*70}", flush=True)
            print(f"    songs_collected: {trend_report.get('songs_collected', 0)}", flush=True)
            stage = "phase1_done"
        else:
            try:
                stage = "phase1_data_collection"
                print(f"\n{'#'*70}", flush=True)
                print("  📊 Phase 1/4: 数据收集 —— 市场趋势分析", flush=True)
                print(f"{'#'*70}", flush=True)

                collector_service = CollectorService(self.browser)
                analyst = CollectorAnalystAgent(
                    collector_service=collector_service,
                    llm=self.sub_llm,
                )
                trend_report = analyst.generate_trend_report()

                sample_size = trend_report.get("songs_collected", 0)
                print(f"\n[OrchestratorAgent] ✅ 趋势报告生成完成", flush=True)
                print(f"   采集歌曲数: {sample_size}", flush=True)

                analysis = trend_report.get("analysis", {})
                recommendations = analysis.get(
                    "actionable_recommendations",
                    [],
                )
                if recommendations:
                    print(f"   可操作建议 ({len(recommendations)} 条):", flush=True)
                    for i, rec in enumerate(recommendations, 1):
                        print(f"     {i}. {rec}", flush=True)

                stage = "phase1_done"

            except Exception as e:
                errors.append(f"Phase 1 数据收集失败: {type(e).__name__}: {e}")
                print(
                    f"[OrchestratorAgent] ❌ Phase 1 异常: {e}",
                    flush=True,
                )
                traceback.print_exc()
                # 使用空趋势报告继续后续流程
                trend_report = self._empty_trend_report()

        # ── Phase 2: 创意策划 + 质检 ───────────────────────────────────────
        if resume_blueprint:
            blueprint = resume_blueprint
            print(f"\n{'#'*70}", flush=True)
            print("  💡 Phase 2/4: 创意策划 —— [跳过] 使用已有蓝图", flush=True)
            print(f"{'#'*70}", flush=True)
            print(f"   标题: {blueprint.get('title_hint', 'N/A')}", flush=True)
            print(f"   风格: {blueprint.get('genre', 'N/A')}", flush=True)
            stage = "phase2_done"
        else:
            try:
                stage = "phase2_creative_planning"
                print(f"\n{'#'*70}", flush=True)
                print("  💡 Phase 2/4: 创意策划 —— 生成蓝图 + 质量审核", flush=True)
                print(f"{'#'*70}", flush=True)

                director = CreativeDirectorAgent(llm=self.sub_llm)

                # 显示趋势报告中的可操作建议
                analysis = trend_report.get("analysis", {})
                recommendations = analysis.get(
                    "actionable_recommendations",
                    [],
                )
                if recommendations:
                    print(f"\n[OrchestratorAgent] 📋 趋势报告建议:", flush=True)
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}", flush=True)

                # 生成蓝图
                print("\n[OrchestratorAgent] 🎨 正在生成歌曲设计方案...", flush=True)
                blueprint = director.generate_blueprint(user_input)
                print(f"[OrchestratorAgent] ✅ 蓝图生成完成", flush=True)
                print(f"   标题提示: {blueprint.get('title_hint', 'N/A')}", flush=True)
                print(f"   风格: {blueprint.get('genre', 'N/A')}", flush=True)
                print(f"   BPM: {blueprint.get('bpm', 'N/A')}", flush=True)

                # 质量审核，最多重试 2 次
                max_retries = 2
                for attempt in range(max_retries + 1):
                    print(
                        f"\n[OrchestratorAgent] 🔍 质量审核 (第 {attempt + 1} 次)...",
                        flush=True,
                    )
                    review = director.review_blueprint(blueprint)

                    decision = review.get("decision", "revise")
                    reason = review.get("reason", "无理由")
                    suggestions = review.get("suggestions", [])

                    print(f"   审核结果: {decision}", flush=True)
                    print(f"   理由: {reason}", flush=True)
                    if suggestions:
                        print(f"   改进建议:", flush=True)
                        for j, sug in enumerate(suggestions, 1):
                            print(f"     {j}. {sug}", flush=True)

                    if decision == "approve":
                        print(
                            "[OrchestratorAgent] ✅ 蓝图通过质量审核",
                            flush=True,
                        )
                        break

                    if attempt < max_retries:
                        print(
                            f"[OrchestratorAgent] 🔄 蓝图未通过，根据建议重新生成 "
                            f"(第 {attempt + 2} 次尝试)...",
                            flush=True,
                        )
                        # 带上审核建议重新生成
                        suggestions_text = "\n".join(
                            f"- {s}" for s in suggestions
                        ) if suggestions else "请改进整体质量"
                        enhanced_input = (
                            f"{user_input}\n\n"
                            f"【改进建议】\n{suggestions_text}\n\n"
                            f"请重点改进：{reason}"
                        )
                        blueprint = director.generate_blueprint(enhanced_input)
                    else:
                        print(
                            "[OrchestratorAgent] ⚠️ 蓝图多次审核未通过，"
                            "使用当前版本继续流程",
                            flush=True,
                        )

                stage = "phase2_done"

            except Exception as e:
                errors.append(f"Phase 2 创意策划失败: {type(e).__name__}: {e}")
                print(
                    f"[OrchestratorAgent] ❌ Phase 2 异常: {e}",
                    flush=True,
                )
                traceback.print_exc()
                # 使用默认蓝图继续
                if not blueprint:
                    director = CreativeDirectorAgent(llm=self.sub_llm)
                    blueprint = director.generate_blueprint(user_input)

        # ── Phase 3: 词曲创作 ──────────────────────────────────────────────
        try:
            stage = "phase3_song_creation"
            print(f"\n{'#'*70}", flush=True)
            print("  🎵 Phase 3/4: 词曲创作 —— 歌词 + 作曲", flush=True)
            print(f"{'#'*70}", flush=True)

            songwriter = SongwriterAgent(
                browser=self.browser,
                llm=self.llm,  # DeepSeek Pro 用于歌词创作
            )

            # 确保 blueprint 中有 lyrics_theme
            lyrics_theme = blueprint.get("lyrics_theme", "")
            if not lyrics_theme and user_input:
                print(
                    "[OrchestratorAgent] ⚠️ blueprint 缺少 lyrics_theme，"
                    "使用 user_input 代替",
                    flush=True,
                )
                blueprint["lyrics_theme"] = user_input

            song_data = songwriter.create_song(blueprint)

            # 质检：检查歌词长度
            lyrics_text = song_data.get("lyrics_text", "")
            lyrics_length = len(lyrics_text)
            print(
                f"[OrchestratorAgent] 📝 歌词长度: {lyrics_length} 字",
                flush=True,
            )

            # 如果歌词太短（少于 100 字），重做一次
            if lyrics_length < 100:
                print(
                    "[OrchestratorAgent] ⚠️ 歌词长度不足 100 字，重新创作...",
                    flush=True,
                )
                # 给 blueprint 添加一个提醒
                enhanced_blueprint = dict(blueprint)
                enhanced_blueprint["lyrics_theme"] = (
                    f"{blueprint.get('lyrics_theme', user_input or '未指定主题')}"
                    f"\n【注意】歌词需要完整、丰富，至少包含 2 段主歌和 2 段副歌，"
                    f"总字数不少于 200 字。"
                )
                song_data = songwriter.create_song(enhanced_blueprint)

                lyrics_text = song_data.get("lyrics_text", "")
                lyrics_length = len(lyrics_text)
                print(
                    f"[OrchestratorAgent] 📝 重做后歌词长度: {lyrics_length} 字",
                    flush=True,
                )

            # 确保 song_data 中有 blueprint 引用（PublisherAgent 依赖）
            if "blueprint" not in song_data or not song_data["blueprint"]:
                song_data["blueprint"] = blueprint

            stage = "phase3_done"

        except Exception as e:
            errors.append(f"Phase 3 词曲创作失败: {type(e).__name__}: {e}")
            print(
                f"[OrchestratorAgent] ❌ Phase 3 异常: {e}",
                flush=True,
            )
            traceback.print_exc()
            # 构造一个空的 song_data 占位
            song_data = {
                "lyrics_text": "",
                "style_prompt": "",
                "asset_id": "",
                "blueprint": blueprint,
            }

        # ── Phase 4: 制作发行 ──────────────────────────────────────────────
        # Phase 3 耗时较长（AI 作曲），登录可能已过期
        # 在进入编辑器前重新检查登录态
        self._ensure_session_before_phase4()

        try:
            stage = "phase4_production_release"
            print(f"\n{'#'*70}", flush=True)
            print("  🚀 Phase 4/4: 制作发行 —— 后期制作 + 发布", flush=True)
            print(f"{'#'*70}", flush=True)

            publisher = PublisherAgent(
                browser=self.browser,
                llm=self.sub_llm,
            )

            release_result = publisher.produce_and_release(song_data)

            # 检查发布结果
            success = release_result.get("success", False)
            if success:
                print(
                    "[OrchestratorAgent] ✅ 制作发行流程全部完成",
                    flush=True,
                )
            else:
                print(
                    "[OrchestratorAgent] ⚠️ 制作发行流程未完全成功",
                    flush=True,
                )

            stage = "phase4_done"

        except Exception as e:
            errors.append(f"Phase 4 制作发行失败: {type(e).__name__}: {e}")
            print(
                f"[OrchestratorAgent] ❌ Phase 4 异常: {e}",
                flush=True,
            )
            traceback.print_exc()
            release_result = {
                "song": None,
                "publish_info": None,
                "success": False,
            }

        # ── 汇总结果 ────────────────────────────────────────────────────────
        result = {
            "stage": stage,
            "blueprint": blueprint,
            "trend_report": trend_report,
            "song_data": song_data,
            "release_result": release_result,
            "errors": errors,
        }

        print(f"\n{'='*70}", flush=True)
        if errors:
            print(
                f"  [OrchestratorAgent] ⚠️ 工作流完成，存在 {len(errors)} 个错误",
                flush=True,
            )
            for i, err in enumerate(errors, 1):
                print(f"    {i}. {err}", flush=True)
        else:
            print(
                "  [OrchestratorAgent] ✅ 完整音乐创作工作流顺利完成！",
                flush=True,
            )
        print(f"  最终阶段: {stage}", flush=True)
        print(f"{'='*70}", flush=True)

        return result

    # ── 会话管理 ────────────────────────────────────────────────────────────

    def _ensure_session_before_phase4(self):
        """在进入 Phase 4 前检查并续期登录会话。

        Phase 3（AI 作曲）通常耗时较长（10-20 分钟），
        此期间登录会话可能过期。此方法在进入编辑器前重新验证登录态，
        若过期则导航到登录页等待扫码。
        """
        import time

        print("\n  [OrchestratorAgent] 🔍 Phase 3→4 会话检查...", flush=True)
        try:
            # 导航到工作室页面重新验证
            self.browser.navigate(
                "https://music.douyin.com/studio", wait_seconds=4
            )
            logged_in = self.browser.check_logged_in(self.browser.page.url)
            if logged_in:
                print(
                    "  [OrchestratorAgent] ✅ 会话有效，继续 Phase 4",
                    flush=True,
                )
                return

            print(
                "  [OrchestratorAgent] ⚠️ 会话已过期，弹出登录页等待扫码...",
                flush=True,
            )
            # 触发登录弹窗
            login_btn = self.browser.find_element(
                "xpath://button[contains(.,'登录')]"
            )
            if login_btn:
                login_btn.click()
                time.sleep(2)

            if self.browser.wait_for_login(timeout=120):
                print(
                    "  [OrchestratorAgent] ✅ 扫码登录成功，继续 Phase 4",
                    flush=True,
                )
            else:
                print(
                    "  [OrchestratorAgent] ⚠️ 登录超时，仍继续 Phase 4 "
                    "（可能失败）",
                    flush=True,
                )
        except Exception as e:
            print(
                f"  [OrchestratorAgent] ⚠️ 会话检查异常: {e}，继续 Phase 4",
                flush=True,
            )

    # ── 内部方法 ────────────────────────────────────────────────────────────

    @staticmethod
    def _empty_trend_report() -> dict:
        """返回空的趋势报告，用于 Phase 1 失败时的降级。"""
        return {
            "report_type": "trend_analysis",
            "source": "fallback_empty",
            "songs_collected": 0,
            "songs": [],
            "analysis": {
                "analysis_date": "",
                "sample_size": 0,
                "genre_distribution": {},
                "bpm_range": {"min": 0, "max": 0},
                "common_structures": [],
                "top_lyrical_themes": [],
                "mood_distribution": {},
                "production_tips": [],
                "actionable_recommendations": [],
            },
            "generated_at": "",
            "is_fallback": True,
        }
