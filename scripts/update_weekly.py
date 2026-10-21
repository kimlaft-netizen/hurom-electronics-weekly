import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

OUT = "data/weekly.json"
MAX_ITEMS = 12
DAYS = 14

# Google News RSS searches. These avoid relying on vendor RSS endpoints that may disappear.
QUERIES = [
    ("MOTOR", 'BLDC OR PMSM OR "sensorless motor" OR "motor control"'),
    ("CIRCUIT", 'MOSFET OR "gate driver" OR "current sensing" OR "power supply" electronics'),
    ("FIRMWARE", 'MCU firmware PWM ADC UART embedded motor'),
    ("APPLIANCE", 'appliance motor electronics inverter kitchen appliance'),
]

KEYWORDS = [
    "bldc", "pmsm", "sensorless", "motor control", "motor driver", "inverter",
    "mosfet", "gate driver", "current sensing", "current sensor", "power supply",
    "mcu", "microcontroller", "firmware", "pwm", "adc", "uart", "embedded",
    "appliance", "emi", "emc"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (HUROM-Electronics-Weekly/1.0)"}

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"\s+", " ", s)
    return s.replace("&nbsp;", " ").strip()

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def google_news_url(query):
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    })
    return "https://news.google.com/rss/search?" + params

def parse_date(text):
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def classify(default, title, desc):
    h = (title + " " + desc).lower()
    if any(k in h for k in ["bldc", "pmsm", "sensorless", "motor control", "motor driver"]):
        return "MOTOR"
    if any(k in h for k in ["mosfet", "gate driver", "current sensing", "power supply", "emi", "emc"]):
        return "CIRCUIT"
    if any(k in h for k in ["mcu", "microcontroller", "firmware", "pwm", "adc", "uart", "embedded"]):
        return "FIRMWARE"
    return default

def score(title, desc):
    h = (title + " " + desc).lower()
    return sum(2 if k in title.lower() else 1 for k in KEYWORDS if k in h)

def item_points(category):
    if category == "MOTOR": return "BLDC/PMSM 제어 관점 검토", "기동·전류·속도·보호 로직 확인"
    if category == "CIRCUIT": return "전원·구동·센싱 회로 관점 검토", "효율·보호·EMI/EMC 영향 확인"
    if category == "FIRMWARE": return "MCU/FW 제어 관점 검토", "PWM·ADC·통신·진단 로직 확인"
    return "가전제품 적용 가능성 검토", "전장·모터 시스템 영향 확인"

def collect():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    found = []
    for default_cat, query in QUERIES:
        url = google_news_url(query)
        try:
            root = ET.fromstring(fetch(url))
            for node in root.findall(".//item")[:30]:
                title = clean(node.findtext("title"))
                desc = clean(node.findtext("description"))
                link = clean(node.findtext("link"))
                pub = clean(node.findtext("pubDate"))
                dt = parse_date(pub)
                hay = (title + " " + desc).lower()
                if not title or not link or not any(k in hay for k in KEYWORDS):
                    continue
                if dt and dt < cutoff:
                    continue
                cat = classify(default_cat, title, desc)
                p1, p2 = item_points(cat)
                found.append({
                    "category": cat,
                    "title": title[:180],
                    "summary": (desc[:320] or "공개 기술자료 업데이트"),
                    "point1": p1,
                    "point2": p2,
                    "url": link,
                    "published": dt.isoformat() if dt else "",
                    "score": score(title, desc),
                })
        except Exception as e:
            print("source error:", query, repr(e))

    # Deduplicate primarily by normalized title; rank for engineering relevance then recency.
    seen, unique = set(), []
    for x in found:
        key = re.sub(r"\W+", "", x["title"].lower())[:120]
        if key and key not in seen:
            seen.add(key); unique.append(x)
    unique.sort(key=lambda x: (x["score"], x["published"]), reverse=True)
    for x in unique:
        x.pop("score", None)
    return unique[:MAX_ITEMS]

def load_old():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"items": []}

def main():
    items = collect()
    now = datetime.now(timezone.utc).isoformat()
    if not items:
        old = load_old()
        old_items = old.get("items", [])
        # Safety: never erase a previously useful weekly issue because a source is temporarily unavailable.
        if old_items:
            print("No new items; preserving existing", len(old_items), "items")
            return
        print("No items collected and no prior items available")
        return
    payload = {"updated": now, "items": items}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Wrote", len(items), "items to", OUT)

if __name__ == "__main__":
    main()
