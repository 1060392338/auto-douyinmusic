"""
douyinmusic_opencli.py — 基于 OpenCLI 的抖音音乐自动化

替代方案: 原 DrissionPage/CDP 代码保留在备份中 (auto-douyinmusic.bak.*)
兜底: 可随时切回原方案

用法:
    python douyinmusic_opencli.py compose "一首关于夏天的歌"
    python douyinmusic_opencli.py export-all
"""

import time
import json
import sys
from opencli_bridge import OpenCLIBridge

# ── 配置 ──────────────────────────────────────────
STUDIO_URL = "https://music.douyin.com/studio"
CREATE_URL = "https://music.douyin.com/studio/create"
ASSETS_URL = "https://music.douyin.com/studio/assets/creation"
SESSION = "dm"


class DouyinMusicOpenCLI:
    """抖音音乐 OpenCLI 自动化"""

    def __init__(self, session: str = SESSION):
        self.cli = OpenCLIBridge(session=session, window="background")

    # ── 导航 ────────────────────────────────────────

    def go_studio(self) -> bool:
        """导航到创作实验室首页"""
        r = self.cli.open(STUDIO_URL)
        self.cli.wait_time(4)
        state = self.cli.state()
        return "music.douyin.com/studio" in state.get("data", "")

    def go_compose(self) -> bool:
        """导航到 AI 作曲页面"""
        self.go_studio()
        # 点击 "AI 作曲" 导航项
        state = self.cli.state()
        # 找 AI 作曲按钮索引
        import re
        match = re.search(r'\[(\d+)\].*AI 作曲', state.get("data", ""))
        if match:
            idx = int(match.group(1))
            self.cli.click(idx)
            self.cli.wait_time(3)
        else:
            # 直接 URL 导航作为 fallback
            self.cli.open(CREATE_URL)
            self.cli.wait_time(4)
        return True

    def go_assets(self) -> bool:
        """导航到我的资产页"""
        self.cli.open(ASSETS_URL)
        self.cli.wait_time(4)
        state = self.cli.state()
        return "assets" in state.get("data", "")

    def _get_song_names(self) -> set:
        """获取素材列表中所有歌曲名（通过 JS 查询 DOM，不依赖文本快照）"""
        result = self.cli.eval('''
        JSON.stringify(
            [...document.querySelectorAll('[class*="libraryItem"] p')]
                .map(p => p.textContent.trim())
                .filter(n => n.length > 0)
        )
        ''')
        raw = result.get("data", result.get("raw", "[]"))
        try:
            names = json.loads(raw)
        except json.JSONDecodeError:
            # 尝试从文本快照 fallback
            data = self.cli.state().get("data", "")
            import re
            idx = data.find("素材列表") if "素材列表" in data else 0
            section = data[idx:] if idx > 0 else data
            return set(
                (n, d) for n, d in re.findall(
                    r'<p>([^<]+)</p>.*?<span>(\d+:\d+)</span>', section, re.DOTALL
                )
            )
        return set(names)

    # ── 公共等待/统计 ───────────────────────────────

    def _wait_for_generation(self, timeout_steps=24, step_sec=5) -> bool:
        """等待 AI 作曲生成完成，返回是否成功"""
        for i in range(timeout_steps):
            self.cli.wait_time(step_sec)
            nav = self.cli.eval('''
            (() => {
                const el = [...document.querySelectorAll("[role=button]")]
                    .find(b => b.textContent.includes("AI 作曲"));
                const status = el?.closest("div")?.parentElement?.textContent || "";
                return status.includes("生成中") ? "生成中" : "done";
            })()
            ''')
            status = nav.get("data", nav.get("raw", "")).strip()
            if "done" in status:
                return True
            if i % 3 == 0:
                print(f"   ... {status} ({i*step_sec+step_sec}s)")
        return False

    def _collect_new_songs(self, songs_before: set) -> list:
        """对比生成前后的素材列表，返回新增歌曲 [(name, duration), ...]"""
        songs_now = self._get_song_names()
        return [(n, d) for n, d in songs_now if n not in songs_before][:4]

    # ── AI 作曲 ─────────────────────────────────────

    def compose_inspiration(self, prompt: str) -> dict:
        """灵感创作模式：输入提示词 → 点击生成 → 等待完成

        Returns: {"success": bool, "song_count": int, "songs": [str]}
        """
        print(f"🎵 AI 作曲: {prompt[:50]}...")
        # 直接导航到创作页
        self.cli.open(CREATE_URL)
        self.cli.wait_time(4)

        # 记录生成前的歌曲（用于后续对比）
        songs_before = self._get_song_names()

        # 1. 用原生 setter 注入提示词
        self.cli.eval(f'''
(() => {{
const el = document.querySelector('textarea[placeholder*="灵感"]');
const ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
ns.call(el, {json.dumps(prompt)});
el.dispatchEvent(new Event("input", {{bubbles: true}}));
el.dispatchEvent(new Event("change", {{bubbles: true}}));
return "typed " + el.value.length;
}})()
''')
        print(f"   📝 已输入: {prompt[:30]}...")
        self.cli.wait_time(2)

        # 2. 检查按钮状态并原生点击
        state_btn = self.cli.eval(
            'document.querySelector("[data-testid=create-song-button]").getAttribute("aria-disabled")'
        )
        btn_disabled = state_btn.get("data", state_btn.get("raw", "true"))
        if "true" in str(btn_disabled):
            return {"success": False, "error": "生成按钮未激活"}
        
        print("   🎹 点击生成...")
        self.cli.eval(
            'document.querySelector("[data-testid=create-song-button]").click(); "clicked"'
        )

        # 3. 等待生成完成
        print("   ⏳ 等待生成...")
        if not self._wait_for_generation():
            return {"success": False, "error": "生成超时"}

        # 4. 统计新歌
        new_songs = self._collect_new_songs(songs_before)

        return {
            "success": len(new_songs) > 0,
            "song_count": len(new_songs),
            "songs": [s[0] for s in new_songs],
            "durations": [s[1] for s in new_songs],
        }

    def compose_advanced(self, lyrics: str, style: str = "国风") -> dict:
        """高级模式：输入歌词+风格 → 生成

        Returns: 同 compose_inspiration
        """
        print(f"🎵 AI 作曲(高级): 风格={style}")
        self.go_compose()

        # 切换到高级模式
        self.cli.native_click('[data-testid="advanced-mode-button"]')
        self.cli.wait_time(2)

        # 输入歌词到 contenteditable div
        self.cli.eval(f"""
const el = document.querySelector('[data-testid=lyric-editor] [contenteditable=true]');
el.innerHTML = `<p>{lyrics.replace(chr(10), '<br>')}</p>`;
el.dispatchEvent(new Event('input', {{bubbles: true}}));
"""
        )
        self.cli.wait_time(1)

        # 输入风格
        style_selector = 'textarea[data-testid="style-prompt-textarea"]'
        self.cli.native_type(style_selector, style)
        self.cli.wait_time(1)

        # 点击生成
        print("   🎹 点击生成...")
        self.cli.native_click('[data-testid="create-song-button"]')

        # 等待生成
        print("   ⏳ 等待生成...")
        if not self._wait_for_generation(timeout_steps=12, step_sec=5):
            return {"success": False, "error": "生成超时"}

        # 统计结果（高级模式可能没有 before 对比，直接用素材列表）
        state = self.cli.state()
        data = state.get("data", "")
        import re
        mat_idx = data.find("素材列表")
        section = data[mat_idx:] if mat_idx > 0 else data
        songs = re.findall(r'<p>([^<]+)</p>.*?<span>(\d+:\d+)</span>', section, re.DOTALL)
        nav_items = {"首页", "素材", "我的资产", "AI 作词", "AI 作曲", "AI 编辑器", "知识库"}
        new_songs = [(n, d) for n, d in songs if n not in nav_items][:4]

        return {
            "success": len(new_songs) > 0,
            "song_count": len(new_songs),
            "songs": [s[0] for s in new_songs],
            "durations": [s[1] for s in new_songs],
        }

    # ── 导出 ────────────────────────────────────────

    def export_all_to_assets(self) -> dict:
        """导出素材列表中所有歌曲到资产页

        点击每首歌的导出按钮 → 等待完成
        """
        print("📦 批量导出到资产...")
        self.go_compose()

        # 滚动素材列表找到所有导出按钮
        state = self.cli.state()
        data = state.get("data", "")
        import re

        # 找素材区的按钮（播放按钮 + 更多按钮）
        # 先用 eval 批量导出
        result = self.cli.eval("""
(async () => {
    // 找到素材列表中的"更多"按钮并批量导出
    const moreButtons = document.querySelectorAll('[aria-haspopup=true][aria-expanded=false]');
    const items = [];
    for (const btn of moreButtons) {
        const card = btn.closest('[class*="material"], [class*="card"], [class*="item"]');
        if (!card) continue;
        const nameEl = card.querySelector('p');
        const name = nameEl ? nameEl.textContent : 'unknown';
        items.push({name, hasMoreBtn: true});
    }
    return JSON.stringify({count: items.length, items: items.slice(0, 10)});
})()
""")
        print(f"   📋 找到素材: {result.get('raw', result.get('data',''))}")

        # 具体导出逻辑：逐个点击更多 → 导出按钮
        # 这需要根据实际的DOM结构来精确操作
        # 暂时输出提示
        return {"success": False, "message": "导出逻辑待完成（需识别导出按钮 DOM 结构）"}


# ── CLI 入口 ───────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python douyinmusic_opencli.py <command> [args]")
        print("  compose <prompt>    — 灵感创作一首歌")
        print("  advanced <lyrics>   — 高级模式创作")
        print("  export-all          — 导出全部到资产")
        print("  test                — 连通性测试")
        sys.exit(1)

    cmd = sys.argv[1]
    dm = DouyinMusicOpenCLI()

    if cmd == "test":
        print("🔍 连通性测试...")
        if dm.go_studio():
            print("✅ 成功连接 music.douyin.com/studio")
        else:
            print("❌ 连接失败")
            sys.exit(1)

    elif cmd == "compose":
        if len(sys.argv) < 3:
            print("缺少提示词参数")
            sys.exit(1)
        prompt = " ".join(sys.argv[2:])
        result = dm.compose_inspiration(prompt)
        print(f"\n📊 结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    elif cmd == "advanced":
        lyrics = sys.argv[2] if len(sys.argv) > 2 else "清风拂面 夏日蝉鸣\n时光匆匆 岁月如歌"
        style = sys.argv[3] if len(sys.argv) > 3 else "国风"
        result = dm.compose_advanced(lyrics, style)
        print(f"\n📊 结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    elif cmd == "export-all":
        result = dm.export_all_to_assets()
        print(f"\n📊 结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
