"""提取 work_id 并直接导航到发布表单"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)

# 用 CDP 提取蝉声漫旧夏卡片的 data-work-id
result = P.run_cdp('Runtime.evaluate', expression="""
(function() {
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for (var i = 0; i < cards.length; i++) {
        if (cards[i].textContent.indexOf('蝉声漫旧夏') >= 0) {
            return JSON.stringify({
                workId: cards[i].getAttribute('data-work-id'),
                title: cards[i].getAttribute('data-title'),
                outerHTML: cards[i].outerHTML.substring(0, 500)
            });
        }
    }
    return 'NOT_FOUND';
})();
""")
print(f"CDP result: {result}", flush=True)

import json
try:
    info = json.loads(result.get('result', {}).get('result', {}).get('value', '{}'))
    work_id = info.get('workId', '')
    print(f"work_id: {work_id}", flush=True)
    
    if work_id:
        # 直接导航到发布表单
        publish_url = f'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId={work_id}'
        print(f"导航到: {publish_url}", flush=True)
        P.run_js(f"window.onbeforeunload=null;window.location.href='{publish_url}';")
        time.sleep(8)
        
        body = P.ele('tag:body').text
        print(f"发布表单文本 (len={len(body)}):", flush=True)
        print(body[:3000], flush=True)
        
        # 检查关键元素
        for kw in ['下一步', '歌曲信息', '授权', '上传', '封面', '艺人', '签约', '合同']:
            print(f"  {kw}: {'✅' if kw in body else '❌'}", flush=True)
except Exception as e:
    print(f"解析失败: {e}", flush=True)
