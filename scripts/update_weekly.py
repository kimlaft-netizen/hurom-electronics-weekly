import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

OUT = "data/weekly.json"
DAYS = 14
MAX_ITEMS = 20
MAX_PER_TOPIC = 1

# 휴롬 전장 실무 중심 검색어. 시장전망보다 기술/부품/설계 자료를 우선 수집한다.
QUERIES = [
    ("MOTOR", '(BLDC OR PMSM OR sensorless) (motor control OR motor driver OR FOC)'),
    ("CIRCUIT", '(MOSFET OR gate driver OR current sensing) (motor OR appliance OR inverter)'),
    ("FIRMWARE", '(MCU OR microcontroller) (motor control OR PWM OR ADC OR sensorless)'),
    ("CIRCUIT", '(AC DC OR DC DC OR flyback OR buck) (appliance OR motor) power supply'),
    ("APPLIANCE", '(juicer OR blender OR food processor OR kitchen appliance) (motor OR electronics OR inverter)'),
    ("PCB", '(Altium OR PCB artwork OR PCB layout) (design rules OR routing OR stackup OR signal integrity)'),
    ("PCB", '(PCB layout OR printed circuit board) (creepage OR clearance OR grounding OR thermal design)'),
    ("SMPS", '(SMPS OR flyback OR LLC OR buck converter) (design OR transformer OR compensation OR feedback)'),
    ("SMPS", '(switch mode power supply OR AC DC converter) (snubber OR MOSFET OR rectifier OR efficiency)'),
    ("EMI", '(EMI OR EMC) (PCB layout OR filter OR common mode choke OR conducted emissions)'),
    ("EMI", '(radiated emissions OR conducted emissions) (appliance OR SMPS OR motor drive)'),
    ("FIRMWARE", '(embedded C OR microcontroller firmware) (coding OR debugging OR unit test OR static analysis)'),
    ("FIRMWARE", '(STM32 OR Renesas OR Nuvoton OR Microchip) (firmware architecture OR bootloader OR watchdog OR RTOS)'),
]

# 시장조사, 투자, 자동차/산업용 초고전압 등 실무 관련성이 낮은 결과 제거
BLOCK_WORDS = [
    "market size", "market forecast", "market share", "growth trends", "industry report",
    "research report", "stock", "shares", "investment", "investor", "revenue forecast",
    "2030", "2031", "2032", "2033", "2034", "2035", "2036",
    "electric vehicle", "ev traction", "automotive traction", "charging station",
    "3.3kv", "6.5kv", "railway", "solar farm", "wind turbine", "data center",
    "web development", "mobile app", "cryptocurrency", "course promotion", "job vacancy",
]

POSITIVE = {
    "bldc": 10, "pmsm": 10, "sensorless": 12, "motor control": 9,
    "motor driver": 9, "foc": 10, "field oriented": 10, "bemf": 9,
    "current sensing": 8, "current sensor": 7, "gate driver": 7,
    "microcontroller": 6, "mcu": 6, "pwm": 6, "adc": 6,
    "flyback": 7, "buck": 6, "ac/dc": 6, "dc/dc": 6,
    "appliance": 5, "blender": 8, "juicer": 8, "food processor": 8,
    "stall": 9, "overcurrent": 8, "over current": 8, "emi": 8, "emc": 8,
    "altium": 12, "pcb artwork": 12, "pcb layout": 10, "design rules": 8,
    "routing": 6, "stackup": 8, "signal integrity": 8, "creepage": 8,
    "clearance": 8, "grounding": 7, "thermal design": 7,
    "smps": 12, "llc": 8, "transformer": 6, "compensation": 7,
    "feedback loop": 8, "snubber": 9, "conducted emissions": 10,
    "radiated emissions": 10, "common mode choke": 9, "filter": 5,
    "embedded c": 10, "bootloader": 9, "watchdog": 8, "rtos": 8,
    "static analysis": 8, "unit test": 7, "debugging": 6,
}

HEADERS = {"User-Agent": "Mozilla/5.0 (HUROM-Electronics-Weekly/3.0)"}


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()


def news_url(query):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"
    })


def parse_date(text):
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def source_from_title(title):
    parts = [p.strip() for p in title.rsplit(" - ", 1)]
    return parts[1] if len(parts) == 2 else ""


def base_title(title):
    return title.rsplit(" - ", 1)[0].strip()


def category_of(default, text):
    h = text.lower()
    if any(x in h for x in ["bldc", "pmsm", "sensorless", "motor control", "motor driver", "foc"]):
        return "MOTOR"
    if any(x in h for x in ["mosfet", "gate driver", "current sensing", "flyback", "buck", "power supply", "emi", "emc"]):
        return "CIRCUIT"
    if any(x in h for x in ["altium", "pcb artwork", "pcb layout", "routing", "stackup", "signal integrity", "creepage", "clearance"]):
        return "PCB"
    if any(x in h for x in ["smps", "llc", "flyback", "buck converter", "snubber", "transformer", "compensation"]):
        return "SMPS"
    if any(x in h for x in ["conducted emissions", "radiated emissions", "common mode choke", "emi", "emc"]):
        return "EMI"
    if any(x in h for x in ["microcontroller", "mcu", "firmware", "embedded c", "bootloader", "watchdog", "rtos", "pwm", "adc", "uart"]):
        return "FIRMWARE"
    return default


def relevance(text):
    h = text.lower()
    if any(word in h for word in BLOCK_WORDS):
        return -100
    return sum(weight for word, weight in POSITIVE.items() if word in h)


def topic_key(title):
    h = base_title(title).lower()
    # 동일 제품/기술 보도는 하나의 주제로 묶는다.
    tokens = re.findall(r"[a-z0-9]+", h)
    stop = {"new", "with", "for", "and", "the", "from", "into", "control", "controls",
            "launches", "introduces", "expands", "family", "system", "systems", "solution"}
    tokens = [t for t in tokens if t not in stop and len(t) > 2]
    return " ".join(tokens[:7])


def korean_summary(category, title):
    h = title.lower()
    if "sensorless" in h:
        return "센서리스 위치 추정과 기동 안정성 관련 기술입니다. 저속·고부하 조건의 BEMF 검출, 전류 샘플링 및 Stall 판단 관점에서 검토할 가치가 있습니다."
    if "bldc" in h or "pmsm" in h or "motor control" in h:
        return "BLDC/PMSM 모터 제어 관련 기술입니다. PWM 구성, 전류 피드백, 속도 안정성 및 보호 로직을 가전 모터 제어 관점에서 확인할 수 있습니다."
    if "microcontroller" in h or "mcu" in h:
        return "모터·전력 제어용 MCU 관련 기술입니다. PWM/ADC 자원, 연산 성능, 통신 인터페이스와 다중 모터 지원 여부를 비교 검토할 수 있습니다."
    if "gate driver" in h or "mosfet" in h:
        return "모터 구동 전력단 관련 기술입니다. Gate 구동 조건, 스위칭 손실, 발열, 보호 기능과 EMI/EMC 영향을 중심으로 검토할 수 있습니다."
    if "current" in h and ("sense" in h or "sensor" in h):
        return "전류 검출 관련 기술입니다. 측정 범위와 정확도, ADC 연계, 과전류 보호 및 부하 판단 적용성을 확인할 수 있습니다."
    if any(x in h for x in ["flyback", "buck", "power supply", "ac/dc", "dc/dc"]):
        return "가전 전원회로 관련 기술입니다. 토폴로지, 효율, 절연·보호 요구사항, BOM 및 EMI/EMC 영향을 비교 검토할 수 있습니다."
    if category == "PCB":
        return "PCB Artwork 및 회로 배치·배선 관련 기술입니다. Altium 설계 규칙, 전원·GND 경로, 절연거리, 발열, 신호 무결성과 양산 DFM 관점에서 검토할 수 있습니다."
    if category == "SMPS":
        return "SMPS 전원 설계 관련 기술입니다. 토폴로지 선정, 변압기·인덕터, 보상회로, MOSFET·정류부, Snubber, 효율·발열 및 보호회로 관점에서 검토할 수 있습니다."
    if category == "EMI":
        return "EMI/EMC 개선 관련 기술입니다. 전도·복사 노이즈 경로, 필터, Common Mode Choke, 접지, PCB Loop 면적과 모터·SMPS 스위칭 영향 관점에서 검토할 수 있습니다."
    if category == "FIRMWARE":
        return "마이컴 Firmware 설계·코딩 관련 기술입니다. Embedded C 구조, Driver/HAL 분리, 상태 머신, Interrupt, Watchdog, Bootloader, 디버깅 및 테스트 관점에서 검토할 수 있습니다."
    if category == "APPLIANCE":
        return "가전제품의 모터·전장 적용 동향입니다. 실제 사용 부하, 소비전력, 소음·진동 및 제어 기능 관점에서 참고할 수 있습니다."
    return "가전 전장 설계와 관련된 공개 기술자료입니다. 회로, 모터 제어, Firmware 및 제품 적용 관점에서 핵심 사양을 확인할 수 있습니다."


def check_points(category, title):
    h = title.lower()
    if category == "MOTOR":
        return ["기동 성공률·저속 안정성", "상전류·RPM·PWM Duty", "Stall·과전류·온도 보호"]
    if category == "CIRCUIT":
        return ["정격 전압·전류·발열", "효율·스위칭 손실·BOM", "보호회로·EMI/EMC"]
    if category == "PCB":
        return ["Altium DRC·Layer Stack·Net Class", "전원/GND·고전류·Gate Loop 배선", "Creepage·Clearance·발열·DFM"]
    if category == "SMPS":
        return ["토폴로지·Transformer·보상회로", "MOSFET·Diode·Snubber·효율", "OCP·OVP·OTP·절연·발열"]
    if category == "EMI":
        return ["전도/복사 Noise Source·Path", "CM Choke·X/Y Cap·접지·Shield", "PCB Loop·Switching Edge·Pre-scan"]
    if category == "FIRMWARE":
        return ["Embedded C·상태 머신·ISR", "Driver/HAL·통신·Bootloader", "Watchdog·정적분석·Unit Test"]
    return ["주방가전 적용 가능성", "부하·소음·소비전력", "기구·회로·FW 연계 영향"]


def rating(score):
    return 5 if score >= 28 else 4 if score >= 18 else 3


def collect():
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    candidates = []
    for default_cat, query in QUERIES:
        try:
            root = ET.fromstring(fetch(news_url(query)))
            for node in root.findall(".//item")[:40]:
                raw_title = clean(node.findtext("title"))
                desc = clean(node.findtext("description"))
                url = clean(node.findtext("link"))
                dt = parse_date(clean(node.findtext("pubDate")))
                text = raw_title + " " + desc
                score = relevance(text)
                if not raw_title or not url or score < 8 or (dt and dt < cutoff):
                    continue
                cat = category_of(default_cat, text)
                title = base_title(raw_title)
                candidates.append({
                    "category": cat,
                    "title": title[:180],
                    "source": source_from_title(raw_title),
                    "summary": korean_summary(cat, title),
                    "checkPoints": check_points(cat, title),
                    "rating": rating(score),
                    "url": url,
                    "published": dt.isoformat() if dt else "",
                    "_score": score,
                    "_topic": topic_key(raw_title),
                })
        except Exception as exc:
            print("source error:", query, repr(exc))

    # 동일 주제 기사는 관련도가 가장 높은 한 건만 선택한다.
    candidates.sort(key=lambda x: (x["_score"], x["published"]), reverse=True)
    selected, topic_counts, normalized_titles = [], {}, set()
    for item in candidates:
        norm = re.sub(r"\W+", "", item["title"].lower())[:150]
        topic = item["_topic"]
        if norm in normalized_titles or topic_counts.get(topic, 0) >= MAX_PER_TOPIC:
            continue
        normalized_titles.add(norm)
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        selected.append(item)
        if len(selected) >= MAX_ITEMS:
            break

    for item in selected:
        item.pop("_score", None)
        item.pop("_topic", None)
    return selected


def load_old():
    try:
        with open(OUT, encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {"items": []}


def main():
    items = collect()
    if not items:
        old_items = load_old().get("items", [])
        if old_items:
            print("No qualified new items; preserving existing", len(old_items), "items")
            return
        print("No qualified items and no prior issue available")
        return
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "issueTitle": "이번 주 가전 전장 기술 TOP " + str(len(items)),
        "items": items,
    }
    with open(OUT, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    print("Wrote", len(items), "curated items to", OUT)


if __name__ == "__main__":
    main()
