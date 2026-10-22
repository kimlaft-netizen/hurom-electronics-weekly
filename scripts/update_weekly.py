import os,re,json,html,time,urllib.parse,urllib.request,urllib.error,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor,as_completed
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
OUT='data/weekly.json';MAX_ITEMS=30;UA='Mozilla/5.0 HUROM-Weekly-V8'
RUN_END=datetime.now(timezone.utc);RUN_START=RUN_END-timedelta(days=7)
Q_KR=[
 'BLDC 모터제어','PMSM 센서리스 FOC','모터 전류센싱 MOSFET 드라이버','가전 모터 청소기 믹서기 착즙기','회로 보호회로 게이트드라이버','Altium PCB 아트웍 EMC','SMPS 플라이백 벅 컨버터','EMI EMC 모터 노이즈 필터','MCU 펌웨어 PWM ADC RTOS','STM32 Renesas 모터 펌웨어','가전 전장 열설계 신뢰성','공개 블로그 카페 모터제어 회로'
 ,'원액기 착즙기 녹즙기 BLDC 모터 제어 회로','블렌더 푸드프로세서 모터 드라이버 PWM 과전류','저속 착즙기 오거 스크류 모터 토크 과열','주방가전 착즙기 블렌더 EMI EMC PCB 전원 설계'
 ,'가전 LED LCD 표시부 상태표시 버튼 스위치 MCU 회로','가전 IPM IGBT 전력모듈 인버터 게이트드라이버','가전 전선 하네스 커넥터 센서 온도 전류 통신 UART I2C SPI'
 ,'가전 인공지능 AI 스마트가전 모터 센서 제어','임베디드 AI 엣지AI MCU 펌웨어 TinyML','모터 전류 진동 센서 AI 고장진단 예지보전'
]
Q_GLOBAL=[
 'BLDC PMSM motor control','sensorless FOC startup BEMF','motor driver current sensing MOSFET','appliance juicer blender motor electronics','PCB layout power electronics EMI','SMPS flyback buck converter design','EMI EMC conducted emissions filter','MCU firmware embedded C RTOS PWM','STM32 Renesas motor control firmware','appliance electronics thermal reliability','motor control engineering blog','site:hackaday.com motor driver PCB','site:eevblog.com SMPS EMI PCB','site:electronics.stackexchange.com motor driver PCB'
 ,'juicer slow juicer BLDC motor control board electronics','blender food processor motor drive current sensing PWM','cold press juicer auger motor torque thermal protection','kitchen appliance juicer blender EMC EMI PCB power supply'
 ,'home appliance LED LCD display indicator button switch MCU circuit','appliance IPM IGBT power module inverter gate driver','appliance wiring harness connector sensor UART I2C SPI CAN communication'
 ,'AI smart appliance motor sensor control embedded artificial intelligence','edge AI MCU firmware TinyML appliance electronics','motor fault detection predictive maintenance sensor machine learning'
]
Q=Q_KR+Q_GLOBAL
S=['site:etnews.com 가전 모터 전원','site:e4ds.com 모터제어 전력반도체','site:blog.naver.com BLDC 모터 PCB','site:cafe.naver.com 모터제어 회로 PCB','site:ti.com motor gate driver current sensing','site:st.com motor control firmware STM32','site:resources.altium.com PCB EMI design','site:hackaday.com motor control PCB']
BLOCK=['english as a second language','second language','제2언어','영어 교육','language education','automotive','electric vehicle','3300v','3.3kv','6.5kv','market size','market forecast','market share','stock','investment','2035','2036','job vacancy','calgary roughnecks','national lacrosse league','lacrosse game']
AUTO=['automotive','electric vehicle','ev traction','차량용','전기차']
APPLIANCE_CONTEXT=['appliance','가전','juicer','blender','food processor','vacuum cleaner','청소기','믹서기','착즙기','원액기','녹즙기','푸드프로세서','주서기','식품가공기']
TERMS=['bldc','pmsm','sensorless','foc','bemf','motor','모터','모터제어','driver','gate drive','current control','current sensing','mosfet','gate driver','mcu','microcontroller','firmware','펌웨어','embedded c','watchdog','rtos','pwm','adc','uart','spi','i2c','isr','bootloader','stm32','renesas','nuvoton','microchip','infineon','altium','pcb','artwork','routing','stackup','creepage','clearance','gnd','grounding','high current','gate loop','dfm','smps','ac/dc','dc/dc','flyback','buck','llc','transformer','snubber','compensation','emi','emc','conducted emission','radiated emission','common mode choke','노이즈','회로','전원','반도체','가전','juicer','blender','food processor','food processing','kitchen appliance','slow juicer','cold press','juice extractor','auger','torque','stall current','overcurrent','thermal protection','gearbox','speed control','current limit','soft start','주방가전','착즙기','원액기','녹즙기','블렌더','푸드프로세서','주서기','식품가공기','저속착즙','스크류','오거','감속기','분쇄','칼날','속도제어','토크','정격전류','과전류','과열','온도보호']
TERMS.extend(['led','led driver','led indicator','lcd','display','display module','seven segment','backlight','ipm','igbt','power module','switch','push button','tact switch','debounce','wiring','wire harness','harness','cable','connector','terminal','crimp','sensor','hall sensor','ntc','thermistor','temperature sensor','current sensor','pressure sensor','flow sensor','position sensor','proximity sensor','communication','can bus','canopen','rs485','modbus','bluetooth','wi-fi','artificial intelligence','machine learning','deep learning','tinyml','edge ai','on-device ai','ai inference','neural network','predictive maintenance','fault detection','인공지능','머신러닝','딥러닝','엣지ai','온디바이스ai','신경망','예지보전','고장진단','엘이디','상태표시등','표시부','액정','디스플레이','백라이트','전력모듈','지능형전력모듈','스위치','버튼','푸시버튼','택트스위치','디바운스','배선','전선','케이블','하네스','커넥터','단자','압착','크림핑','센서','홀센서','온도센서','서미스터','전류센서','압력센서','유량센서','위치센서','근접센서','통신','통신프로토콜','캔통신','시리얼통신','무선통신'])

def term_match(text,term):
 text=(text or '').lower();term=term.lower()
 if term.isascii() and term.isalnum() and len(term)<=4:
  return re.search(r'(?<![a-z0-9])'+re.escape(term)+r'(?![a-z0-9])',text) is not None
 return term in text
def fetch(u,h=None,d=None,timeout=8):
 r=urllib.request.Request(u,data=d,headers=h or {'User-Agent':UA})
 for attempt in range(2):
  try:return urllib.request.urlopen(r,timeout=timeout).read()
  except urllib.error.HTTPError as e:
   if e.code not in (429,500,502,503,504) or attempt==1:raise
   time.sleep(1)
  except (urllib.error.URLError,TimeoutError):
   if attempt==1:raise
   time.sleep(1)
def clean(s):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(s or ''))).strip()

def parse_publish_date(date_text):
 if not date_text:return None
 t=str(date_text).strip()
 # Parse ISO first. email.utils accepts some ISO-like inputs but can silently
 # discard their time component, which would let a future timestamp through.
 try:
  d=datetime.fromisoformat(t.replace('Z','+00:00'))
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc)
 except Exception:pass
 try:
  d=parsedate_to_datetime(t)
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc)
 except Exception:pass
 for fmt in ('%Y%m%d','%Y-%m-%d','%Y/%m/%d'):
  try:return datetime.strptime(t[:10] if fmt!='%Y%m%d' else t[:8],fmt).replace(tzinfo=timezone.utc)
  except Exception:pass
 return None

def within_last_week(date_text):
 d=parse_publish_date(date_text)
 if d is None:return False
 return RUN_START <= d <= RUN_END

def rel(t):
 h=t.lower()
 if any(x in h for x in BLOCK if x not in AUTO):return 0
 if any(x in h for x in AUTO) and not any(x in h for x in APPLIANCE_CONTEXT):return 0
 return sum(term_match(h,x) for x in TERMS)

def language_group(title, source, url=''):
 s=(source or '').lower();host=urllib.parse.urlparse(url or '').netloc.lower()
 if any(x in s or x in host for x in ['etnews','e4ds','rohm.co.kr','naver','tistory','chosun','korea','livesnews','hinews','전자신문','뉴스','조선','한국']):return 'KR'
 if any(x in s or x in host for x in ['ti.com','st.com','infineon','renesas','nxp.com','onsemi','microchip','altium','hackaday','eevblog','electronics.stackexchange','medium.com']):return 'GLOBAL'
 if re.search(r'[가-힣]',source or ''):return 'KR'
 return 'KR' if re.search(r'[가-힣]',title or '') and not re.search(r'[A-Za-z]{3,}',source or '') else 'GLOBAL'

def title_tokens(title):
 stop={'with','from','this','that','design','using','for','and','the','how','new','guide','기술','출시','선봬','적용'}
 return {x for x in re.findall(r'[a-z0-9가-힣]+',title.lower()) if len(x)>1 and x not in stop}

def duplicate_title(title, seen_titles):
 tokens=title_tokens(title)
 if not tokens:return True
 model_ids=set(re.findall(r'\b[a-z]+\d+[a-z0-9]*\b',title.lower()))
 tech_terms={'bldc','pmsm','foc','motor','모터','driver','emi','emc','smps','pcb','mcu'}
 for prior in seen_titles:
  prior_tokens=title_tokens(prior)
  if not prior_tokens:continue
  shared=tokens & prior_tokens
  if shared and len(shared)/len(tokens | prior_tokens) >= 0.78:return True
  prior_models=set(re.findall(r'\b[a-z]+\d+[a-z0-9]*\b',prior.lower()))
  if model_ids & prior_models and shared & tech_terms:return True
 return False
def cat(title,snippet=''):
 t=(title or '').lower();h=(t+' '+(snippet or '').lower())
 emi_title=any(term_match(t,x) for x in ['emi','emc','conducted emission','radiated emission','emi filter','emc filter','noise filter','노이즈 필터','전자파 필터'])
 smps_title=any(term_match(t,x) for x in ['smps','flyback','buck converter','buck','llc','ac/dc','dc/dc','switching regulator','power supply','스위칭 전원','플라이백','벅 컨버터'])
 # Give the headline's primary subject more weight than secondary terms in a
 # search snippet. This prevents EMI-filter market/design articles from being
 # misrouted to SMPS just because the body mentions AC/DC or DC/DC.
 if any(term_match(t,x) for x in ['emi filter','emc filter','emi 필터','emc 필터','noise filter','노이즈 필터']):return 'EMI'
 if emi_title and not smps_title:return 'EMI'
 if smps_title and not emi_title:return 'SMPS'
 if any(x in h for x in ['altium','pcb','artwork','routing','stackup','creepage','clearance']):return 'PCB'
 if any(x in h for x in ['smps','flyback','llc','snubber','power supply','전원']):return 'SMPS'
 if any(x in h for x in ['emi','emc','conducted emission','radiated emission','노이즈']):return 'EMI'
 if any(term_match(h,x) for x in ['ai','artificial intelligence','machine learning','deep learning','tinyml','edge ai','on-device ai','ai inference','neural network','predictive maintenance','fault detection','인공지능','머신러닝','딥러닝','엣지ai','온디바이스ai','신경망','예지보전','고장진단']):return 'AI'
 if any(x in h for x in ['firmware','펌웨어','embedded c','mcu','microcontroller','watchdog','rtos','pwm','adc']):return 'FIRMWARE'
 if any(term_match(h,x) for x in ['led','lcd','display','ipm','igbt','switch','button','harness','wiring','wire','cable','connector','terminal','crimp','sensor','communication','uart','i2c','spi','can bus','canopen','rs485','modbus','bluetooth','wi-fi','엘이디','표시등','표시부','액정','디스플레이','백라이트','전력모듈','스위치','버튼','디바운스','배선','전선','케이블','하네스','커넥터','단자','압착','센서','통신','캔통신','시리얼통신','무선통신']):return 'COMPONENTS'
 if any(x in h for x in ['bldc','pmsm','sensorless','foc','bemf','motor','모터']):return 'MOTOR'
 return 'CIRCUIT'
def add(a,title,snip,url,date='',src='',typ='뉴스/웹',group=None):
 title=clean(title);snip=clean(snip);score=rel(title+' '+snip+' '+clean(src))
 if title and url and score and within_last_week(date):
  pd=parse_publish_date(date)
  source=src or urllib.parse.urlparse(url).netloc
  a.append({'title':title,'snippet':snip,'url':url,'published':pd.isoformat() if pd else '','source':source,'sourceType':typ,'languageGroup':group or language_group(title,source,url),'score':score})
def gnews(a):
 searches=[(q,'ko','KR','KR:ko',None) for q in S+Q_KR]+[(q,'ko','US','US:en','GLOBAL') for q in Q_GLOBAL]
 for q,hl,gl,ceid,group in searches:
  try:
   u='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q+' when:7d','hl':hl,'gl':gl,'ceid':ceid});root=ET.fromstring(fetch(u))
   for n in root.findall('.//item')[:100]:
    raw=clean(n.findtext('title'));src=raw.rsplit(' - ',1)[1] if ' - ' in raw else '';title=raw.rsplit(' - ',1)[0];add(a,title,n.findtext('description'),clean(n.findtext('link')),clean(n.findtext('pubDate')),src,'뉴스/검색',group)
  except Exception as e:print('gnews query failed',q,repr(e))
  time.sleep(0.35)

def resolve_google_news_url(url):
 # Google News RSS article links are JS-driven redirect pages, not publisher URLs.
 # Resolve them before saving so readers never land on Google's "Sorry" page.
 try:
  parsed=urllib.parse.urlparse(url)
  if parsed.hostname not in ('news.google.com','www.news.google.com'):return url
  gid=parsed.path.rstrip('/').split('/')[-1]
  if not gid:return None
  headers={'User-Agent':UA,'Cookie':'CONSENT=YES+cb; SOCS=CAI'}
  page_req=urllib.request.Request(f'https://news.google.com/rss/articles/{gid}',headers=headers)
  page=urllib.request.urlopen(page_req,timeout=6).read().decode('utf-8','ignore')
  sg=re.search(r'data-n-a-sg="([^"]+)"',page)
  ts=re.search(r'data-n-a-ts="([^"]+)"',page)
  article_id=re.search(r'data-n-a-id="([^"]+)"',page)
  if not(sg and ts and article_id):return None
  gid=article_id.group(1)
  inner=(
   '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,'
   'null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],'
   f'"{gid}",{ts.group(1)},"{sg.group(1)}"]'
  )
  body=urllib.parse.urlencode({'f.req':json.dumps([[['Fbv4je',inner,None,'generic']]])}).encode()
  req=urllib.request.Request(
   'https://news.google.com/_/DotsSplashUi/data/batchexecute',data=body,
   headers={**headers,'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'})
  raw=urllib.request.urlopen(req,timeout=6).read().decode('utf-8','ignore')
  payload=raw.split('\n\n',1)[-1]
  row=json.loads(payload)[0][2]
  if not row:return None
  real_url=json.loads(row)[1]
  return real_url if urllib.parse.urlparse(real_url).scheme in ('http','https') and 'news.google.com' not in urllib.parse.urlparse(real_url).netloc else None
 except Exception as e:
  print('Google News link resolution failed',repr(e))
  return None

def resolve_selected_links(selected):
 targets=[x for x in selected if urllib.parse.urlparse(x.get('url','')).hostname in ('news.google.com','www.news.google.com')]
 if not targets:return selected
 with ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(resolve_google_news_url,x['url']):x for x in targets}
  for future in as_completed(futures):
   item=futures[future];resolved=future.result()
   if resolved:item['url']=resolved
   else:item['skipGoogleRedirect']=True
 return [x for x in selected if not x.get('skipGoogleRedirect')]

def naver(a):
 cid=os.getenv('NAVER_CLIENT_ID');sec=os.getenv('NAVER_CLIENT_SECRET')
 if not(cid and sec):
  print('Naver news/blog/public-cafe search skipped: NAVER_CLIENT_ID/SECRET not configured')
  return
 h={'X-Naver-Client-Id':cid,'X-Naver-Client-Secret':sec,'User-Agent':UA}
 for ep,typ in [('news','전문매체'),('blog','기술 블로그'),('cafearticle','공개 카페 글')]:
  for q in Q_KR:
   try:
    u='https://openapi.naver.com/v1/search/'+ep+'.json?'+urllib.parse.urlencode({'query':q,'display':100,'start':1,'sort':'date'});d=json.loads(fetch(u,h))
    for x in d.get('items',[]):
     url=x.get('originallink') or x.get('link') or ''
     source=x.get('bloggername') or x.get('cafename') or urllib.parse.urlparse(url).netloc or '네이버 검색'
     date=x.get('postdate') or x.get('pubDate') or x.get('date') or ''
     add(a,x.get('title'),x.get('description'),url,date,source,typ,'KR')
    time.sleep(0.2)
   except Exception as e:print('naver',ep,q,repr(e))

def public_rss(a):
 feeds=[
  ('https://hackaday.com/blog/feed/','Hackaday','기술 블로그','GLOBAL'),
  ('https://electronics.stackexchange.com/feeds/tag/motor-control?sort=creation','Electrical Engineering Stack Exchange','공개 커뮤니티','GLOBAL'),
  ('https://electronics.stackexchange.com/feeds/tag/pcb?sort=creation','Electrical Engineering Stack Exchange','공개 커뮤니티','GLOBAL'),
  ('https://electronics.stackexchange.com/feeds/tag/power-electronics?sort=creation','Electrical Engineering Stack Exchange','공개 커뮤니티','GLOBAL'),
  ('https://electronics.stackexchange.com/feeds/tag/embedded?sort=creation','Electrical Engineering Stack Exchange','공개 커뮤니티','GLOBAL')]
 for url,source,typ,group in feeds:
  try:
   root=ET.fromstring(fetch(url));nodes=root.findall('.//item')+root.findall('.//{*}entry')
   for node in nodes[:100]:
    vals={child.tag.rsplit('}',1)[-1]:child for child in node}
    title=vals.get('title').text if vals.get('title') is not None else ''
    desc=vals.get('description') or vals.get('summary') or vals.get('content')
    link=vals.get('link');link=(link.attrib.get('href','') if link is not None and link.attrib.get('href') else (link.text if link is not None else ''))
    date=next((vals[k].text for k in ('pubDate','published','updated') if vals.get(k) is not None and vals[k].text),'')
    add(a,title,desc.text if desc is not None else '',link,date,source,typ,group)
  except Exception as e:print('public RSS failed',source,url,repr(e))

def cse(a):
 key=os.getenv('GOOGLE_CSE_API_KEY');cx=os.getenv('GOOGLE_CSE_ID')
 if not(key and cx):
  print('Google Custom Search skipped: GOOGLE_CSE_API_KEY/ID not configured')
  return
 for q in S+Q:
  try:
   u='https://www.googleapis.com/customsearch/v1?'+urllib.parse.urlencode({'key':key,'cx':cx,'q':q,'start':1,'num':10,'dateRestrict':'d7'});d=json.loads(fetch(u))
   for x in d.get('items',[]):
    meta=(x.get('pagemap') or {}).get('metatags') or [{}]
    m=meta[0] if meta else {}
    date=next((m.get(k) for k in ('article:published_time','datepublished','pubdate','date') if m.get(k)), '')
    add(a,x.get('title'),x.get('snippet'),x.get('link'),date,'Google 검색','검색/웹')
  except Exception as e:print('cse',q,repr(e))
  time.sleep(0.2)

class ArticleParser(HTMLParser):
 def __init__(self):
  super().__init__();self.in_p=False;self.parts=[];self.meta=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='p':self.in_p=True
  if tag=='meta':
   key=(a.get('property') or a.get('name') or '').lower();val=a.get('content','')
   if key in ['description','og:description','twitter:description'] and val:self.meta.append(val)
 def handle_endtag(self,tag):
  if tag=='p':self.in_p=False
 def handle_data(self,data):
  if self.in_p and data.strip():self.parts.append(data.strip())

def get_article_text(url):
 # Search aggregator pages are not treated as article bodies.
 if not url or 'news.google.com/' in url:return ''
 try:
  raw=fetch(url).decode('utf-8','ignore')[:1500000]
  p=ArticleParser();p.feed(raw)
  paras=[]
  for x in p.parts:
   x=clean(x)
   if any(noise in x.lower() for noise in ['google 검색에서 더 쉽게','관심 있는 itchosun 기사','subscribe to our newsletter','sign up for our newsletter','advertisement']):continue
   if len(x)>=35 and x not in paras:paras.append(x)
  text=' '.join(paras)
  if len(text)<180:
   # Many publishers expose the actual article body as JSON-LD even when the
   # visible article is rendered by JavaScript and contains no usable <p> tags.
   bodies=re.findall(r'"articleBody"\s*:\s*("(?:\\.|[^"\\])*")',raw,re.I)
   for body in bodies:
    try:
     value=clean(json.loads(body))
     if len(value)>len(text):text=value
    except Exception:pass
  if len(text)<180 and p.meta:text=clean(' '.join(p.meta))
  return text[:4500]
 except Exception as e:
  print('article fetch',url[:80],repr(e));return ''

def normalize_summary(text,title='',source=''):
 text=clean(text)
 if not text:return ''
 # Search descriptions sometimes contain only the headline plus its outlet.
 text=re.sub(r'\s*(?:\||｜|[-–—])\s*(?:에이빙|aving)\s*$', '', text, flags=re.I).strip()
 if source:
  outlet=re.escape(clean(source))
  text=re.sub(rf'\s*(?:\||｜|[-–—])\s*{outlet}\s*$', '', text, flags=re.I).strip()
 if title:
  key=lambda value:re.sub(r'[^a-z0-9가-힣]','',clean(value).lower())
  normalized_text=key(text);normalized_title=key(title)
  if normalized_title and normalized_text.startswith(normalized_title):
   text=text[len(clean(title)):].lstrip(' \t\r\n|｜:：-–—·…\"\'')
   text=re.sub(r'^(?:에이빙|aving)\b\s*','',text,flags=re.I).strip()
 if not text:return ''
 return text[:900].rstrip()

def fallback_summary(text,title='',source='',limit=900):
 text=normalize_summary(text,title,source)
 if not text:return ''
 sentences=[x.strip() for x in re.split(r'(?<=[.!?。])\s+',text) if len(x.strip())>24]
 result=' '.join(sentences[:5]) if sentences else text
 return result[:limit].rstrip()

def analyze(title,snip,c,article_text="",source=''):
 # Prefer genuine page text. A headline-only search snippet is never shown as
 # if it were article content.
 body=article_text or snip
 fallback=fallback_summary(body,title,source)
 if not fallback:fallback='본문 미리보기를 가져오지 못했습니다. 원문 링크에서 기사 내용을 확인해 주세요.'
 ks=[x for x in TERMS if term_match(title+' '+snip+' '+article_text,x)][:6] or [c]
 if not article_text and not normalize_summary(snip,title,source):
  return title,fallback,ks
 ep=os.getenv('AZURE_OPENAI_ENDPOINT','').rstrip('/');key=os.getenv('AZURE_OPENAI_API_KEY');dep=os.getenv('AZURE_OPENAI_DEPLOYMENT')
 if not(ep and key and dep):return title,fallback,ks
 source_text=(article_text[:4000] if article_text else snip)
 prompt='기사 제목을 요약에 반복하지 말고, 매체명이나 기자명을 덧붙이지 말 것. 본문에 적힌 사실만 사용해 한국어로 기술적인 본문 핵심을 구체적으로 요약하고 없는 내용은 만들지 말 것. JSON만 출력 {\"titleKo\":\"\",\"articleSummaryKo\":\"\",\"keywords\":[]}. articleSummaryKo는 제목이 아닌 기사 본문 내용 4~5문장, 최대 450자. keywords는 본문에서 확인되는 기술어 3~6개. 제목:'+title+' 본문:'+source_text
 body=json.dumps({'messages':[{'role':'system','content':'가전 전장 기술 편집자'},{'role':'user','content':prompt}],'temperature':0,'response_format':{'type':'json_object'}}).encode()
 try:
  u=f'{ep}/openai/deployments/{dep}/chat/completions?api-version=2024-10-21';d=json.loads(fetch(u,{'Content-Type':'application/json','api-key':key,'User-Agent':UA},body));o=json.loads(d['choices'][0]['message']['content']);summary=fallback_summary(o.get('articleSummaryKo',''),title,source) or fallback;return clean(o.get('titleKo')) or title,summary,[clean(str(x)) for x in o.get('keywords',[])][:6] or ks
 except Exception as e:print('ai',repr(e));return title,fallback,ks
def old(a):
 try:
  for x in json.load(open(OUT,encoding='utf-8')).get('items',[]):add(a,x.get('originalTitle') or x.get('title'),x.get('summary'),x.get('url'),x.get('published',''),x.get('source',''),x.get('sourceType',''))
 except:pass

def select_candidates(items,max_items=MAX_ITEMS):
 ordered=sorted((x for x in items if within_last_week(x.get('published','')) and x.get('score',0)>=1),key=lambda x:x.get('score',0),reverse=True)
 chosen=[];titles=[];publishers={};groups={'KR':0,'GLOBAL':0}
 def take(x,preferred_group=None,enforce_quota=False):
  group=x.get('languageGroup') or language_group(x.get('title',''),x.get('source',''),x.get('url',''))
  source=x.get('source') or urllib.parse.urlparse(x.get('url','')).netloc
  if preferred_group and group!=preferred_group:return
  if enforce_quota and groups[group]>=MAX_ITEMS//2:return
  if publishers.get(source,0)>=5 or duplicate_title(x.get('title',''),titles):return
  chosen.append(x);titles.append(x.get('title',''));publishers[source]=publishers.get(source,0)+1;groups[group]=groups.get(group,0)+1
 for group in ('KR','GLOBAL'):
  for x in ordered:
   if groups[group]>=MAX_ITEMS//2:break
   take(x,group,True)
 for x in ordered:
  if len(chosen)>=max_items:break
  take(x)
 return chosen

def relevance_rating(title,snippet,article_text=''):
 title_terms={term for term in TERMS if term_match(title,term)}
 all_terms={term for term in TERMS if term_match(title+' '+snippet+' '+article_text,term)}
 direct=len(title_terms);total=len(all_terms)
 if direct>=3 and total>=5:return 5
 if direct>=2 and total>=4:return 4
 if direct>=1 and total>=3:return 3
 if total>=2:return 2
 return 1

def main():
 a=[];gnews(a);naver(a);public_rss(a);cse(a);old(a);out=[]
 # Keep a small reserve so a card with a headline-only or irrelevant snippet
 # can be skipped and replaced without widening the search itself.
 selected=select_candidates(a,MAX_ITEMS*2)
 used=set()
 def curate(x):
  resolved=resolve_selected_links([x])
  if not resolved:return None
  x=resolved[0]
  c=cat(x['title'],x['snippet']);article_text='' if x['sourceType']=='공개 카페 글' else get_article_text(x['url']);t,s,kw=analyze(x['title'],x['snippet'],c,article_text,x['source'])
  if not normalize_summary(s,x['title'],x['source']) or s.startswith('본문 미리보기를 가져오지 못했습니다'):return None
  return {'category':c,'title':t,'originalTitle':x['title'],'source':x['source'],'sourceType':x['sourceType'],'languageGroup':x.get('languageGroup') or language_group(x['title'],x['source'],x['url']),'summary':s,'keywords':kw,'rating':relevance_rating(x['title'],x['snippet'],article_text),'url':x['url'],'published':x['published']}
 # First fill up to 15 usable cards in each language. Invalid articles do not
 # consume a slot, so the next candidate in that language gets a chance.
 for group in ('KR','GLOBAL'):
  for x in selected:
   if sum(1 for item in out if item['languageGroup']==group)>=MAX_ITEMS//2:break
   candidate_group=x.get('languageGroup') or language_group(x.get('title',''),x.get('source',''),x.get('url',''))
   if candidate_group!=group or id(x) in used:continue
   used.add(id(x));item=curate(x)
   if item:out.append(item)
 # If either language has fewer than 15 usable items, fill the remaining slots
 # from whichever language still has relevant, sufficiently detailed content.
 if len(out)<MAX_ITEMS:
  for x in selected:
   if len(out)>=MAX_ITEMS:break
   if id(x) in used:continue
   used.add(id(x));item=curate(x)
   if item:out.append(item)
 # Last mandatory check immediately before writing. Never carry stale cards forward.
 out=[x for x in out if within_last_week(x.get('published',''))]
 out.sort(key=lambda x:x.get('published',''),reverse=True)
 out.sort(key=lambda x:x.get('rating',1),reverse=True)
 for x in out:
  x['published']=parse_publish_date(x['published']).isoformat()
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 # Archive the previously published issue before replacing weekly.json.
 # A date key makes repeated runs on the same day idempotent.
 archive_path='data/archive.json'
 try:
  with open(archive_path,encoding='utf-8') as f:archive=json.load(f)
 except (OSError,ValueError):archive={'weeks':[]}
 weeks=archive.get('weeks',[])
 try:
  with open(OUT,encoding='utf-8') as f:previous=json.load(f)
 except (OSError,ValueError):previous={}
 if previous.get('items'):
  week_key=(previous.get('windowEnd') or previous.get('updated') or '')[:10]
  if week_key:
   snapshot={'week':week_key,'updated':previous.get('updated',''),'issueTitle':previous.get('issueTitle',''),'items':previous['items']}
   weeks=[w for w in weeks if w.get('week')!=week_key]
   weeks.append(snapshot)
 archive['weeks']=sorted(weeks,key=lambda w:w.get('week',''),reverse=True)
 with open(archive_path,'w',encoding='utf-8') as f:json.dump(archive,f,ensure_ascii=False,indent=2)
 payload={'updated':RUN_END.isoformat(),'windowStart':RUN_START.isoformat(),'windowEnd':RUN_END.isoformat(),'issueTitle':f'전장 기술 TOP {len(out)}','searchedCandidates':len(a),'languageBalance':{'KR':sum(1 for x in out if x.get('languageGroup')=='KR'),'GLOBAL':sum(1 for x in out if x.get('languageGroup')=='GLOBAL')},'items':out}
 with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print('candidates',len(a),'KR',sum(1 for x in out if x.get('languageGroup')=='KR'),'GLOBAL',sum(1 for x in out if x.get('languageGroup')=='GLOBAL'),'selected',len(out))
if __name__=='__main__':main()
