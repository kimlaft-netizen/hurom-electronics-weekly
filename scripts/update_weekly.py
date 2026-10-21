import os, re, json, html, hashlib
import urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

OUT='data/weekly.json'; DAYS=60; MAX_ITEMS=30; MIN_ITEMS=30
UA={'User-Agent':'Mozilla/5.0 HUROM-Electronics-Weekly/4.0'}

# 여러 출처를 각각 검색한다. Google News는 통합 색인으로 사용하고,
# NAVER_CLIENT_ID/SECRET이 있으면 네이버 뉴스 API 결과도 직접 합친다.
SOURCE_QUERIES=[
 ('ETNEWS','site:etnews.com (반도체 OR 회로 OR 모터 OR 전원 OR 펌웨어 OR PCB OR EMI)'),
 ('e4ds','site:e4ds.com (BLDC OR MCU OR SMPS OR PCB OR EMI OR 전력반도체)'),
 ('ROHM','site:rohm.co.kr (모터드라이버 OR MOSFET OR 전원 IC OR MCU OR 기술자료)'),
 ('ST','site:st.com (BLDC OR PMSM OR motor control OR STM32 OR power supply)'),
 ('TI','site:ti.com (motor control OR gate driver OR current sensing OR power supply)'),
 ('Infineon','site:infineon.com (motor control OR MOSFET OR PSoC OR gate driver)'),
 ('Renesas','site:renesas.com (motor control OR MCU OR inverter OR firmware)'),
 ('NXP','site:nxp.com (motor control OR MCU OR power management)'),
 ('onsemi','site:onsemi.com (motor driver OR MOSFET OR power supply)'),
 ('Microchip','site:microchip.com (motor control OR embedded C OR MCU OR SMPS)'),
 ('Altium','site:resources.altium.com (PCB layout OR stackup OR routing OR EMC)'),
 ('ALL','(BLDC OR PMSM OR sensorless OR SMPS OR PCB layout OR embedded C OR EMI EMC) appliance'),
 ('PCB2','(PCB design OR PCB routing OR grounding OR creepage clearance OR thermal design) electronics'),
 ('POWER','(power electronics OR AC DC OR DC DC OR flyback OR buck OR LLC) design'),
 ('EMI2','(EMI filter OR EMC design OR conducted emissions OR radiated emissions) electronics'),
 ('FW2','(embedded firmware OR embedded C OR RTOS OR watchdog OR bootloader) microcontroller'),
 ('MCU2','(STM32 OR Renesas OR Nuvoton OR Microchip OR Infineon MCU) motor power control'),
 ('MOTOR2','(FOC OR six step OR field oriented control OR BEMF OR stall detection) BLDC PMSM'),
 ('COMP','(current sensor OR MOSFET OR gate driver OR motor driver OR power IC) electronics'),
 ('BLOGKR','(BLDC OR PCB OR SMPS OR EMI OR 펌웨어) (블로그 OR 개발기 OR 설계기 OR 트러블슈팅)'),
 ('NAVERBLOG','site:blog.naver.com (BLDC OR PCB 설계 OR SMPS OR EMI EMC OR MCU 펌웨어)'),
 ('TISTORY','site:tistory.com (BLDC OR Altium OR PCB layout OR SMPS OR EMI OR embedded firmware)'),
 ('EEVBlog','site:eevblog.com (PCB layout OR SMPS OR EMI EMC OR motor control OR firmware)'),
 ('Hackaday','site:hackaday.com (motor control OR PCB design OR power supply OR embedded firmware)'),
 ('StackExchange','site:electronics.stackexchange.com (BLDC OR PCB layout OR SMPS OR EMI OR microcontroller firmware)'),
 ('Community','(BLDC OR PMSM OR PCB OR SMPS OR EMI OR MCU) (forum OR community OR troubleshooting)'),
]
NAVER_QUERIES=['BLDC 모터 제어','PMSM 센서리스','PCB 아트웍 알티움','SMPS 설계','EMI EMC 대책','마이컴 펌웨어 코딩','전력반도체 게이트 드라이버','전류센싱 회로']
BLOCK=['market size','market forecast','market share','growth trends','stock','investment','revenue forecast','2035','2036','job vacancy','course promotion','3.3kv','6.5kv','railway','ev traction']
WEIGHTS={'bldc':12,'pmsm':12,'sensorless':14,'motor control':10,'motor driver':10,'foc':11,'bemf':10,'stall':9,'current sensing':9,'gate driver':8,'mosfet':7,'mcu':7,'microcontroller':7,'firmware':8,'embedded c':11,'bootloader':9,'watchdog':8,'rtos':8,'pwm':7,'adc':7,'altium':13,'pcb layout':12,'pcb artwork':13,'stackup':9,'routing':7,'creepage':8,'clearance':8,'signal integrity':9,'smps':13,'flyback':10,'llc':9,'snubber':9,'compensation':8,'emi':10,'emc':10,'conducted emissions':11,'radiated emissions':11,'common mode choke':9,'appliance':5,'blender':8,'juicer':8}

def fetch(url, headers=None):
 req=urllib.request.Request(url,headers=headers or UA)
 with urllib.request.urlopen(req,timeout=30) as r:return r.read()
def clean(s):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(s or ''))).strip()
def parse_date(s):
 try:
  d=parsedate_to_datetime(s); return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
 except:return None
def gnews(q):return 'https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':'ko','gl':'KR','ceid':'KR:ko'})
def score(text):
 h=text.lower()
 if any(x in h for x in BLOCK):return -100
 return sum(v for k,v in WEIGHTS.items() if k in h)
def category(text):
 h=text.lower()
 if any(x in h for x in ['altium','pcb layout','pcb artwork','stackup','routing','creepage','clearance','signal integrity']):return 'PCB'
 if any(x in h for x in ['smps','flyback','llc','snubber','power supply','ac/dc','dc/dc']):return 'SMPS'
 if any(x in h for x in ['conducted emissions','radiated emissions','common mode choke','emi','emc']):return 'EMI'
 if any(x in h for x in ['bldc','pmsm','sensorless','motor control','motor driver','foc','bemf']):return 'MOTOR'
 if any(x in h for x in ['embedded c','firmware','microcontroller','mcu','bootloader','watchdog','rtos','uart','pwm','adc']):return 'FIRMWARE'
 return 'CIRCUIT'
def fallback_summary(cat):
 return {'PCB':'PCB 배치·배선, 전원/GND 경로, 절연거리, 발열 및 DFM 관점의 기술자료입니다.','SMPS':'SMPS 토폴로지, 자성부품, 보상회로, 효율·발열 및 보호회로 관점의 기술자료입니다.','EMI':'전도·복사 노이즈, 필터, 접지, PCB Loop 및 스위칭 영향 관점의 기술자료입니다.','MOTOR':'BLDC/PMSM 기동, 전류·속도 제어, 센서리스 및 보호 로직 관점의 기술자료입니다.','FIRMWARE':'마이컴 펌웨어 구조, 상태 머신, Interrupt, 통신, Watchdog 및 테스트 관점의 기술자료입니다.','CIRCUIT':'가전 회로설계의 부품 선정, 보호, 발열 및 신뢰성 관점의 기술자료입니다.'}[cat]
def checks(cat):
 return {'PCB':['Altium DRC·Stackup·Net Class','전원/GND·고전류·Gate Loop','Creepage·Clearance·발열·DFM'],'SMPS':['Topology·Transformer·보상회로','MOSFET·Diode·Snubber·효율','OCP·OVP·OTP·절연·발열'],'EMI':['전도/복사 Noise Source·Path','CM Choke·X/Y Cap·접지·Shield','PCB Loop·Switching Edge·Pre-scan'],'MOTOR':['기동 성공률·저속 안정성','상전류·RPM·PWM Duty','Stall·과전류·온도 보호'],'FIRMWARE':['Embedded C·상태 머신·ISR','Driver/HAL·통신·Bootloader','Watchdog·정적분석·Unit Test'],'CIRCUIT':['정격·Derating·발열','Protection·Reliability','BOM·검증·양산성']}[cat]
def translate_with_azure(title, snippet, cat):
 endpoint=os.getenv('AZURE_OPENAI_ENDPOINT','').rstrip('/'); key=os.getenv('AZURE_OPENAI_API_KEY',''); dep=os.getenv('AZURE_OPENAI_DEPLOYMENT','')
 if not(endpoint and key and dep):return title, fallback_summary(cat)
 url=f'{endpoint}/openai/deployments/{dep}/chat/completions?api-version=2024-10-21'
 prompt='''다음 뉴스 검색 메타정보를 한국어로 번역·요약하십시오. 원문에 없는 수치나 사양은 만들지 마십시오. JSON만 출력: {"titleKo":"한국어 제목","summaryKo":"2문장 기술 요약"}.\n제목: %s\n검색요약: %s\n분류: %s'''%(title,snippet,cat)
 body=json.dumps({'messages':[{'role':'system','content':'가전 전장 기술 편집자입니다.'},{'role':'user','content':prompt}],'temperature':0.1,'response_format':{'type':'json_object'}}).encode()
 try:
  data=json.loads(fetch(url,{'Content-Type':'application/json','api-key':key,'User-Agent':UA['User-Agent']} if False else None))
 except Exception:
  try:
   req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json','api-key':key})
   with urllib.request.urlopen(req,timeout=45) as r:data=json.load(r)
  except Exception as e:
   print('Azure translation error',repr(e));return title,fallback_summary(cat)
 try:
  obj=json.loads(data['choices'][0]['message']['content']);return clean(obj.get('titleKo')) or title,clean(obj.get('summaryKo')) or fallback_summary(cat)
 except:return title,fallback_summary(cat)
def add_google(candidates):
 cutoff=datetime.now(timezone.utc)-timedelta(days=DAYS)
 for source,q in SOURCE_QUERIES:
  try:
   root=ET.fromstring(fetch(gnews(q)))
   for n in root.findall('.//item')[:25]:
    raw=clean(n.findtext('title')); desc=clean(n.findtext('description')); url=clean(n.findtext('link')); dt=parse_date(clean(n.findtext('pubDate')))
    sc=score(raw+' '+desc)
    if not raw or not url or sc<4 or (dt and dt<cutoff):continue
    title=raw.rsplit(' - ',1)[0]; publisher=raw.rsplit(' - ',1)[1] if ' - ' in raw else source
    stype='전문매체'
    if source in ['ROHM','ST','TI','Infineon','Renesas','NXP','onsemi','Microchip','Altium']: stype='공식 기술자료'
    elif source in ['NAVERBLOG','TISTORY','Hackaday']: stype='기술블로그'
    elif source in ['EEVBlog','StackExchange','Community']: stype='커뮤니티'
    candidates.append({'title':title,'snippet':desc,'url':url,'published':dt.isoformat() if dt else '','source':publisher or source,'sourceType':stype,'score':sc})
  except Exception as e:print('Google source error',source,repr(e))
def add_naver(candidates):
 cid=os.getenv('NAVER_CLIENT_ID',''); secret=os.getenv('NAVER_CLIENT_SECRET','')
 if not(cid and secret):return
 for q in NAVER_QUERIES:
  url='https://openapi.naver.com/v1/search/news.json?'+urllib.parse.urlencode({'query':q,'display':20,'sort':'date'})
  try:
   data=json.loads(fetch(url,{'X-Naver-Client-Id':cid,'X-Naver-Client-Secret':secret,'User-Agent':UA['User-Agent']}))
   for n in data.get('items',[]):
    title=clean(n.get('title')); desc=clean(n.get('description')); sc=score(title+' '+desc)
    if sc<4:continue
    dt=parse_date(n.get('pubDate',''))
    candidates.append({'title':title,'snippet':desc,'url':n.get('originallink') or n.get('link'),'published':dt.isoformat() if dt else '','source':'네이버 뉴스 검색','sourceType':'뉴스/포털','score':sc})
  except Exception as e:print('Naver source error',q,repr(e))
def main():
 c=[];add_google(c);add_naver(c);c.sort(key=lambda x:(x['score'],x['published']),reverse=True)
 chosen=[];seen=set();source_count={}
 for x in c:
  key=''.join(re.findall(r'[a-z0-9가-힣]+',x['title'].lower()))[:90]
  if key in seen or source_count.get(x['source'],0)>=5:continue
  seen.add(key);source_count[x['source']]=source_count.get(x['source'],0)+1
  cat=category(x['title']+' '+x['snippet']); ko_title,ko_summary=translate_with_azure(x['title'],x['snippet'],cat)
  if not os.getenv('AZURE_OPENAI_API_KEY') and not re.search(r'[가-힣]', ko_title): ko_title=f'[{cat}] {ko_title}'
  chosen.append({'category':cat,'title':ko_title,'originalTitle':x['title'],'source':x['source'],'sourceType':x['sourceType'],'summary':ko_summary,'checkPoints':checks(cat),'rating':5 if x['score']>=30 else 4 if x['score']>=18 else 3,'url':x['url'],'published':x['published']})
  if len(chosen)>=MAX_ITEMS:break
 if not chosen:print('No qualified items; existing file preserved');return
 with open(OUT,'w',encoding='utf-8') as f:json.dump({'updated':datetime.now(timezone.utc).isoformat(),'issueTitle':f'이번 주 가전 전장 기술 TOP {len(chosen)}','translationMode':'Azure OpenAI' if os.getenv('AZURE_OPENAI_API_KEY') else '기본 한국어 요약','items':chosen},f,ensure_ascii=False,indent=2)
 print('Wrote',len(chosen),'items from',len(source_count),'sources')
if __name__=='__main__':main()
