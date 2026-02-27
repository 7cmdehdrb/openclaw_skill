import os, re, json, datetime, time
from urllib import request
import requests
from bs4 import BeautifulSoup

NOTION_KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
NOTION_VERSION='2025-09-03'
ROOT_RESEARCH_PAGE='312bd3c5-5e1b-80d6-be49-e2b6fbbcbc41'
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36'

HEADERS={
    'Authorization':f'Bearer {NOTION_KEY}',
    'Notion-Version':NOTION_VERSION,
    'Content-Type':'application/json'
}

TARGETS=['QCOM','ON','MU','AMD','PLTR','PFE','DHR','SYK','TRGP','OXY','EQT','MS','C','AXP']
PEER_GROUP={
    'QCOM':['MRVL','ON'], 'ON':['QCOM','MRVL'],
    'MU':['AMD','PLTR'], 'AMD':['MU','PLTR'], 'PLTR':['AMD','MU'],
    'PFE':['DHR','SYK'], 'DHR':['PFE','SYK'], 'SYK':['DHR','PFE'],
    'TRGP':['OXY','EQT'], 'OXY':['TRGP','EQT'], 'EQT':['TRGP','OXY'],
    'MS':['C','AXP'], 'C':['MS','AXP'], 'AXP':['MS','C']
}

S=requests.Session(); S.headers.update({'User-Agent':UA})

def notion(method,path,payload=None):
    data=json.dumps(payload).encode('utf-8') if payload is not None else None
    req=request.Request('https://api.notion.com'+path,data=data,headers=HEADERS,method=method)
    with request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

def get_text(url):
    r=S.get(url,timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True)

def first(pattern,text,flags=re.I):
    m=re.search(pattern,text,flags)
    return m.group(1).strip() if m else None

def numlist_from_segment(label,next_label,text,count=6):
    pat=rf'{re.escape(label)}\s+(.+?){re.escape(next_label)}'
    m=re.search(pat,text,re.I)
    if not m:
        return []
    seg=m.group(1)
    nums=re.findall(r'\d{1,3}(?:,\d{3})+',seg)
    return nums[:count]

def fetch_stats(ticker):
    out={'ticker':ticker}
    txt=get_text(f'https://stockanalysis.com/stocks/{ticker.lower()}/statistics/')
    out['price']=first(r'USD\s+([0-9]+\.[0-9]+)',txt)
    out['market_cap']=first(r'market cap or net worth of \$([0-9.,]+\s+[A-Za-z]+)',txt)
    out['pe']=first(r'PE ratio is ([0-9.]+)',txt)
    out['fpe']=first(r'forward PE ratio is ([0-9.]+)',txt)
    out['ev_ebitda']=first(r'EV/EBITDA ratio is ([0-9.]+)',txt)
    out['de']=first(r'Debt / Equity ratio of ([0-9.]+)',txt)
    out['roe']=first(r'Return on equity \(ROE\) is ([0-9.]+%)',txt)
    out['eps']=first(r'Earnings per share was \$([0-9.]+)',txt)
    out['fcf_yield']=first(r'FCF Yield\s+([0-9.]+%)',txt)
    out['target']=first(r'average price target .* is \$([0-9.]+)',txt)
    out['consensus']=first(r'consensus rating is "([A-Za-z]+)"',txt)
    out['analyst_count']=first(r'Analyst Count\s+([0-9]+)',txt)
    out['employees']=first(r'Employee Count\s*([0-9,]+)',txt)
    out['rev_growth_5y']=first(r'Revenue Growth Forecast \(5Y\)\s*([0-9.]+%)',txt)
    out['op_margin']=first(r'Operating Margin\s*([0-9.]+%)',txt)
    out['text']=txt
    return out

def fetch_company_desc(ticker):
    txt=get_text(f'https://stockanalysis.com/stocks/{ticker.lower()}/company/')
    name=first(rf'(.+?)\s*\({ticker}\) Company Profile',txt)
    if not name:
        name=first(rf'(.+?)\s+engages in',txt) or ticker
    desc=first(r'---\s*(.+)',txt,re.S) or txt[:600]
    return name, desc

def fetch_financials_5y(ticker):
    txt=get_text(f'https://stockanalysis.com/stocks/{ticker.lower()}/financials/')
    years=[]
    for y in re.findall(r'FY\s*(20\d{2})',txt):
        if y not in years:
            years.append(y)
        if len(years)>=5:
            break
    if len(years)<5:
        years=['2025','2024','2023','2022','2021']
    rev=numlist_from_segment('Revenue','Revenue Growth',txt,6)
    op=numlist_from_segment('Operating Income','Interest Expense',txt,6)
    ni=numlist_from_segment('Net Income ','Net Income to Common',txt,6) or numlist_from_segment('Net Income','Net Income to Common',txt,6)
    fcf=numlist_from_segment('Free Cash Flow','Free Cash Flow Per Share',txt,6)
    if len(rev)>=6: rev=rev[1:6]
    if len(op)>=6: op=op[1:6]
    if len(ni)>=6: ni=ni[1:6]
    if len(fcf)>=6: fcf=fcf[1:6]
    rows=[]
    for i,y in enumerate(years[:5]):
        rows.append({'year':y,'revenue':rev[i] if i<len(rev) else 'N/A','op_income':op[i] if i<len(op) else 'N/A','net_income':ni[i] if i<len(ni) else 'N/A','fcf':fcf[i] if i<len(fcf) else 'N/A'})
    return rows

def search_pages_under_research():
    blocks=notion('GET',f'/v1/blocks/{ROOT_RESEARCH_PAGE}/children?page_size=100')
    out={}
    for b in blocks.get('results',[]):
        if b.get('type')=='child_page':
            title=b['child_page'].get('title','')
            t=title.split(' ')[0].strip()
            out[t]=b['id']
    return out

def archive_all_children(page_id):
    res=notion('GET',f'/v1/blocks/{page_id}/children?page_size=100')
    for b in res.get('results',[]):
        try:
            notion('PATCH',f"/v1/blocks/{b['id']}",{'archived':True})
        except Exception:
            pass

def rich_chunks(s,n=1800):
    s=s or ''
    return [s[i:i+n] for i in range(0,len(s),n)] or ['']

def rt(s):
    return [{'type':'text','text':{'content':c}} for c in rich_chunks(s)]

def append_blocks(page_id,blocks):
    for i in range(0,len(blocks),80):
        notion('PATCH',f'/v1/blocks/{page_id}/children',{'children':blocks[i:i+80]})

def section_blocks(lines):
    bs=[{"object":"block","type":"paragraph","paragraph":{"rich_text":rt(f"업데이트 시각(KST): {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")}},
        {"object":"block","type":"paragraph","paragraph":{"rich_text":rt("작성 원칙: [사실]은 출처 데이터, [해석]은 분석 의견입니다.")}}]
    for t,x in lines:
        if t=='h2':
            bs.append({"object":"block","type":"heading_2","heading_2":{"rich_text":rt(x)}})
        else:
            bs.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rt(x)}})
    return bs

def build_lines(tk,stats,rows,name,desc,peer_stats):
    lines=[]
    lines.append(('h2','1) 회사 개요'))
    lines.append(('p',f"[사실] {name}({tk})의 최근 시가총액은 약 ${stats.get('market_cap','N/A')}이며, 직원 수는 {stats.get('employees','N/A')}명, 최근 주가는 ${stats.get('price','N/A')}입니다."))
    lines.append(('p',f"[사실] 사업 설명(요약): {desc[:450]}"))
    lines.append(('p',"[해석] 핵심 투자포인트는 성장률(매출/이익)과 멀티플(PER, EV/EBITDA) 간의 괴리 축소 여부입니다."))

    lines.append(('h2','2) 매출 구성(사업부/지역/제품)'))
    lines.append(('p',"[사실] 무료 공개 소스(StockAnalysis 요약)에는 사업부/지역 매출 비중이 구조화되어 있지 않아, 본문은 회사 설명 중심으로 정리했습니다."))
    lines.append(('p',"[한계] 정확한 세그먼트 비중은 최신 10-K/10-Q의 Segment 주석 및 IR 프레젠테이션 확인이 필요합니다."))

    lines.append(('h2','3) 최근 5년 수익성(매출, 영업이익, 순이익, FCF)'))
    for r in rows:
        lines.append(('p',f"[사실][FY{r['year']}] 매출 ${r['revenue']}M, 영업이익 ${r['op_income']}M, 순이익 ${r['net_income']}M, FCF ${r['fcf']}M"))
    lines.append(('p',"[해석] 매출 증가와 FCF 동행 여부를 통해 성장의 질(회계이익 vs 현금이익)을 점검할 필요가 있습니다."))

    lines.append(('h2','4) 투자지표(PER, ROE, EPS, 부채비율 + EV/EBITDA, FCF Yield 등)'))
    lines.append(('p',f"[사실] PER {stats.get('pe','N/A')}, Forward PER {stats.get('fpe','N/A')}, ROE {stats.get('roe','N/A')}, EPS ${stats.get('eps','N/A')}, D/E {stats.get('de','N/A')}, EV/EBITDA {stats.get('ev_ebitda','N/A')}, FCF Yield {stats.get('fcf_yield','N/A')}"))
    lines.append(('p',"[해석] 고평가/저평가 판단은 절대 배수보다 이익 추정치 상향·하향 전환과 함께 해석하는 것이 유효합니다."))

    lines.append(('h2','5) 경쟁사 비교(밸류·성장·마진·점유율)'))
    for p in peer_stats:
        lines.append(('p',f"[사실] {p['ticker']}: 시총 ${p.get('market_cap','N/A')}, PER {p.get('pe','N/A')}, Fwd PER {p.get('fpe','N/A')}, 운영마진 {p.get('op_margin','N/A')}, 5Y 매출성장 전망 {p.get('rev_growth_5y','N/A')}"))
    lines.append(('p',"[한계] 점유율 데이터는 유료 산업리포트 비중이 높아 본 자동 업데이트 범위에서 제외했습니다."))

    lines.append(('h2','6) 애널리스트/기관 의견(목표가 변경, 레이팅 추세)'))
    lines.append(('p',f"[사실] 컨센서스 {stats.get('consensus','N/A')}, 평균 목표가 ${stats.get('target','N/A')}, 커버 애널리스트 수 {stats.get('analyst_count','N/A')}명."))
    lines.append(('p',"[해석] 목표가 상향보다 실적 가이던스 상향의 지속성이 주가 추세 유지에 더 중요합니다."))

    lines.append(('h2','7) 어닝콜 핵심 코멘트(가이던스, 리스크, 모멘텀)'))
    lines.append(('p',"[사실] 자동 수집 범위에서는 어닝콜 전문/문장 단위 인용 데이터가 제한적입니다."))
    lines.append(('p',"[해석] 다음 실적 시즌에는 수요 가시성, 마진 가이던스, CAPEX/재고 코멘트를 최우선 체크포인트로 삼아야 합니다."))

    lines.append(('h2','8) 리스크 체크리스트(규제, 사이클, 수요, 원가, 지정학)'))
    lines.append(('p',"[사실] 공통 리스크: 경기 민감도, 고객/제품 집중도, 금리·환율, 공급망/원자재, 규제·소송 이슈."))
    lines.append(('p',"[해석] 다운사이드 관리의 핵심은 (1) 실적 추정치 하향 속도 (2) 밸류 축소 탄력 (3) 재무레버리지 부담입니다."))

    lines.append(('h2','9) 투자 관점 요약(불/중립/약세 시나리오)'))
    lines.append(('p',f"[불] {tk}: 실적 상향 + 멀티플 유지/확대 시 리레이팅 가능."))
    lines.append(('p',f"[중립] {tk}: 성장 둔화와 비용 통제가 균형일 경우 박스권 흐름."))
    lines.append(('p',f"[약세] {tk}: 가이던스 하향 및 마진 압박 동시 발생 시 변동성 확대."))

    lines.append(('h2','10) 참고 출처 링크'))
    links=[
        f'https://stockanalysis.com/stocks/{tk.lower()}/',
        f'https://stockanalysis.com/stocks/{tk.lower()}/company/',
        f'https://stockanalysis.com/stocks/{tk.lower()}/financials/',
        f'https://stockanalysis.com/stocks/{tk.lower()}/statistics/',
        f'https://stockanalysis.com/stocks/{tk.lower()}/financials/balance-sheet/',
        f'https://stockanalysis.com/stocks/{tk.lower()}/financials/cash-flow-statement/',
        f'https://stockanalysis.com/stocks/{tk.lower()}/forecast/',
        f'https://www.sec.gov/edgar/search/#/q={tk}'
    ]
    for l in links:
        lines.append(('p',l))
    return lines


def main():
    page_map=search_pages_under_research()
    updated=[]; failed=[]
    for tk in TARGETS:
        pid=page_map.get(tk)
        if not pid:
            failed.append((tk,'page_not_found')); continue
        try:
            st=fetch_stats(tk)
            rows=fetch_financials_5y(tk)
            name,desc=fetch_company_desc(tk)
            peers=[tk]+PEER_GROUP.get(tk,[])
            peer_stats=[]
            for p in peers:
                try:
                    peer_stats.append(fetch_stats(p))
                    time.sleep(0.3)
                except Exception:
                    peer_stats.append({'ticker':p,'market_cap':'N/A','pe':'N/A','fpe':'N/A','op_margin':'N/A','rev_growth_5y':'N/A'})
            lines=build_lines(tk,st,rows,name,desc,peer_stats)
            blocks=section_blocks(lines)
            archive_all_children(pid)
            append_blocks(pid,blocks)
            updated.append(tk)
            print('UPDATED',tk,flush=True)
            time.sleep(0.5)
        except Exception as e:
            failed.append((tk,f'{type(e).__name__}:{e}'))
            print('FAILED',tk,e,flush=True)
    result={'updated':updated,'failed':failed,'timestamp':datetime.datetime.now().isoformat()}
    with open('/home/soyu/.openclaw/workspace/notion_phase2_retry_alt_sources_result.json','w') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    main()
