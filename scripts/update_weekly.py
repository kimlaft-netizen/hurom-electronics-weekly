import os, re, json, html, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

OUT='data/weekly.json'; MAX_ITEMS=30; LOOKBACK_DAYS=180
UA='Mozilla/5.0 (HUROM-Electronics-Weekly/7.0)'
QUERIES=[
 'BLDC PMSM sensorless motor control FOC BEMF stall',
 'motor driver gate driver current sensing MOSFET appliance',
 'Altium PCB artwork layout routing stackup grounding creepage clearance',
 'SMPS flyback buck LLC transformer snubber compensation design',
 'EMI EMC conducted radiated emission common mode choke PCB layout',
 'microcontroller firmware embedded C RTOS watchdog bootloader UART PWM ADC',
 'STM32 Renesas Nuvoton Microchip Infineon motor control firmware',
 'juicer blender food processor motor electronics circuit design'
]
SITE_QUERIES=[
 'site:etnews.com 반도체 회로 모터 전원 펌웨어 PCB EMI',
 'site:e4ds.com BLDC MCU SMPS PCB EMI 전력반도체',
 'site:rohm.co.kr 모터드라이버 MOSFET 전원IC MCU 기술자료',
 'site:st.com motor control STM32 BLDC PMSM power supply',
 'site:ti.com motor control gate driver current sensing power supply',
 'site:infineon.com motor control MOSFET PSoC gate driver',
 'site:renesas.com motor control MCU inverter firmware',
 'site:nxp.com motor control MCU power management',
 'site:onsemi.com motor driver MOSFET power supply',
 'site:microchip.com motor control embedded C MCU SMPS',
 'site:resources.altium.com PCB layout stackup routing EMC',
 'site:blog.naver.com BLDC PCB SMPS EMI 펌웨어 회로설계',
 'site:tistory.com BLDC Altium PCB SMPS EMI embedded firmware',
 'site:eevblog.com PCB SMPS EMI motor control firmware',
 'site:hackaday.com motor control PCB power supply embedded firmware',
 'site:electronics.stackexchange.com BLDC PCB SMPS EMI microcontroller firmware'
]
BLOCK=[
 'english as a second language','second language','제2언어','영어 교육','고등 교육','language education',
 'vehicle can do','software defines','automotive','electric vehicle','ev traction','3300v','3.3kv','6.5kv',
 'market size','market forecast','market share','growth trends','stock','investment','revenue forecast',
 '2035','2036','job vacancy','course promotion','railway','solar farm','data center'
]
TERMS=['bldc','pmsm','sensorless','motor control','motor driver','foc','bemf','stall','current sensing','gate driver','mosfet','mcu','microcontroller','firmware','embedded c','bootloader','watchdog','rtos','pwm','adc','uart','altium','pcb','artwork','routing','stackup','creepage','clearance','grounding','signal integrity','smps','flyback','buck','llc','transformer','snubber','compensation','emi','emc','conducted emissions','radiated emissions','common mode choke','appliance','blender','juicer','food processor','모터','회로','전원','펌웨어','아트웍','노이즈','접지','반도체']

def fetch(url,headers=None,data=None):
 req=urllib.request.Request(url,data=data,headers=headers or {'User-Agent':UA})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read()
def clean(s):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(s or ''))).strip()
def parse_date(s):
 try:
  d=parsedate_to_datetime(s); return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
 except:return None
def relevant(text):
 h=text.lower()
 if any(x in h for x in BLOCK):return 0
 return sum(1 for x in TERMS if x in h)
def cat(text):
 h=text.lower()
 if any(x in h for x in ['altium','pcb','artwork','routing','stackup','creepage','clearance','signal integrity']):return 'PCB'
 if any(x in h for x in ['smps','flyback','llc','snubber','power supply','전원','buck converter']):return 'SMPS'
 if any(x in h for x in ['conducted emission','radiated emission','common mode choke','emi','emc','노이즈']):return 'EMI'
 if any(x in h for x in ['bldc','pmsm','sensorless','motor control','motor driver','foc','bemf','모터']):return 'MOTOR'
 if any(x in h for x in ['embedded c','firmware','펌웨어','microcontroller','mcu','bootloader','watchdog','rtos','uart','pwm','adc']):return 'FIRMWARE'
 return 'CIRCUIT'
def stype(url,source=''):
 h=(url+' '+source).lower()
 if any(x in h for x in ['rohm.','st.com','ti.com','infineon.','renesas.','nxp.','onsemi.','microchip.','altium.']):return '공식 기술자료'
 if any(x in h for x in ['blog.naver.','tistory.','hackaday.']):return '기술블로그'
 if any(x in h for x in ['eevblog.','stackexchange.','cafe.naver.']):return '커뮤니티'
 if any(x in h for x in ['etnews.','e4ds.']):return '전문매체'
 return '뉴스/웹'
def summary(category):
 return {'PCB':'PCB Artwork, 배치·배선, 전원/GND 경로, 절연거리, 발열 및 DFM 관점의 자료입니다.','SMPS':'SMPS 토폴로지, 자성부품, 보상회로, 효율·발열 및 보호회로 관점의 자료입니다.','EMI':'전도·복사 노이즈, 필터, 접지, PCB Loop 및 스위칭 영향 관점의 자료입니다.','MOTOR':'BLDC/PMSM 기동, 전류·속도 제어, 센서리스 및 보호 로직 관점의 자료입니다.','FIRMWARE':'마이컴 펌웨어 구조, 상태 머신, Interrupt, 통신, Watchdog 및 테스트 관점의 자료입니다.','CIRCUIT':'가전 회로설계의 부품 선정, 보호, 발열 및 신뢰성 관점의 자료입니다.'}[category]
def checks(category):
 return {'PCB':['Altium DRC·Stackup·Net Class','전원/GND·고전류·Gate Loop','Creepage·Clearance·발열·DFM'],'SMPS':['Topology·Transformer·보상회로','MOSFET·Diode·Snubber·효율','OCP·OVP·OTP·절연·발열'],'EMI':['전도/복사 Noise Source·Path','CM Choke·X/Y Cap·접지·Shield','PCB Loop·Switching Edge·Pre-scan'],'MOTOR':['기동 성공률·저속 안정성','상전류·RPM·PWM Duty','Stall·과전류·온도 보호'],'FIRMWARE':['Embedded C·상태 머신·ISR','Driver/HAL·통신·Bootloader','Watchdog·정적분석·Unit Test'],'CIRCUIT':['정격·Derating·발열','Protection·Reliability','BOM·검증·양산성']}[category]
def add(out,title,desc,url,date='',source='',kind=''):
 title=clean(title);desc=clean(desc)
 rel=relevant(title+' '+desc)
 if not title or not url or rel<1:return
 out.append({'title':title,'snippet':desc,'url':url,'published':date,'source':source or urllib.parse.urlparse(url).netloc,'sourceType':kind or stype(url,source),'score':rel})

def collect_google_news(out):
 for q in SITE_QUERIES+QUERIES:
  try:
   u='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q,'hl':'ko','gl':'KR','ceid':'KR:ko'})
   root=ET.fromstring(fetch(u))
   for n in root.findall('.//item')[:100]:
    raw=clean(n.findtext('title')); title=raw.rsplit(' - ',1)[0]; src=raw.rsplit(' - ',1)[1] if ' - ' in raw else ''
    dt=parse_date(clean(n.findtext('pubDate'))); date=dt.isoformat() if dt else ''
    add(out,title,n.findtext('description'),clean(n.findtext('link')),date,src,stype('',src))
  except Exception as e:print('gnews',q,repr(e))

def collect_naver(out):
 cid=os.getenv('NAVER_CLIENT_ID'); sec=os.getenv('NAVER_CLIENT_SECRET')
 if not(cid and sec):return
 headers={'X-Naver-Client-Id':cid,'X-Naver-Client-Secret':sec,'User-Agent':UA}
 for endpoint,kind in [('blog','기술블로그'),('news','뉴스/포털')]:
  for q in QUERIES:
   for start in [1,101,201]:
    try:
     u=f'https://openapi.naver.com/v1/search/{endpoint}.json?'+urllib.parse.urlencode({'query':q,'display':100,'start':start,'sort':'date' if endpoint=='news' else 'sim'})
     data=json.loads(fetch(u,headers))
     for x in data.get('items',[]):add(out,x.get('title'),x.get('description'),x.get('originallink') or x.get('link'),x.get('postdate') or x.get('pubDate',''),'네이버 '+('블로그' if endpoint=='blog' else '뉴스'),kind)
    except Exception as e:print('naver',endpoint,start,repr(e));break

def collect_google_custom(out):
 key=os.getenv('GOOGLE_CSE_API_KEY'); cx=os.getenv('GOOGLE_CSE_ID')
 if not(key and cx):return
 for q in SITE_QUERIES+QUERIES:
  for start in [1,11,21,31,41]:
   try:
    u='https://www.googleapis.com/customsearch/v1?'+urllib.parse.urlencode({'key':key,'cx':cx,'q':q,'start':start,'num':10,'dateRestrict':'m12'})
    data=json.loads(fetch(u))
    for x in data.get('items',[]):add(out,x.get('title'),x.get('snippet'),x.get('link'),'','','')
   except Exception as e:print('cse',q,start,repr(e));break

def translate(title,snippet,category):
 endpoint=os.getenv('AZURE_OPENAI_ENDPOINT','').rstrip('/');key=os.getenv('AZURE_OPENAI_API_KEY');dep=os.getenv('AZURE_OPENAI_DEPLOYMENT')
 if not(endpoint and key and dep):return title,summary(category)
 prompt='다음 검색 메타정보를 한국어 제목과 2문장 기술 요약으로 바꾸세요. 원문에 없는 사양은 만들지 마세요. JSON만 출력: {"titleKo":"","summaryKo":""}\n제목:'+title+'\n요약:'+snippet
 body=json.dumps({'messages':[{'role':'system','content':'가전 전장 기술 편집자'},{'role':'user','content':prompt}],'temperature':0.1,'response_format':{'type':'json_object'}}).encode()
 try:
  u=f'{endpoint}/openai/deployments/{dep}/chat/completions?api-version=2024-10-21';data=json.loads(fetch(u,{'Content-Type':'application/json','api-key':key,'User-Agent':UA},body));obj=json.loads(data['choices'][0]['message']['content']);return clean(obj.get('titleKo')) or title,clean(obj.get('summaryKo')) or summary(category)
 except Exception as e:print('translate',repr(e));return title,summary(category)

def old_items():
 try:return json.load(open(OUT,encoding='utf-8')).get('items',[])
 except:return []
def main():
 rows=[];collect_google_news(rows);collect_naver(rows);collect_google_custom(rows)
 # 이전에 잘 찾은 유효 자료도 후보로 유지하여 새 실행 때 전부 사라지지 않게 한다.
 for x in old_items():add(rows,x.get('originalTitle') or x.get('title'),x.get('summary'),x.get('url'),x.get('published',''),x.get('source',''),x.get('sourceType',''))
 rows.sort(key=lambda x:(x['score'],x.get('published','')),reverse=True)
 picked=[];seen=set();per_source={};per_category={}
 for x in rows:
  key=''.join(re.findall(r'[a-z0-9가-힣]+',x['title'].lower()))[:100]
  if not key or key in seen:continue
  c=cat(x['title']+' '+x['snippet']); src=x['source']
  if per_source.get(src,0)>=6:continue
  seen.add(key);per_source[src]=per_source.get(src,0)+1;per_category[c]=per_category.get(c,0)+1
  kt,ks=translate(x['title'],x['snippet'],c)
  picked.append({'category':c,'title':kt,'originalTitle':x['title'],'source':src,'sourceType':x['sourceType'],'summary':ks,'checkPoints':checks(c),'rating':5 if x['score']>=6 else 4 if x['score']>=3 else 3,'url':x['url'],'published':x['published']})
  if len(picked)>=MAX_ITEMS:break
 if not picked:print('No valid items; preserved existing file');return
 json.dump({'updated':datetime.now(timezone.utc).isoformat(),'issueTitle':f'가전 전장 기술 TOP {len(picked)}','searchedCandidates':len(rows),'translationMode':'Azure OpenAI' if os.getenv('AZURE_OPENAI_API_KEY') else '기본 한국어 요약','items':picked},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print('candidates',len(rows),'selected',len(picked),'categories',per_category)
if __name__=='__main__':main()
