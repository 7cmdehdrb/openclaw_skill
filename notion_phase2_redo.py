import os, json, time, datetime, traceback
from urllib import request, parse, error

NOTION_KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
NOTION_VERSION = '2025-09-03'
ROOT_RESEARCH_PAGE = '312bd3c5-5e1b-80d6-be49-e2b6fbbcbc41'
UA='Mozilla/5.0'

HEADERS = {
    'Authorization': f'Bearer {NOTION_KEY}',
    'Notion-Version': NOTION_VERSION,
    'Content-Type': 'application/json'
}

PEER_GROUP = {
    'MRVL':['QCOM','ON'], 'QCOM':['MRVL','ON'], 'ON':['QCOM','MRVL'],
    'MU':['AMD','PLTR'], 'AMD':['MU','PLTR'], 'PLTR':['AMD','MU'],
    'PFE':['DHR','SYK'], 'DHR':['PFE','SYK'], 'SYK':['DHR','PFE'],
    'TRGP':['OXY','EQT'], 'OXY':['TRGP','EQT'], 'EQT':['TRGP','OXY'],
    'MS':['C','AXP'], 'C':['MS','AXP'], 'AXP':['MS','C']
}
TARGETS = ['MRVL','QCOM','ON','MU','AMD','PLTR','PFE','DHR','SYK','TRGP','OXY','EQT','MS','C','AXP']


def http_json(url, method='GET', payload=None, headers=None, timeout=30):
    h = headers.copy() if headers else {}
    if 'User-Agent' not in h:
        h['User-Agent'] = UA
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = request.Request(url, data=data, headers=h, method=method)
    with request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def notion(method, path, payload=None):
    return http_json('https://api.notion.com'+path, method=method, payload=payload, headers=HEADERS, timeout=60)


def search_pages_under_research():
    blocks = notion('GET', f'/v1/blocks/{ROOT_RESEARCH_PAGE}/children?page_size=100')
    out = {}
    for b in blocks.get('results',[]):
        if b.get('type') == 'child_page':
            title = b['child_page'].get('title','')
            tkr = title.split(' ')[0].strip()
            if tkr in TARGETS:
                out[tkr] = {'id': b['id'], 'title': title}
    return out


def archive_all_children(page_id):
    res = notion('GET', f'/v1/blocks/{page_id}/children?page_size=100')
    for b in res.get('results',[]):
        try:
            notion('PATCH', f"/v1/blocks/{b['id']}", {'archived': True})
        except Exception:
            pass


def chunk_text(s, n=1800):
    s = s or ''
    out = []
    while s:
        out.append(s[:n])
        s = s[n:]
    return out or ['']


def rich_text(text):
    return [{"type":"text","text":{"content":t}} for t in chunk_text(text)]


def append_blocks(page_id, blocks):
    for i in range(0, len(blocks), 80):
        notion('PATCH', f'/v1/blocks/{page_id}/children', {'children': blocks[i:i+80]})


def fmt_num(v, pct=False):
    if v is None:
        return 'N/A'
    try:
        v=float(v)
        if pct:
            return f"{v*100:.1f}%"
        av = abs(v)
        if av >= 1e12: return f"{v/1e12:.2f}T"
        if av >= 1e9: return f"{v/1e9:.2f}B"
        if av >= 1e6: return f"{v/1e6:.2f}M"
        return f"{v:,.2f}"
    except Exception:
        return str(v)


def yahoo_quote(ticker):
    modules='assetProfile,price,defaultKeyStatistics,financialData,recommendationTrend,summaryDetail'
    url=f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules={modules}'
    j=http_json(url, headers={'User-Agent':UA}, timeout=25)
    r=j.get('quoteSummary',{}).get('result')
    if not r:
        return {}
    m=r[0]
    def gv(path, default=None):
        cur=m
        for p in path.split('.'):
            if not isinstance(cur,dict) or p not in cur:
                return default
            cur=cur[p]
        if isinstance(cur,dict) and 'raw' in cur:
            return cur['raw']
        return cur
    return {
        'longName': gv('price.longName') or gv('price.shortName') or ticker,
        'sector': gv('assetProfile.sector'),
        'industry': gv('assetProfile.industry'),
        'employees': gv('assetProfile.fullTimeEmployees'),
        'marketCap': gv('price.marketCap'),
        'currency': gv('price.currency') or 'USD',
        'price': gv('price.regularMarketPrice'),
        'website': gv('assetProfile.website'),
        'pe': gv('summaryDetail.trailingPE') or gv('defaultKeyStatistics.trailingPE'),
        'fpe': gv('summaryDetail.forwardPE') or gv('defaultKeyStatistics.forwardPE'),
        'roe': gv('financialData.returnOnEquity'),
        'eps': gv('defaultKeyStatistics.trailingEps'),
        'de': gv('financialData.debtToEquity'),
        'ev_ebitda': gv('defaultKeyStatistics.enterpriseToEbitda'),
        'fcf': gv('financialData.freeCashflow'),
        'rev_growth': gv('financialData.revenueGrowth'),
        'op_margin': gv('financialData.operatingMargins'),
        'n_analyst': gv('financialData.numberOfAnalystOpinions'),
        'target_mean': gv('financialData.targetMeanPrice'),
        'target_high': gv('financialData.targetHighPrice'),
        'target_low': gv('financialData.targetLowPrice'),
        'recommendation': gv('financialData.recommendationKey'),
        'recommendation_mean': gv('financialData.recommendationMean'),
    }


def yahoo_timeseries(ticker):
    now=int(time.time())
    p1=now-8*365*24*3600
    types=['annualTotalRevenue','annualOperatingIncome','annualNetIncome','annualFreeCashFlow']
    u='https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/'+ticker
    u+='?'+parse.urlencode({'type':','.join(types),'period1':p1,'period2':now})
    j=http_json(u, headers={'User-Agent':UA}, timeout=25)
    arr=j.get('timeseries',{}).get('result',[])
    bucket={}
    for item in arr:
        for k,v in item.items():
            if not k.startswith('annual'):
                continue
            for e in v:
                y=datetime.datetime.utcfromtimestamp(e.get('asOfDate',0)).strftime('%Y') if isinstance(e.get('asOfDate'),int) else str(e.get('asOfDate',''))[:4]
                bucket.setdefault(y,{})
                bucket[y][k]=e.get('reportedValue',{}).get('raw')
    ys=sorted(bucket.keys(), reverse=True)[:5]
    out=[]
    for y in ys:
        b=bucket[y]
        out.append((y,b.get('annualTotalRevenue'),b.get('annualOperatingIncome'),b.get('annualNetIncome'),b.get('annualFreeCashFlow')))
    return out


def build_content(ticker):
    info=yahoo_quote(ticker)
    rows=yahoo_timeseries(ticker)
    peers=[ticker]+PEER_GROUP.get(ticker,[])
    ps={tk:yahoo_quote(tk) for tk in peers}

    mcap=info.get('marketCap'); fcf=info.get('fcf')
    fcf_yield=(fcf/mcap) if (fcf and mcap) else None

    style_map={
      'MRVL':'AI 인프라 수요 민감형','QCOM':'모바일+엣지AI 전환형','ON':'자동차/산업 사이클형','MU':'메모리 업사이클 탄력형','AMD':'점유율 확대 실행형','PLTR':'소프트웨어 고밸류 성장형','PFE':'파이프라인 재평가형','DHR':'품질+인수 통합형','SYK':'의료기기 점진 성장형','TRGP':'미드스트림 현금흐름형','OXY':'유가 레버리지형','EQT':'가스 가격 연동형','MS':'IB/자산관리 복합형','C':'리스트럭처링 반등형','AXP':'결제 프리미엄 소비형'
    }

    lines=[]
    lines.append(('h2','1) 회사 개요'))
    lines.append(('p',f"[사실] {info.get('longName',ticker)}({ticker})는 {info.get('sector','N/A')}/{info.get('industry','N/A')} 업종이며, 시가총액은 {fmt_num(info.get('marketCap'))} {info.get('currency','USD')}, 상시 인력은 {info.get('employees','N/A')}명입니다."))
    lines.append(('p',f"[해석] {ticker}는 '{style_map.get(ticker,'멀티팩터')}' 특성이 강해 실적 모멘텀 변화가 밸류에이션보다 주가 방향성을 좌우할 가능성이 큽니다."))

    lines.append(('h2','2) 매출 구성(사업부/지역/제품)'))
    lines.append(('p','[사실] Yahoo 공개 API에서는 사업부/지역/제품별 매출 비중을 일관된 구조로 제공하지 않습니다.'))
    lines.append(('p','[한계] 세부 매출 믹스는 최근 10-K/10-Q Segment note 및 IR 자료 수동 검증이 필요합니다.'))

    lines.append(('h2','3) 최근 5년 수익성(매출, 영업이익, 순이익, FCF)'))
    if rows:
        for y, rev, opi, ni, f in rows:
            lines.append(('p',f"[사실][{y}] 매출 {fmt_num(rev)}, 영업이익 {fmt_num(opi)}, 순이익 {fmt_num(ni)}, FCF {fmt_num(f)}"))
    else:
        lines.append(('p','[한계] 최근 5년 시계열 데이터를 충분히 확보하지 못했습니다.'))
    lines.append(('p','[해석] 영업이익률 유지 여부와 FCF의 추세 일치가 이익의 질을 판별하는 핵심입니다.'))

    lines.append(('h2','4) 투자지표(PER, ROE, EPS, 부채비율 + EV/EBITDA, FCF Yield 등)'))
    lines.append(('p',f"[사실] PER {fmt_num(info.get('pe'))}, ROE {fmt_num(info.get('roe'),pct=True)}, EPS {fmt_num(info.get('eps'))}, 부채비율(D/E) {fmt_num(info.get('de'))}, EV/EBITDA {fmt_num(info.get('ev_ebitda'))}, FCF Yield {fmt_num(fcf_yield,pct=True)}"))
    lines.append(('p','[해석] 멀티플의 고저보다 이익 추정치(컨센서스) 상향/하향 전환 시점이 기대수익률에 더 결정적입니다.'))

    lines.append(('h2','5) 경쟁사 비교(밸류·성장·마진·점유율)'))
    for tk in peers:
        p=ps.get(tk,{})
        lines.append(('p',f"[사실] {tk}: PER {fmt_num(p.get('pe'))}, Forward PER {fmt_num(p.get('fpe'))}, 매출성장률 {fmt_num(p.get('rev_growth'),pct=True)}, 영업마진 {fmt_num(p.get('op_margin'),pct=True)}, 시총 {fmt_num(p.get('marketCap'))}"))
    lines.append(('p','[한계] 산업 점유율은 외부 산업리포트(유료 포함) 의존도가 높아 본 자동 수집 범위에서는 제외했습니다.'))

    lines.append(('h2','6) 애널리스트/기관 의견(목표가 변경, 레이팅 추세)'))
    lines.append(('p',f"[사실] 커버 애널리스트 {info.get('n_analyst','N/A')}명, 추천평균 {info.get('recommendation_mean','N/A')} ({info.get('recommendation','N/A')}), 목표가 평균/고가/저가 {info.get('target_mean','N/A')}/{info.get('target_high','N/A')}/{info.get('target_low','N/A')}, 현재가 {info.get('price','N/A')}"))
    lines.append(('p','[해석] 목표가 하향이 연속되는 구간에서는 밸류 정당화보다 이익 하향 리스크 관리가 우선입니다.'))

    lines.append(('h2','7) 어닝콜 핵심 코멘트(가이던스, 리스크, 모멘텀)'))
    lines.append(('p','[사실] 무료 구조화 소스에서 어닝콜 원문/가이던스 문장 단위 데이터는 제한적입니다.'))
    lines.append(('p','[해석] 다음 콜에서는 (1) 가이던스 방향 (2) 재고/주문 추세 (3) 원가·환율 영향 코멘트 3가지를 우선 점검해야 합니다.'))

    lines.append(('h2','8) 리스크 체크리스트(규제, 사이클, 수요, 원가, 지정학)'))
    lines.append(('p',f"[사실] {ticker}는 업종 특성상 경기/수요 사이클, 원가, 금리·환율, 지정학 이벤트에 실적 민감도가 존재합니다."))
    lines.append(('p','[해석] 리스크 점검 순서: 규제/소송 → 수요 둔화 → 원가상승 → 자금조달비용 → 지정학 공급망 이슈.'))

    lines.append(('h2','9) 투자 관점 요약(불/중립/약세 시나리오)'))
    lines.append(('p',f"[불] {ticker}: 매출 성장률 반등과 마진 개선이 동반되면 컨센서스 상향과 함께 리레이팅 가능."))
    lines.append(('p',f"[중립] {ticker}: 성장 둔화와 비용 통제가 균형이면 멀티플 박스권 내 등락 가능."))
    lines.append(('p',f"[약세] {ticker}: 가이던스 하향+마진 훼손이 겹치면 이익 추정치 하향과 변동성 확대 가능."))

    lines.append(('h2','10) 참고 출처 링크'))
    links=[
      f'https://finance.yahoo.com/quote/{ticker}',
      f'https://finance.yahoo.com/quote/{ticker}/financials',
      f'https://finance.yahoo.com/quote/{ticker}/cash-flow',
      f'https://finance.yahoo.com/quote/{ticker}/balance-sheet',
      f'https://finance.yahoo.com/quote/{ticker}/analysis',
      f'https://finance.yahoo.com/quote/{ticker}/key-statistics',
      f'https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=assetProfile,price,defaultKeyStatistics,financialData,recommendationTrend,summaryDetail',
      f'https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{ticker}'
    ]
    if info.get('website'):
      links.append(info['website'])
    for l in links:
      lines.append(('p',l))
    return lines


def to_notion_blocks(lines):
    out=[]
    stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    out.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rich_text(f"업데이트 시각(KST): {stamp}")}})
    out.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rich_text("작성 원칙: [사실]은 데이터 기반, [해석]은 분석 의견입니다.")}})
    for typ,txt in lines:
        if typ=='h2': out.append({"object":"block","type":"heading_2","heading_2":{"rich_text":rich_text(txt)}})
        else: out.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rich_text(txt)}})
    return out


def check_usage_and_maybe_stop(done_count):
    usage=None
    try:
        import subprocess, re
        p=subprocess.run(['codexbar','cost','--provider','codex','--format','json'],capture_output=True,text=True,timeout=20)
        if p.returncode==0:
            m=re.search(r'"dailyUsagePercent"\s*:\s*([0-9.]+)',p.stdout)
            if m: usage=float(m.group(1))
    except Exception:
        pass
    if usage is not None and usage>75:
        title=f'사용량 임계치 초과 중단 ({datetime.date.today().isoformat()})'
        pg=notion('POST','/v1/pages',{'parent':{'page_id':ROOT_RESEARCH_PAGE},'properties':{'title':{'title':[{'type':'text','text':{'content':title}}]}}})
        append_blocks(pg['id'],[
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"중단 사유"}}]}},
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":f"일일 사용량 {usage:.1f}%로 75% 초과. {done_count}개 완료 후 중단."}}]}},
        ])
        return True, usage
    return False, usage


def main():
    mapping=search_pages_under_research()
    updated=[]; failed=[]
    last_complete=None

    for tk in TARGETS:
        if tk not in mapping:
            failed.append((tk,'page_not_found')); continue
        if last_complete:
            el=time.time()-last_complete
            if el<900: time.sleep(900-el)
        pid=mapping[tk]['id']
        try:
            lines=build_content(tk)
            blocks=to_notion_blocks(lines)
            archive_all_children(pid)
            append_blocks(pid,blocks)
            updated.append(tk)
            last_complete=time.time()
            print(f'UPDATED {tk} {datetime.datetime.now().isoformat()}', flush=True)
        except Exception as e:
            failed.append((tk,f'{type(e).__name__}:{e}'))
            print('ERROR',tk,e, flush=True)
            traceback.print_exc()

        if len(updated)%3==0:
            stop,usage=check_usage_and_maybe_stop(len(updated))
            print(f'USAGE_CHECK after {len(updated)} usage={usage}', flush=True)
            if stop:
                break

    result={'updated':updated,'failed':failed,'stopped':len(updated)<len(TARGETS),'timestamp':datetime.datetime.now().isoformat()}
    with open('/home/soyu/.openclaw/workspace/notion_phase2_redo_result.json','w') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print('DONE',json.dumps(result,ensure_ascii=False), flush=True)

if __name__=='__main__':
    main()
