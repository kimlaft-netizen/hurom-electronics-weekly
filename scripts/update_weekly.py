import os, json, urllib.request, urllib.parse, xml.etree.ElementTree as ET, re
from datetime import datetime, timezone

FEEDS = [
 ("MOTOR","https://www.st.com/content/st_com/en/rss.html"),
 ("CIRCUIT","https://www.ti.com/rss/whatsnew.xml"),
]
KEYWORDS = ["motor","bldc","pmsm","sensorless","inverter","mosfet","gate driver","current sensing","power supply","mcu","embedded","appliance"]

def clean(s): return re.sub(r'<[^>]+>',' ',s or '').replace('&nbsp;',' ').strip()
def collect():
    out=[]
    for cat,url in FEEDS:
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            data=urllib.request.urlopen(req,timeout=15).read()
            root=ET.fromstring(data)
            for item in root.findall('.//item')[:30]:
                title=clean(item.findtext('title')); desc=clean(item.findtext('description')); link=clean(item.findtext('link'))
                hay=(title+' '+desc).lower()
                if any(k in hay for k in KEYWORDS):
                    out.append({'category':cat,'title':title[:150],'summary':desc[:260] or '공개 기술자료 업데이트','point1':'가전 적용 가능성 검토','point2':'회로/FW 영향 검토','url':link})
        except Exception as e: print('feed error',url,e)
    # Deduplicate, keep newest feed order. No invented content.
    seen=set(); items=[]
    for x in out:
        k=x['url'] or x['title']
        if k and k not in seen: seen.add(k); items.append(x)
    return items[:12]

items=collect()
with open('data/weekly.json','w',encoding='utf-8') as f:
    json.dump({'updated':datetime.now(timezone.utc).isoformat(),'items':items},f,ensure_ascii=False,indent=2)
