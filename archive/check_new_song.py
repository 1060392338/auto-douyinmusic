"""检查作曲页是否有新生成的歌曲"""
from DrissionPage import ChromiumPage
import time
P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
time.sleep(2)
for _ in range(5):
    try: P.handle_alert(accept=True); time.sleep(0.3)
    except: break
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create';")
time.sleep(6)
body = P.ele("tag:body").text
known = ["缓歌寄意","杂乱思绪","无章","无序歌","星落肩头","空白页",
         "纸鸢远","夏蝉语","迷音","巷尾琴音","木吉他叙旧","吉他与诗","欢歌寄意",
         "AChq","首页","素材","我的资产","自由创作","AI 作词","AI 作曲","AI 编辑器","知识库"]
parts = body.split("Sway v5.5")
for p in parts:
    for line in p.strip().split("\n"):
        line = line.strip()
        if line and line not in known and 2 <= len(line) <= 6 and not any(c.isdigit() for c in line):
            print(f"NEW_SONG={line}")
