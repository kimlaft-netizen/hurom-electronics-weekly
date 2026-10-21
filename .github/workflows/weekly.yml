import os,re,json,html,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
OUT='data/weekly.json';MAX_ITEMS=30;UA='Mozilla/5.0 HUROM-Weekly-V8'
Q=['BLDC PMSM sensorless FOC motor control','motor driver gate driver current sensing MOSFET','Altium PCB artwork routing stackup grounding creepage clearance','SMPS flyback buck LLC transformer snubber compensation','EMI EMC conducted radiated emissions common mode choke','microcontroller firmware embedded C RTOS watchdog bootloader UART PWM ADC','STM32 Renesas Nuvoton Microchip Infineon firmware motor','juicer blender food processor motor electronics']
S=['site:etnews.com 반도체 회로 모터 전원 펌웨어 PCB EMI','site:e4ds.com BLDC MCU SMPS PCB EMI 전력반도체','site:rohm.co.kr 모터드라이버 MOSFET 전원IC MCU','site:st.com BLDC PMSM motor control STM32','site:ti.com motor control gate driver current sensing','site:infineon.com motor control MOSFET PSoC','site:renesas.com motor control MCU inverter firmware','site:nxp.com motor control MCU','site:onsemi.com motor driver MOSFET','site:microchip.com motor control embedded C','site:resources.altium.com PCB layout stackup EMC','site:blog.naver.com BLDC PCB SMPS EMI 펌웨어','site:tistory.com BLDC Altium PCB SMPS EMI firmware','site:eevblog.com PCB SMPS EMI motor control','site:electronics.stackexchange.com BLDC PCB SMPS EMI microcontroller']
BLOCK=['english as a second language','second language','제2언어','영어 교육','language education','automotive','electric vehicle','3300v','3.3kv','6.5kv','market size','market forecast','market share','stock','investment','2035','2036','job vacancy']
TERMS=['bldc','pmsm','sensorless','foc','bemf','motor','모터','driver','current sensing','mosfet','mcu','firmware','펌웨어','embedded c','watchdog','rtos','pwm','adc','uart','altium','pcb','artwork','routing','stackup','creepage','clearance','grounding','smps','flyback','buck','llc','snubber','emi','emc','노이즈','회로','전원','반도체']
def fetch(u,h=None,d=None):
 r=urllib.request.Request(u,data=d,headers=h or {'User-Agent':UA});return urllib.request.urlopen(r,timeout=45).read()
def clean(s):return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(s or ''))).strip()

def within_last_week(date_text):
 if not date_text: return False
 now=datetime.now(timezone.utc); cutoff=now-timedelta(days=7)
 try:
  d=parsedate_to_datetime(date_text)
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return cutoff <= d.astimezone(timezone.utc) <= now
 except Exception:
  try:
   t=str(date_text).strip()
   if re.fullmatch(r'\d{8}',t): d=datetime.strptime(t,'%Y%m%d').replace(tzinfo=timezone.utc)
   else: d=datetime.fromisoformat(t.replace('Z','+00:00'))
   if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
   return cutoff <= d.astimezone(timezone.utc) <= now
  except Exception:return False

def rel(t):
 h=t.lower()
 if any(x in h for x in BLOCK):return 0
 return sum(x in h for x in TERMS)
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
 if title and url and score and within_last_week(date):a.append({'title':title,'snippet':snip,'url':url,'published':date,'source':src or urllib.parse.urlparse(url).netloc,'sourceType':typ,'score':score})
def gnews(a):
 for q in S+Q:
  try:
   u='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q+' when:7d','hl':'ko','gl':'KR','ceid':'KR:ko'});root=ET.fromstring(fetch(u))
   for n in root.findall('.//item')[:100]:
    raw=clean(n.findtext('title'));src=raw.rsplit(' - ',1)[1] if ' - ' in raw else '';title=raw.rsplit(' - ',1)[0];add(a,title,n.findtext('description'),clean(n.findtext('link')),clean(n.findtext('pubDate')),src,'검색/전문매체')
  except Exception as e:print('gnews',repr(e))
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
    for x in d.get('items',[]):add(a,x.get('title'),x.get('snippet'),x.get('link'))
   except Exception as e:print('cse',repr(e));break
def analyze(title,snip,c):
 fallback=snip[:360] or '기사 검색요약에 확인 가능한 기술 내용입니다.';ks=[x for x in TERMS if x in (title+' '+snip).lower()][:6] or [c]
 ep=os.getenv('AZURE_OPENAI_ENDPOINT','').rstrip('/');key=os.getenv('AZURE_OPENAI_API_KEY');dep=os.getenv('AZURE_OPENAI_DEPLOYMENT')
 if not(ep and key and dep):return title,fallback,ks
 prompt='검색 메타정보만 근거로 한국어로 정리. 없는 사실은 만들지 말 것. JSON만 출력 {"titleKo":"","articleSummaryKo":"","keywords":[]}. summary는 실제 핵심 2~3문장 260자 이하, keywords는 실제 확인되는 기술어 3~6개. 제목:'+title+' 요약:'+snip
 body=json.dumps({'messages':[{'role':'system','content':'가전 전장 기술 편집자'},{'role':'user','content':prompt}],'temperature':0,'response_format':{'type':'json_object'}}).encode()
 try:
  u=f'{ep}/openai/deployments/{dep}/chat/completions?api-version=2024-10-21';d=json.loads(fetch(u,{'Content-Type':'application/json','api-key':key,'User-Agent':UA},body));o=json.loads(d['choices'][0]['message']['content']);return clean(o.get('titleKo')) or title,clean(o.get('articleSummaryKo')) or fallback,[clean(str(x)) for x in o.get('keywords',[])][:6] or ks
 except Exception as e:print('ai',repr(e));return title,fallback,ks
def old(a):
 try:
  for x in json.load(open(OUT,encoding='utf-8')).get('items',[]):add(a,x.get('originalTitle') or x.get('title'),x.get('summary'),x.get('url'),x.get('published',''),x.get('source',''),x.get('sourceType',''))
 except:pass
def main():
 a=[];gnews(a);naver(a);cse(a);old(a);a.sort(key=lambda x:x['score'],reverse=True);out=[];seen=set();srcn={}
 for x in a:
  k=''.join(re.findall(r'[a-z0-9가-힣]+',x['title'].lower()))[:100]
  if not k or k in seen or srcn.get(x['source'],0)>=6:continue
  seen.add(k);srcn[x['source']]=srcn.get(x['source'],0)+1;c=cat(x['title']+' '+x['snippet']);t,s,kw=analyze(x['title'],x['snippet'],c);out.append({'category':c,'title':t,'originalTitle':x['title'],'source':x['source'],'sourceType':x['sourceType'],'summary':s,'keywords':kw,'rating':5 if x['score']>=6 else 4 if x['score']>=3 else 3,'url':x['url'],'published':x['published']})
  if len(out)>=MAX_ITEMS:break
 if out:json.dump({'updated':datetime.now(timezone.utc).isoformat(),'issueTitle':f'가전 전장 기술 TOP {len(out)}','searchedCandidates':len(a),'items':out},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print('candidates',len(a),'selected',len(out))
if __name__=='__main__':main()
