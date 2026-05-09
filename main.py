#!/usr/bin/env python3
"""抖音音乐创作助手 — CLI 入口

用法:
    python main.py --list-tenants
    python main.py --login --tenant douyin_music_default
    python main.py --full --tenant douyin_music_default
"""

import argparse
import sys
import traceback

# ── 确保项目根目录在 sys.path 中 ───────────────────────────────────────────
from models.config import PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT))

# ── 导入业务模块 ────────────────────────────────────────────────────────────
from models.config import load_config, get_tenant
from pipelines import get_pipeline
from infrastructure.browser import BrowserCore


def list_tenants():
    """列出租户列表"""
    config = load_config()
    tenants = config.get("tenants", [])

    if not tenants:
        print("  没有配置任何租户", flush=True)
        return

    print(f"\n  共 {len(tenants)} 个租户:\n", flush=True)
    for t in tenants:
        enabled = "✅" if t.get("enabled") else "❌"
        tenant_id = t.get("id", "?")
        platform = t.get("platform", "?")
        account = t.get("account", "?")
        display = t.get("display_name", "")
        print(
            f"  {enabled} [{tenant_id}] "
            f"平台={platform}, 账号={account}"
            f"{f' ({display})' if display else ''}",
            flush=True,
        )
    print(flush=True)


def run_login(tenant_id: str):
    """仅执行登录（扫码持久化）

    Args:
        tenant_id: 租户 ID
    """
    print(f"\n  [Login] 开始登录流程 (租户: {tenant_id})", flush=True)

    config = load_config()
    tenant = get_tenant(tenant_id)
    if tenant is None:
        print(f"\n  ❌ 未找到租户: {tenant_id}", flush=True)
        sys.exit(1)

    if not tenant.platform_config:
        print(f"\n  ❌ 租户 {tenant_id} 未配置 platform_config", flush=True)
        sys.exit(1)

    studio_url = tenant.platform_config.studio_url
    chrome_data = tenant.platform_config.chrome_data
    chrome_port = tenant.config.chrome_port if tenant.config else 9223

    # 构建完整用户数据目录路径
    data_dir = f"data/douyin_music/default/{chrome_data}"

    if not studio_url:
        print(f"\n  ❌ 租户 {tenant_id} 未配置 studio_url", flush=True)
        sys.exit(1)
    if not chrome_data:
        print(f"\n  ❌ 租户 {tenant_id} 未配置 chrome_data", flush=True)
        sys.exit(1)

    print(
        f"  [Login] studio_url: {studio_url}",
        flush=True,
    )
    print(
        f"  [Login] chrome_data: {chrome_data}",
        flush=True,
    )

    browser = BrowserCore(user_data_dir=data_dir, port=chrome_port)
    try:
        # ── 启动浏览器 ─────────────────────────────────────────────────────
        browser.launch()

        # ── 导航到创作者平台 ───────────────────────────────────────────────
        browser.navigate(studio_url, wait_seconds=3)

        # ── 检查登录态 ─────────────────────────────────────────────────────
        import time
        time.sleep(5)  # 等待页面 SPA 完全加载（需等待 Vue/React 渲染）
        print("  [Login] 正在检查登录态...", flush=True)
        logged_in = browser.check_logged_in(browser.page.url)
        if logged_in:
            print(
                f"  [Login] ✅ 已处于登录状态，无需扫码",
                flush=True,
            )
        else:
            print(
                f"  [Login] 检测到未登录，等待扫码...",
                flush=True,
            )
            success = browser.wait_for_login(timeout=120)
            if success:
                print(
                    f"  [Login] ✅ 登录成功（Cookie 已持久化到用户数据目录）",
                    flush=True,
                )
            else:
                print(
                    f"  [Login] ❌ 登录超时",
                    flush=True,
                )
                sys.exit(1)
    finally:
        browser.cleanup()

    print(f"  [Login] ✅ 登录流程完成\n", flush=True)


def run_resume(tenant_id: str):
    """执行恢复创作流程（跳过 Phase 1&2，从 Phase 3 词曲创作开始）。

    Args:
        tenant_id: 租户 ID
    """
    print(f"\n  [Resume] 开始恢复创作流程 (租户: {tenant_id})", flush=True)
    print("  [Resume] 将跳过数据收集和创意策划阶段，直接进入词曲创作", flush=True)

    tenant = get_tenant(tenant_id)
    if tenant is None:
        print(f"\n  ❌ 未找到租户: {tenant_id}", flush=True)
        sys.exit(1)

    # ── 获取 Pipeline ──────────────────────────────────────────────────────
    print(f"  [Resume] 获取 Pipeline: music_creation", flush=True)
    pipeline = get_pipeline("music_creation", tenant)

    # ── 传递默认蓝图（跳过 Phase 1&2） ─────────────────────────────────────
    default_blueprint = {
        "title_hint": "未完成的信",
        "genre": "民谣",
        "mood": "怀念",
        "bpm": 80,
        "key": "C大调",
        "instruments": ["木吉他", "口琴", "钢琴"],
        "style_description": "民谣风格，木吉他为主，节奏舒缓，情感细腻",
        "lyrics_theme": (
            "创作一首关于爱情遗憾的民谣歌词，风格偏向伤感，"
            "包含'错过''回忆'等关键词，结构为主歌1→副歌→主歌2→副歌→桥段→副歌"
        ),
        "structure": ["verse1", "chorus", "verse2", "chorus", "bridge", "chorus"],
    }

    print(f"  [Resume] 使用默认蓝图: {default_blueprint['title_hint']}", flush=True)
    print(f"  [Resume] 开始执行 (Phase 3 → Phase 4)...\n", flush=True)

    try:
        result = pipeline.run(resume_blueprint=default_blueprint)
        stage = result.get("stage", "unknown")
        success = result.get("release_result", {}).get("success", False)
        status = "✅ 成功" if success else "❌ 失败"
        error = result.get("errors", [])
        print(f"\n  [Resume] 流程结束: 阶段={stage}, 状态={status}", flush=True)
        if error:
            print(f"  [Resume] 错误信息: {error}", flush=True)
    except Exception as e:
        print(f"\n  [Resume] ❌ 流程异常: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    print(f"  [Resume] ✅ 恢复创作流程结束\n", flush=True)


def run_full(tenant_id: str):
    """执行完整创作流程

    Args:
        tenant_id: 租户 ID
    """
    print(f"\n  [Full] 开始完整创作流程 (租户: {tenant_id})", flush=True)

    tenant = get_tenant(tenant_id)
    if tenant is None:
        print(f"\n  ❌ 未找到租户: {tenant_id}", flush=True)
        sys.exit(1)

    # ── 获取 Pipeline ──────────────────────────────────────────────────────
    print(f"  [Full] 获取 Pipeline: music_creation", flush=True)
    pipeline = get_pipeline("music_creation", tenant)

    # ── 执行 ──────────────────────────────────────────────────────────────
    print(f"  [Full] 开始执行...\n", flush=True)
    try:
        result = pipeline.run()
        stage = result.get("stage", "unknown")
        success = result.get("release_result", {}).get("success", False)
        status = "✅ 成功" if success else "❌ 失败"
        error = result.get("errors", [])
        print(f"\n  [Full] 流程结束: 阶段={stage}, 状态={status}", flush=True)
        if error:
            print(f"  [Full] 错误信息: {error}", flush=True)
    except Exception as e:
        print(f"\n  [Full] ❌ 流程异常: {e}", flush=True)
        sys.exit(1)

    print(f"  [Full] ✅ 完整创作流程结束\n", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="抖音音乐创作助手 — 自动化音乐创作与发布",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python main.py --list-tenants\n"
            "  python main.py --login --tenant douyin_music_default\n"
            "  python main.py --full --tenant douyin_music_default\n"
            "  python main.py --resume --tenant douyin_music_default\n"
        ),
    )

    parser.add_argument(
        "--list-tenants",
        action="store_true",
        help="列出所有租户",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="仅执行登录（扫码持久化 Cookie）",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="执行完整创作流程",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="恢复创作流程（跳过 Phase 1&2，从 Phase 3 词曲创作开始）",
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default="douyin_music_default",
        help="租户 ID（默认: douyin_music_default）",
    )

    args = parser.parse_args()

    # ── 加载配置（确保 .env 和 config.yaml 正确加载） ──────────────────────
    try:
        load_config()
    except FileNotFoundError as e:
        print(f"❌ {e}", flush=True)
        sys.exit(1)

    # ── 分发命令 ───────────────────────────────────────────────────────────
    if args.list_tenants:
        list_tenants()
    elif args.login:
        run_login(args.tenant)
    elif args.full:
        run_full(args.tenant)
    elif args.resume:
        run_resume(args.tenant)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
