"""测试Chromium连接"""
from DrissionPage import Chromium
import time
try:
    b = Chromium(9223)
    tab = b.get_tab()
    print("URL:", tab.url)
    print("Title:", tab.title)
    print("OK")
except Exception as e:
    print("ERR:", e)
