import os,re,json,html,time,urllib.parse,urllib.request,urllib.error,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
OUT='data/weekly.json';MAX_ITEMS=30;UA='Mozilla/5.0 HUROM-Weekly-V8'
RUN_END=datetime.now(timezone.utc);RUN_START=RUN_END-timedelta(days=7)
Q=['BLDC PMSM sensorless FOC motor control','motor driver gate driver current sensing MOSFET','Altium PCB artwork routing stackup grounding creepage clearance','SMPS flyback buck LLC transformer snubber compensation','EMI EMC conducted radiated emissions common mode choke','microcontroller firmware embedded C RTOS watchdog bootloader UART PWM ADC','STM32 Renesas Nuvoton Microchip Infineon firmware motor','juicer blender food processor motor electronics','가전 모터 BLDC','가전 전장 모터 회로','주방가전 모터 전자회로','BLDC vacuum cleaner motor','home appliance motor control electronics','kitchen appliance motor BLDC','smart motor gate drive TDRIVE','secured MCU legacy board firmware design']
S=['site:etnews.com 반도체 회로 모터 전원 펌웨어 PCB EMI','site:e4ds.com BLDC MCU SMPS PCB EMI 전력반도체','site:rohm.co.kr 모터드라이버 MOSFET 전원IC MCU','site:st.com BLDC PMSM motor control STM32','site:ti.com motor control gate driver current sensing','site:infineon.com motor control MOSFET PSoC','site:renesas.com motor control MCU inverter firmware','site:nxp.com motor control MCU','site:onsemi.com motor driver MOSFET','site:microchip.com motor control embedded C','site:resources.altium.com PCB layout stackup EMC','site:blog.naver.com BLDC PCB SMPS EMI 펌웨어','site:tistory.com BLDC Altium PCB SMPS EMI firmware','site:eevblog.com PCB SMPS EMI motor control','site:electronics.stackexchange.com BLDC PCB SMPS EMI microcontroller']
BLOCK=['english as a second language','second language','제2언어','영어 교육','language education','automotive','electric vehicle','3300v','3.3kv','6.5kv','market size','market forecast','market share','stock','investment','2035','2036','job vacancy']
TERMS=['bldc','pmsm','sensorless','foc','bemf','motor','모터','driver','current sensing','mosfet','mcu','firmware','펌웨어','embedded c','watchdog','rtos','pwm','adc','uart','altium','pcb','artwork','routing','stackup','creepage','clearance','grounding','smps','flyback','buck','llc','snubber','emi','emc','노이즈','회로','전원','반도체']
def fetch(u,h=None,d=None):
 r=urllib.request.Request(u,data=d,headers=h or {'User-Agent':UA})
 for attempt in range(3):
  try:return urllib.request.urlopen(r,timeout=45).read()
  except urllib.error.HTTPError as e:
   if e.code not in (429,500,502,503,504) or attempt==2:raise
   time.sleep(1+attempt*2)
  except (urllib.error.URLError,TimeoutError):
   if attempt==2:raise
   time.sleep(1+attempt*2)
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
 if any(x in h for x in BLOCK):return 0
 return sum(x in h for x in TERMS)

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
  if len(shared)/min(len(tokens),len(prior_tokens)) >= 0.68:return True
  prior_models=set(re.findall(r'\b[a-z]+\d+[a-z0-9]*\b',prior.lower()))
  if model_ids & prior_models and shared & tech_terms:return True
 return False
def cat(t):
 h=t.lower()
 if any(x in h for x in ['altium','pcb','artwork','routing','stackup','creepage','clearance']):return 'PCB'
 if any(x in h for x in ['smps','flyback','llc','snubber','power supply','전원']):return 'SMPS'
 if any(x in h for x in ['emi','emc','conducted emission','radiated emission','노이즈']):return 'EMI'
 if any(x in h for x in ['bldc','pmsm','sensorless','foc','bemf','motor','모터']):return 'MOTOR'
 if any(x in h for x in ['firmware','펌웨어','embedded c','mcu','microcontroller','watchdog','rtos','uart','pwm','adc']):return 'FIRMWARE'
 return 'CIRCUIT'
def add(a,title,snip,url,date='',src='',typ='뉴스/웹'):
 title=clean(title);snip=clean(snip);score=rel(title+' '+snip)
 if title and url and score and within_last_week(date):
  pd=parse_publish_date(date)
  a.append({'title':title,'snippet':snip,'url':url,'published':pd.isoformat() if pd else '','source':src or urllib.parse.urlparse(url).netloc,'sourceType':typ,'score':score})
def gnews(a):
 for q in S+Q:
  try:
   u='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q+' when:7d','hl':'ko','gl':'KR','ceid':'KR:ko'});root=ET.fromstring(fetch(u))
   for n in root.findall('.//item')[:100]:
    raw=clean(n.findtext('title'));src=raw.rsplit(' - ',1)[1] if ' - ' in raw else '';title=raw.rsplit(' - ',1)[0];add(a,title,n.findtext('description'),clean(n.findtext('link')),clean(n.findtext('pubDate')),src,'검색/전문매체')
  except Exception as e:print('gnews query failed',q,repr(e))
  time.sleep(0.35)
def naver(a):
 cid=os.getenv('NAVER_CLIENT_ID');sec=os.getenv('NAVER_CLIENT_SECRET')
 if not(cid and sec):return
 h={'X-Naver-Client-Id':cid,'X-Naver-Client-Secret':sec,'User-Agent':UA}
 for ep,typ in [('blog','기술블로그'),('news','뉴스/포털')]:
  for q in Q:
   for start in [1,101,201]:
    try:
     u='https://openapi.naver.com/v1/search/'+ep+'.json?'+urllib.parse.urlencode({'query':q,'display':100,'start':start,'sort':'date' if ep=='news' else 'sim'});d=json.loads(fetch(u,h))
     for x in d.get('items',[]):add(a,x.get('title'),x.get('description'),x.get('originallink') or x.get('link'),x.get('postdate') or x.get('pubDate',''),'네이버',typ)
    except Exception as e:print('naver',repr(e));break
def cse(a):
 key=os.getenv('GOOGLE_CSE_API_KEY');cx=os.getenv('GOOGLE_CSE_ID')
 if not(key and cx):return
 for q in S+Q:
  for start in [1,11,21,31,41]:
   try:
    u='https://www.googleapis.com/customsearch/v1?'+urllib.parse.urlencode({'key':key,'cx':cx,'q':q,'start':start,'num':10,'dateRestrict':'d7'});d=json.loads(fetch(u))
    for x in d.get('items',[]):
     meta=(x.get('pagemap') or {}).get('metatags') or [{}]
     m=meta[0] if meta else {}
     date=next((m.get(k) for k in ('article:published_time','datepublished','date','pubdate','og:updated_time') if m.get(k)), '')
     add(a,x.get('title'),x.get('snippet'),x.get('link'),date,'Google 검색','검색/웹')
   except Exception as e:print('cse',repr(e));break

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
   if len(x)>=35 and x not in paras:paras.append(x)
  text=' '.join(paras)
  if len(text)<180 and p.meta:text=clean(' '.join(p.meta))
  return text[:4500]
 except Exception as e:
  print('article fetch',url[:80],repr(e));return ''

def analyze(title,snip,c,article_text=""):
 fallback=(article_text[:900] if article_text else snip[:360]) or '기사 검색요약에 확인 가능한 기술 내용입니다.';ks=[x for x in TERMS if x in (title+' '+snip).lower()][:6] or [c]
 ep=os.getenv('AZURE_OPENAI_ENDPOINT','').rstrip('/');key=os.getenv('AZURE_OPENAI_API_KEY');dep=os.getenv('AZURE_OPENAI_DEPLOYMENT')
 if not(ep and key and dep):return title,fallback,ks
 source_text=(article_text[:4000] if article_text else snip)
 prompt='제공된 기사 본문 또는 검색요약에 있는 사실만 사용해 한국어로 정리. 없는 사실은 만들지 말 것. JSON만 출력 {\"titleKo\":\"\",\"articleSummaryKo\":\"\",\"keywords\":[]}. articleSummaryKo는 해당 자료의 구체적 핵심내용 2~3문장 260자 이하. keywords는 실제 확인되는 기술어 3~6개. 제목:'+title+' 본문/요약:'+source_text
 body=json.dumps({'messages':[{'role':'system','content':'가전 전장 기술 편집자'},{'role':'user','content':prompt}],'temperature':0,'response_format':{'type':'json_object'}}).encode()
 try:
  u=f'{ep}/openai/deployments/{dep}/chat/completions?api-version=2024-10-21';d=json.loads(fetch(u,{'Content-Type':'application/json','api-key':key,'User-Agent':UA},body));o=json.loads(d['choices'][0]['message']['content']);return clean(o.get('titleKo')) or title,clean(o.get('articleSummaryKo')) or fallback,[clean(str(x)) for x in o.get('keywords',[])][:6] or ks
 except Exception as e:print('ai',repr(e));return title,fallback,ks
def old(a):
 try:
  for x in json.load(open(OUT,encoding='utf-8')).get('items',[]):add(a,x.get('originalTitle') or x.get('title'),x.get('summary'),x.get('url'),x.get('published',''),x.get('source',''),x.get('sourceType',''))
 except:pass
def main():
 a=[];gnews(a);naver(a);cse(a);old(a);a.sort(key=lambda x:x['score'],reverse=True);out=[];seen=set();seen_titles=[];srcn={}
 for x in a:
  if not within_last_week(x.get('published','')):continue
  k=''.join(re.findall(r'[a-z0-9가-힣]+',x['title'].lower()))[:100]
  tokens=title_tokens(x['title'])
  if not k or k in seen or duplicate_title(x['title'],seen_titles) or srcn.get(x['source'],0)>=6:continue
  seen.add(k);seen_titles.append(x['title']);srcn[x['source']]=srcn.get(x['source'],0)+1;c=cat(x['title']+' '+x['snippet']);article_text=get_article_text(x['url']);t,s,kw=analyze(x['title'],x['snippet'],c,article_text);out.append({'category':c,'title':t,'originalTitle':x['title'],'source':x['source'],'sourceType':x['sourceType'],'summary':s,'keywords':kw,'rating':5 if x['score']>=6 else 4 if x['score']>=3 else 3,'url':x['url'],'published':x['published']})
  if len(out)>=MAX_ITEMS:break
 # Last mandatory check immediately before writing. Never carry stale cards forward.
 out=[x for x in out if within_last_week(x.get('published',''))]
 for x in out:
  x['published']=parse_publish_date(x['published']).isoformat()
 os.makedirs(os.path.dirname(OUT),exist_ok=True)
 payload={'updated':RUN_END.isoformat(),'windowStart':RUN_START.isoformat(),'windowEnd':RUN_END.isoformat(),'issueTitle':f'가전 전장 기술 TOP {len(out)}','searchedCandidates':len(a),'items':out}
 with open(OUT,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print('candidates',len(a),'selected',len(out))
if __name__=='__main__':main()
