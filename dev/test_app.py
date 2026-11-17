# 헤아림 전체 흐름 시험: python3 test_app.py  (가짜 데이터베이스와 가짜 파이어베이스 SDK로 돌림 — 실제 규칙은 실제 프로젝트에서 한 번 더 확인)
import subprocess, sys, os, time, json, re, urllib.request
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); SHOTS=os.environ.get('SHOTS','')
web=subprocess.Popen([sys.executable,'-m','http.server','8930','--bind','127.0.0.1','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
db=subprocess.Popen([sys.executable,os.path.join(HERE,'mockdb.py'),'8931'])
time.sleep(1.2)
DBU='http://127.0.0.1:8931'; APP='http://127.0.0.1:8930/index.html'
CFG="window.HEARIM_CONFIG={apiKey:'x',authDomain:'x',databaseURL:'%s',projectId:'x'};"%DBU
STUB=open(os.path.join(HERE,'fbstub.js'),encoding='utf-8').read()
ok=True
def check(l,c,x=''):
    global ok; ok=ok and bool(c); print(('✔' if c else '✘'),l,x)
def dbget(p): return json.loads(urllib.request.urlopen(DBU+'/'+p+'.json').read())
def dbput(p,v,auth=''):
    r=urllib.request.Request(DBU+'/'+p+'.json'+('?auth='+auth if auth else ''),data=json.dumps(v).encode(),method='PUT',headers={'Content-Type':'application/json'}); return urllib.request.urlopen(r).read()
def hl(code):
    h=dbget('polls/%s/meta/hide'%code); return (list(h.values()) if isinstance(h,dict) else h) or []
def setup(ctx):
    ctx.route(re.compile(r'.*/config\.js(\?.*)?$'), lambda r: r.fulfill(body=CFG,content_type='application/javascript'))
    ctx.route(re.compile(r'https://www\.gstatic\.com/firebasejs/.*/firebase-app-compat\.js'), lambda r: r.fulfill(body=STUB,content_type='application/javascript'))
    ctx.route(re.compile(r'https://www\.gstatic\.com/firebasejs/.*/firebase-(auth|database)-compat\.js'), lambda r: r.fulfill(body='',content_type='application/javascript'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    T=b.new_context(viewport={'width':1100,'height':900}); setup(T); T.grant_permissions(['clipboard-read','clipboard-write'],origin='http://127.0.0.1:8930')
    t=T.new_page(); errs=[]; t.on('pageerror',lambda e: errs.append(str(e)))
    t.goto(APP); t.wait_for_timeout(600)
    check('첫 화면: 번호로 참여 · 만들기는 로그인 먼저', t.locator('#hc').count()==1 and t.locator('#lg').count()==1)
    t.fill('#hc','ab'); t.click('#hg'); check('잘못된 번호 안내', '6자리' in t.inner_text('#hm'))
    t.click('#lg'); t.wait_for_timeout(400)
    check('로그인 뒤 만들기 칸', t.locator('#mq').count()==1 and '아직 만든 설문이 없어요' in t.inner_text('#my'))
    t.click('#mc'); check('질문 없이 만들기 막힘', '질문을 적어' in t.inner_text('#mm'))
    t.fill('#mq','어떻게 보여 주면 모두가 꾸준히 뛸까요?')
    for i,o in enumerate(['지금처럼 총 횟수 순위','뛴 날 수 순위']): t.locator('#mo input').nth(i).fill(o)
    t.click('#ma'); t.locator('#mo input').nth(2).fill('평일 5일 달성'); t.click('#ma'); t.locator('#mo input').nth(3).fill('주 500회 적금')
    t.fill('#ml','https://musicalpe.github.io/apps/'); t.fill('#mll','앱 모음 보러 가기')
    t.click('#mc'); t.wait_for_timeout(700)
    code=t.locator('.poll').first.get_attribute('data-code')
    meta=dbget('polls/%s/meta'%code)
    check('설문 만들어짐 (번호 6자리 · 보기 4개 · 열림)', re.match(r'^[a-z0-9]{6}$',code or '') and len(meta['opts'])==4 and meta['open'] is True and meta['owner']=='teacher1', code)
    check('내가 만든 설문 목록', '받는 중' in t.inner_text('.poll') and '답 0명' in t.inner_text('.poll'))
    t.locator('.poll [data-act=copy]').first.click(); t.wait_for_timeout(200)
    check('참여 주소 복사', t.evaluate('navigator.clipboard.readText()').endswith('?p='+code))
    # 결과 화면 (선생님)
    bd=T.new_page(); bd.on('pageerror',lambda e: errs.append(str(e))); bd.goto(APP+'?b='+code); bd.wait_for_timeout(900)
    check('결과 화면: 질문·QR·번호·주인 단추', '꾸준히 뛸까요' in bd.inner_text('#bm') and bd.locator('#bj svg').count()==1 and code in bd.inner_text('#bj') and bd.locator('#bop').count()==1 and bd.locator('#bcl').count()==1)
    check('결과 화면: 0명', '0' in bd.inner_text('.b-count'))
    # 참여자 6명 (로그인 없음, SDK 없음)
    sdk=[]; texts=['하루 빠져도 채울 수 있어서 좋아요','','<b>굵게</b> & "따옴표"','','','무리하지 않아서 좋습니다']; picks=[3,3,2,0,3,1]
    for i in range(6):
        C=b.new_context(viewport={'width':390,'height':800}); setup(C); pg=C.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.on('request',lambda r: sdk.append(r.url) if 'gstatic' in r.url else None)
        pg.goto(APP+'?p='+code); pg.wait_for_timeout(500)
        if i==0:
            check('참여 화면: 질문·보기 4개·내기 단추 잠김', pg.locator('.opt').count()==4 and pg.is_disabled('#js') and pg.locator('#jt').count()==1)
        pg.locator('.opt').nth(picks[i]).click()
        if texts[i]: pg.fill('#jt',texts[i])
        pg.click('#js'); pg.wait_for_timeout(500)
        if i==0:
            check('낸 뒤: 고마워요 · 결과 · 끝난 뒤 주소 단추', '고마워요' in pg.inner_text('#jc') and '지금까지 1명' in pg.inner_text('#jr').replace('\n',' ') and pg.locator('a.btn.main').get_attribute('href')=='https://musicalpe.github.io/apps/' and '앱 모음 보러 가기' in pg.inner_text('#jc'))
            if SHOTS: pg.screenshot(path=SHOTS+'/ha_join.png')
            pg.reload(); pg.wait_for_timeout(500); check('다시 열면 낸 상태 그대로', '고마워요' in pg.inner_text('#jc'))
            pg.click('#jch'); pg.locator('.opt').nth(2).click(); pg.click('#js'); pg.wait_for_timeout(400)
            check('답 바꾸기 → 한 사람은 한 표', len(dbget('polls/%s/votes'%code))==1 and list(dbget('polls/%s/votes'%code).values())[0]['c']==2)
            pg.click('#jch'); pg.locator('.opt').nth(3).click(); pg.click('#js'); pg.wait_for_timeout(400)
            keep=pg
        else: C.close()
    check('참여 화면은 파이어베이스 SDK를 불러오지 않음', not sdk, str(sdk[:1]))
    bd.wait_for_timeout(900); tx=bd.inner_text('#bm')
    check('결과 화면 실시간: 6명 · 주 500회 적금 3명 50%', '6' in bd.inner_text('.b-count') and '3명 · 50%' in tx and bd.locator('.bar.lead').count()==1 and '주 500회 적금' in bd.inner_text('.bar.lead'), bd.inner_text('.bar.lead').replace('\n',' '))
    check('한 줄 의견 3개 · 꺾쇠는 글자로만', bd.locator('.b-cmts .cmt').count()==3 and bd.locator('.b-cmts b').count()==0 and '<b>굵게</b>' in bd.inner_text('.b-cmts'))
    if SHOTS: bd.set_viewport_size({'width':1600,'height':900}); bd.wait_for_timeout(300); bd.screenshot(path=SHOTS+'/ha_board.png')
    # 발표 모드
    bd.click('#bsh'); bd.wait_for_timeout(250)
    check('발표 모드: 로고·단추 숨고 질문·QR·막대는 그대로 · 주소에 show=1', not bd.locator('.b-top').is_visible() and bd.locator('#bj svg').is_visible() and bd.locator('.bar').count()==4 and bd.locator('.b-q').is_visible() and 'show=1' in bd.url and '?b='+code in bd.url)
    if SHOTS: bd.set_viewport_size({'width':1600,'height':900}); bd.wait_for_timeout(300); bd.screenshot(path=SHOTS+'/ha_show.png')
    bd.keyboard.press('Escape'); bd.wait_for_timeout(200); e1=bd.locator('.b-top').is_visible() and 'show=1' not in bd.url
    bd.click('#bsh'); bd.wait_for_timeout(200); bd.click('#bx'); bd.wait_for_timeout(200)
    check('발표 모드 끝내기 (Esc · 단추)', e1 and bd.locator('.b-top').is_visible() and 'show=1' not in bd.url)
    sh=bd.context.new_page(); sh.goto(APP+'?b='+code+'&show=1'); sh.wait_for_timeout(900)
    check('발표 모드 주소로 바로 열기: 답이 실시간으로 보임', not sh.locator('.b-top').is_visible() and '6' in sh.inner_text('.b-count') and sh.locator('#bj svg').is_visible()); sh.close()
    bd.click('#bcm'); bd.wait_for_timeout(200); check('한 줄 의견 숨김', bd.locator('.b-cmts').count()==0); bd.click('#bcm')
    # 남이 연 결과 화면에는 주인 단추가 없음
    O=b.new_context(viewport={'width':1100,'height':800}); setup(O); ob=O.new_page(); ob.goto(APP+'?b='+code); ob.wait_for_timeout(900)
    check('다른 사람의 결과 화면: 보기만 (마감·지우기 단추 없음)', '6' in ob.inner_text('.b-count') and ob.locator('#bop').count()==0 and ob.locator('#bcl').count()==0)
    # 마감
    bd.click('#bop'); bd.wait_for_timeout(700)
    check('마감하기 → 결과 화면에 마감 표시', bd.locator('.b-closed').count()==1 and dbget('polls/%s/meta/open'%code) is False)
    keep.click('#jch') if keep.locator('#jch').count() else None; 
    if keep.locator('#js').count():
        keep.locator('.opt').nth(0).click(); keep.click('#js'); keep.wait_for_timeout(700)
        check('마감 뒤 낸 답은 막히고 마감 안내', '마감' in keep.inner_text('#jc') and len(dbget('polls/%s/votes'%code))==6 and sorted(v['c'] for v in dbget('polls/%s/votes'%code).values())==[0,1,2,3,3,3])
    C=b.new_context(viewport={'width':390,'height':800}); setup(C); late=C.new_page(); late.goto(APP+'?p='+code); late.wait_for_timeout(500)
    check('마감 뒤 들어온 사람: 마감 안내와 결과', '마감됐어요' in late.inner_text('#jc') and late.locator('.opt').count()==0 and '6명' in late.inner_text('#jr').replace('\n',' '))
    # 없는 번호
    late.goto(APP+'?p=zzzzzz'); late.wait_for_timeout(500); check('없는 번호: 찾지 못했어요', '찾지 못했어요' in late.inner_text('#jc'))
    # 남이 주인인 척 못 함 (가짜 규칙)
    ob.goto(APP); ob.wait_for_timeout(400); ob.evaluate("window.__STUB_LOGIN_AS='intruder'"); ob.click('#lg'); ob.wait_for_timeout(400)
    r=ob.evaluate("fetch('%s/polls/%s/votes.json?auth=intruder',{method:'DELETE'}).then(r=>r.status)"%(DBU,code))
    check('다른 선생님은 내 설문 답을 못 지움 · 내 목록에도 안 보임', r==401 and '아직 만든 설문이 없어요' in ob.inner_text('#my'))
    # 다시 받기 · 답 지우기 · 내려받기 · 지우기
    t.reload(); t.wait_for_timeout(700)
    check('목록: 마감 · 답 6명', '마감' in t.inner_text('.poll') and '답 6명' in t.inner_text('.poll'))
    # 고치기 (답이 6명 있는 설문)
    t.locator('.poll [data-act=edit]').first.click(); t.wait_for_timeout(200)
    check('고치기: 칸에 내용이 채워지고 · 답이 있어 보기 빼기는 잠김', t.input_value('#mq')=='어떻게 보여 주면 모두가 꾸준히 뛸까요?' and t.locator('#mo input').count()==4 and t.locator('#mo button:disabled').count()==4 and '6명' in t.inner_text('#me') and t.input_value('#ml')=='https://musicalpe.github.io/apps/' and '고친 내용 저장' in t.inner_text('#mc'))
    t.locator('#mo input').nth(1).fill(''); t.click('#mc'); e0='비울 수 없어요' in t.inner_text('#mm')
    t.click('#mx'); t.wait_for_timeout(100)
    check('고치기: 답 있는 보기는 못 비움 · 그만두기 하면 그대로', e0 and t.input_value('#mq')=='' and '설문 만들기' in t.inner_text('#mc') and dbget('polls/%s/meta/q'%code)=='어떻게 보여 주면 모두가 꾸준히 뛸까요?')
    t.locator('.poll [data-act=edit]').first.click(); t.wait_for_timeout(200)
    t.fill('#mq','어떻게 보여 주면 모두가 꾸준히 뛸까요? (고침)'); t.locator('#mo input').nth(1).fill('하루 100회 넘게 뛴 날 수 순위'); t.click('#ma'); t.locator('#mo input').nth(4).fill('잘 모르겠어요'); t.uncheck('#mask')
    t.click('#mc'); t.wait_for_timeout(700); m2=dbget('polls/%s/meta'%code)
    check('고치기 저장: 질문·보기 글·보기 더하기 반영 · 답 6명·마감 상태·주인·번호 그대로', m2['q'].endswith('(고침)') and (m2['opts']['1'] if isinstance(m2['opts'],dict) else m2['opts'][1])=='하루 100회 넘게 뛴 날 수 순위' and len(m2['opts'])==5 and m2['ask'] is False and m2['open'] is False and m2['owner']=='teacher1' and m2['link']=='https://musicalpe.github.io/apps/' and len(dbget('polls/%s/votes'%code))==6 and '(고침)' in t.inner_text('.poll') and '고쳤어요' in t.inner_text('#mm'))
    bd.wait_for_timeout(500); check('고친 내용이 열려 있는 결과 화면에 바로 반영', '(고침)' in bd.inner_text('.b-q') and bd.locator('.bar').count()==5 and '3명 · 50%' in bd.inner_text('.bar.lead'))
    with t.expect_download() as dl: t.locator('.poll [data-act=csv]').first.click()
    csv=open(dl.value.path(),encoding='utf-8-sig').read()
    check('답 내려받기 (6줄 · 연락처 같은 건 없음)', csv.count('\n')==7 and '주 500회 적금' in csv and '하루 빠져도' in csv, dl.value.suggested_filename)
    t.locator('.poll [data-act=open]').first.click(); t.wait_for_timeout(600); check('다시 받기', dbget('polls/%s/meta/open'%code) is True and '받는 중' in t.inner_text('.poll'))
    bd.wait_for_timeout(600); bd.click('#bcl'); check('답 지우기는 한 번 더 눌러야', '한 번 더' in bd.inner_text('#bcl') and len(dbget('polls/%s/votes'%code))==6)
    bd.click('#bcl'); bd.wait_for_timeout(800); check('답 지우기 → 0명', dbget('polls/%s/votes'%code) is None and '0' in bd.inner_text('.b-count'))
    t.locator('.poll [data-act=del]').first.click(); t.locator('.poll [data-act=del]').first.click(); t.wait_for_timeout(900)
    check('설문 지우기', dbget('polls/%s'%code) is None and '아직 만든 설문이 없어요' in t.inner_text('#my'))
    # ===== 적어서 내기 (답 구름) =====
    t.check('#mt1'); t.wait_for_timeout(100)
    e0=(not t.locator('#mpk').is_visible()) and t.locator('#mmx').is_visible()
    t.fill('#mq','체육 시간에 가장 하고 싶은 것은?'); t.select_option('#mmx','3'); t.click('#mc'); t.wait_for_timeout(700)
    tc=t.locator('.poll').first.get_attribute('data-code'); tm=dbget('polls/%s/meta'%tc)
    check('적어서 내기 만들기: 보기 칸 숨고 답 수 고르기 · 저장(보기 없음·답 3개까지)', e0 and tm.get('type')=='text' and tm.get('max')==3 and 'opts' not in tm and tm['open'] is True and '적어서 내기' in t.inner_text('.poll'))
    tb=T.new_page(); tb.on('pageerror',lambda e: errs.append(str(e))); tb.goto(APP+'?b='+tc); tb.wait_for_timeout(900)
    check('적어서 내기 결과 화면: 0명 · 적어 주세요 안내 · 한 줄 의견 단추 없음', '0' in tb.inner_text('.b-count') and '적어 주세요' in tb.inner_text('#bhow') and tb.locator('#bcm').count()==0 and tb.locator('#bop').count()==1)
    answers=[['피구','줄넘기'],['피구!'],[' 피 구 ','달리기','★축구★ <3'],['줄넘기','!!! ^^'],['PIGU','pigu']]
    for i,ans in enumerate(answers):
        C=b.new_context(viewport={'width':390,'height':800}); setup(C); pg=C.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.goto(APP+'?p='+tc); pg.wait_for_timeout(500)
        if i==0: check('적어서 내기 참여 화면: 답 칸 3개 · 20자까지 · 빈 채로는 못 냄', pg.locator('.ja').count()==3 and pg.locator('.ja').first.get_attribute('maxlength')=='20' and pg.is_disabled('#js') and pg.locator('.opt').count()==0)
        for j,x in enumerate(ans): pg.locator('.ja').nth(j).fill(x)
        pg.click('#js'); pg.wait_for_timeout(500)
        if i==0:
            check('적어서 내기 낸 뒤: 고마워요 · 낸 답 · 구름', '고마워요' in pg.inner_text('#jc') and '피구, 줄넘기' in pg.inner_text('#jc') and pg.locator('#jr .cloud .w').count()==2)
            pg.click('#jch'); e1=pg.locator('.ja').nth(0).input_value()=='피구'; pg.locator('.ja').nth(2).fill('공놀이'); pg.click('#js'); pg.wait_for_timeout(500)
            check('적어서 내기 답 바꾸기: 한 사람은 한 묶음', e1 and len(dbget('polls/%s/votes'%tc))==1)
            pg.click('#jch'); pg.locator('.ja').nth(2).fill(''); pg.click('#js'); pg.wait_for_timeout(500)
        if i==2: tb.wait_for_timeout(700); n3=tb.locator('#bw .w').count()
        C.close() if i<4 else None
    tb.wait_for_timeout(900)
    ws={w.get_attribute('data-k'):w for w in tb.locator('#bw .w').all()}
    fs=lambda k: float(ws[k].evaluate('e=>getComputedStyle(e).fontSize').replace('px',''))
    check('답 구름: 5명 · 기호는 빠지고(기호뿐인 답은 버림) · 띄어쓰기·대소문자만 다른 답은 한데 모임 (피구 3 · 줄넘기 2 · 한 사람이 같은 답 두 번은 한 번)', '5' in tb.inner_text('.b-count') and set(ws)=={'피구','줄넘기','달리기','축구3','pigu'} and '3' in ws['피구'].inner_text() and '2' in ws['줄넘기'].inner_text() and ws['pigu'].locator('sup').inner_text()=='', str(sorted(ws)))
    check('답 구름: 많이 나온 답일수록 글씨가 큼 · 가장 많은 답은 노란색 · 기호 없음', fs('피구')>fs('줄넘기')>fs('달리기') and 'lead' in ws['피구'].get_attribute('class') and '★' not in tb.inner_text('#bw') and '<' not in tb.inner_text('#bw') and '!' not in tb.inner_text('#bw') and '축구 3' in tb.inner_text('#bw'), '%s %s %s'%(fs('피구'),fs('줄넘기'),fs('달리기')))
    check('답 구름: 새 답은 뒤에 새로 나타남 (있던 글자는 그대로)', n3==4 and 'new' in ws['pigu'].get_attribute('class') and tb.locator('#bw .w').last.get_attribute('data-k')=='pigu')
    if SHOTS: tb.set_viewport_size({'width':1600,'height':900}); tb.wait_for_timeout(300); tb.screenshot(path=SHOTS+'/ha_cloud.png')
    # 다른 사람은 못 숨김 · 주인은 눌러서 숨김 · 되살리기
    ws['달리기'].click(); tb.wait_for_timeout(600)
    check('주인이 글자를 누르면 숨김 · 되살리기 단추', tb.locator('#bw .w[data-k="달리기"]').count()==0 and tb.locator('#bw .w').count()==4 and list((dbget('polls/%s/meta/hide'%tc) or {}).values() if isinstance(dbget('polls/%s/meta/hide'%tc),dict) else dbget('polls/%s/meta/hide'%tc))==['달리기'] and '1개' in tb.inner_text('#bun'))
    anon=b.new_context(viewport={'width':1200,'height':800}); setup(anon); ap=anon.new_page(); ap.goto(APP+'?b='+tc); ap.wait_for_timeout(900)
    ap.locator('#bw .w').first.click(); ap.wait_for_timeout(400)
    check('다른 사람의 답 구름: 보기만 (눌러도 안 숨겨짐 · 숨긴 답은 안 보임)', ap.locator('#bw .w').count()==4 and ap.locator('#bun').count()==0 and len(dbget('polls/%s/meta/hide'%tc))==1); anon.close()
    tb.click('#bsh'); tb.wait_for_timeout(200); e2=(not tb.locator('.b-top').is_visible()) and tb.locator('#bw .w').count()==4; tb.click('#bx'); tb.wait_for_timeout(200)
    tb.click('#bun'); tb.wait_for_timeout(600)
    check('답 구름 발표 모드 · 숨긴 답 되살리기', e2 and tb.locator('#bw .w').count()==5 and dbget('polls/%s/meta/hide'%tc) is None)
    # 고치기(답 수) · 내려받기 · 마감
    t.reload(); t.wait_for_timeout(800)
    t.locator('.poll[data-code="%s"] [data-act=edit]'%tc).click(); t.wait_for_timeout(200)
    e3=t.is_disabled('#mt0') and t.is_checked('#mt1') and t.input_value('#mmx')=='3' and not t.locator('#mpk').is_visible()
    t.select_option('#mmx','1'); t.fill('#mq','체육 시간에 가장 하고 싶은 것은? (한 가지)'); t.click('#mc'); t.wait_for_timeout(700); tm=dbget('polls/%s/meta'%tc)
    check('적어서 내기 고치기: 방식은 못 바꾸고 질문·답 수만 · 답 그대로', e3 and tm['max']==1 and tm['type']=='text' and tm['q'].endswith('(한 가지)') and len(dbget('polls/%s/votes'%tc))==5 and t.is_checked('#mt0') and t.locator('#mpk').is_visible())
    with t.expect_download() as dl: t.locator('.poll[data-code="%s"] [data-act=csv]'%tc).click()
    csv=open(dl.value.path(),encoding='utf-8-sig').read()
    check('적어서 내기 답 내려받기 (5줄)', csv.count('\n')==6 and '줄넘기' in csv and '적은 답' in csv)
    tb.click('#bop'); tb.wait_for_timeout(500); pg.goto(APP+'?p='+tc); pg.wait_for_timeout(600)
    check('적어서 내기 마감: 결과 화면 표시 · 참여 화면은 마감 안내와 구름', '마감' in tb.inner_text('#bq') and '마감됐어요' in pg.inner_text('#jc') and pg.locator('#jr .cloud .w').count()==5)
    pg.context.close()
    armed_del=t.locator('.poll[data-code="%s"] [data-act=del]'%tc); armed_del.click(); armed_del.click(); t.wait_for_timeout(900)
    check('적어서 내기 설문 지우기', dbget('polls/%s'%tc) is None)
    # ===== 거친 말 거르기 =====
    bad=['시발','씨발','ㅅㅂ','병신','시 발','시1발','FUCK you','개새끼','보지','지랄 마']; good=['다시 발표','해보지 뭐','줄넘기','시바견','발야구 하고 싶어요','검색기','잠자지 말자','새우깡','미쳤다 재밌다']
    rb=t.evaluate('(a)=>a.map(isBad)',bad); rg=t.evaluate('(a)=>a.map(isBad)',good)
    check('거친 말 가리기: 거친 말 %d개는 걸리고 · 보통 말 %d개는 통과'%(len(bad),len(good)), all(rb) and not any(rg), '%s %s'%(rb,rg))
    t.check('#mt1'); t.fill('#mq','오늘 체육 어땠나요?'); t.select_option('#mmx','2'); t.click('#mc'); t.wait_for_timeout(700)
    fc=t.locator('.poll').first.get_attribute('data-code')
    for i,a in enumerate([['시발','줄넘기'],['ㅅㅂ'],['다시 발야구'],['시 발'],['새끼손가락']]): dbput('polls/%s/votes/%s'%(fc,'f%015d'%i),{'a':a,'at':{'.sv':'timestamp'}})
    fb=T.new_page(); fb.on('pageerror',lambda e: errs.append(str(e))); fb.goto(APP+'?b='+fc); fb.wait_for_timeout(1000)
    ks=lambda pg: sorted(w.get_attribute('data-k') for w in pg.locator('#bw .w').all())
    check('거친 말은 구름에 안 나옴 · 만든 사람에게 걸러진 답 3개 단추', ks(fb)==['다시발야구','줄넘기'] and '3개' in fb.inner_text('#bfb') and '5' in fb.inner_text('.b-count'), str(ks(fb)))
    fb.click('#bfb'); fb.wait_for_timeout(200); e0='새끼손가락' in fb.inner_text('#bfl') and '시발 · 2명' in fb.inner_text('#bfl')
    fb.locator('#bfl button[data-k="새끼손가락"]').click(); fb.wait_for_timeout(600)
    check('걸러진 답 보기 · 괜찮은 답은 보이기로 되살림', e0 and ks(fb)==['다시발야구','새끼손가락','줄넘기'] and hl(fc)==['+새끼손가락'] and '2개' in fb.inner_text('#bfb'))
    fb.locator('#bw .w[data-k="줄넘기"]').click(); fb.wait_for_timeout(600); e1=ks(fb)==['다시발야구','새끼손가락'] and len(hl(fc))==2
    fb.click('#bun'); fb.wait_for_timeout(600)
    check('숨긴 답 되살리기를 해도 보이기 한 답은 그대로', e1 and ks(fb)==['다시발야구','새끼손가락','줄넘기'] and hl(fc)==['+새끼손가락'])
    an=b.new_context(viewport={'width':1200,'height':800}); setup(an); ap=an.new_page(); ap.goto(APP+'?b='+fc); ap.wait_for_timeout(900)
    jp=an.new_page(); jp.goto(APP+'?p='+fc); jp.wait_for_timeout(500); jp.locator('.ja').first.fill('씨발'); jp.click('#js'); jp.wait_for_timeout(600)
    check('다른 사람 화면: 걸러진 답·단추 안 보임 · 참여자가 낸 거친 말도 자기 결과에 안 나옴', ks(ap)==['다시발야구','새끼손가락','줄넘기'] and ap.locator('#bfb').count()==0 and jp.locator('#jr .cloud .w').count()==3 and '고마워요' in jp.inner_text('#jc')); an.close()
    fb.close(); d=t.locator('.poll[data-code="%s"] [data-act=del]'%fc); d.click(); d.click(); t.wait_for_timeout(900)
    # ===== 질문 잇기 (묶음) =====
    sibs=lambda c: (lambda v: (list(v.values()) if isinstance(v,dict) else v) or [])(dbget('polls/%s/meta/sib'%c))
    t.reload(); t.wait_for_timeout(800)
    t.fill('#mq','첫째 질문'); t.locator('#mo input').nth(0).fill('가'); t.locator('#mo input').nth(1).fill('나'); t.fill('#ml','https://musicalpe.github.io/apps/'); t.click('#mc'); t.wait_for_timeout(800)
    A=t.locator('.poll').first.get_attribute('data-code')
    t.locator('.poll[data-code="%s"] [data-act=add]'%A).click(); t.wait_for_timeout(200)
    e0='질문 잇기' in t.inner_text('#mh') and t.locator('#mfw').is_visible() and A in t.inner_text('#me') and '이 질문 잇기' in t.inner_text('#mc')
    t.check('#mt1'); t.fill('#mq','둘째 질문'); t.click('#mc'); t.wait_for_timeout(900)
    B=[c for c in sibs(A) if c!=A][0] if len(sibs(A))==2 else ''
    check('질문 잇기: 둘째 질문이 묶음으로 이어짐 (두 설문 모두 순서 목록·넘어가는 방식)', e0 and sibs(A)==[A,B] and sibs(B)==[A,B] and dbget('polls/%s/meta/flow'%A)=='self' and dbget('polls/%s/meta/flow'%B)=='self' and dbget('polls/%s/meta/type'%B)=='text' and '2개가 한 묶음' in t.inner_text('#mm') and '설문 만들기' in t.inner_text('#mh'))
    e1=t.locator('.poll[data-code="%s"] [data-act=add]'%A).count()==0
    t.locator('.poll[data-code="%s"] [data-act=add]'%B).click(); t.wait_for_timeout(200); t.fill('#mq','셋째 질문'); t.locator('#mo input').nth(0).fill('예'); t.locator('#mo input').nth(1).fill('아니오'); t.select_option('#mfl','with'); t.click('#mc'); t.wait_for_timeout(900)
    C=sibs(A)[2] if len(sibs(A))==3 else ''
    order=[e.get_attribute('data-code') for e in t.locator('.poll').all()][:3]
    check('질문 잇기: 셋째까지 · 넘어가는 방식을 바꾸면 묶음 전체에 적용 · 목록에 순서대로', e1 and sibs(A)==[A,B,C]==sibs(B)==sibs(C) and [dbget('polls/%s/meta/flow'%c) for c in (A,B,C)]==['with']*3 and order==[A,B,C] and '묶음 1/3' in t.inner_text('.poll[data-code="%s"]'%A) and '묶음 3/3' in t.inner_text('.poll[data-code="%s"]'%C), str(order))
    # 선생님과 함께 넘어가기
    W=b.new_context(viewport={'width':390,'height':800}); setup(W); wp=W.new_page(); wp.on('pageerror',lambda e: errs.append(str(e))); wp.goto(APP+'?p='+A); wp.wait_for_timeout(500)
    e2='질문 1 / 3' in wp.inner_text('#jc'); wp.locator('.opt').nth(0).click(); wp.click('#js'); wp.wait_for_timeout(500)
    check('함께 넘어가기: 답을 내면 다음 QR을 기다리라는 안내 (다음 단추·끝 주소 없음)', e2 and wp.locator('#jnx').count()==0 and 'QR을 찍어' in wp.inner_text('#jc') and '앱 모음' not in wp.inner_text('#jc')); W.close()
    # 고치기로 스스로 넘어가기로 바꿈
    t.locator('.poll[data-code="%s"] [data-act=edit]'%B).click(); t.wait_for_timeout(200); e3=t.locator('#mfw').is_visible() and t.input_value('#mfl')=='with'
    t.select_option('#mfl','self'); t.click('#mc'); t.wait_for_timeout(900)
    check('고치기: 넘어가는 방식을 바꾸면 묶음 전체에 적용 · 순서 목록 그대로', e3 and [dbget('polls/%s/meta/flow'%c) for c in (A,B,C)]==['self']*3 and sibs(B)==[A,B,C] and dbget('polls/%s/meta/type'%B)=='text')
    S=b.new_context(viewport={'width':390,'height':800}); setup(S); sp=S.new_page(); sp.on('pageerror',lambda e: errs.append(str(e))); sp.goto(APP+'?p='+A); sp.wait_for_timeout(500)
    sp.locator('.opt').nth(1).click(); sp.click('#js'); sp.wait_for_timeout(500); e4='다음 질문 (2 / 3)' in sp.inner_text('#jnx') and '앱 모음' not in sp.inner_text('#jc')
    sp.click('#jnx'); sp.wait_for_timeout(700); e5=('p='+B) in sp.url and '질문 2 / 3' in sp.inner_text('#jc') and sp.locator('.ja').count()==1
    sp.locator('.ja').first.fill('줄넘기'); sp.click('#js'); sp.wait_for_timeout(500); sp.click('#jnx'); sp.wait_for_timeout(700)
    e6=('p='+C) in sp.url and '질문 3 / 3' in sp.inner_text('#jc'); sp.locator('.opt').nth(0).click(); sp.click('#js'); sp.wait_for_timeout(500)
    check('스스로 넘어가기: 다음 질문 단추로 끝까지 · 마지막에만 끝 주소', e4 and e5 and e6 and sp.locator('#jnx').count()==0 and len(dbget('polls/%s/votes'%B))==1 and len(dbget('polls/%s/votes'%C))==1)
    # 결과 화면 쪽 넘기기
    sb=T.new_page(); sb.on('pageerror',lambda e: errs.append(str(e))); sb.goto(APP+'?b='+A); sb.wait_for_timeout(1000)
    e7='1 / 3' in sb.inner_text('#bnv') and sb.is_disabled('#bpv') and '첫째 질문' in sb.inner_text('#bm') and ('p='+A) in sb.inner_text('#bj')
    sb.click('#bnx'); sb.wait_for_timeout(900)
    e8=('b='+B) in sb.url and '둘째 질문' in sb.inner_text('#bm') and sb.locator('#bw .w').count()==1 and ('p='+B) in sb.inner_text('#bj') and '2 / 3' in sb.inner_text('#bnv') and '적어 주세요' in sb.inner_text('#bhow')
    sb.keyboard.press('ArrowRight'); sb.wait_for_timeout(900); e9=('b='+C) in sb.url and '셋째 질문' in sb.inner_text('#bm') and sb.locator('.bar').count()==2 and sb.is_disabled('#bnx') and '골라 주세요' in sb.inner_text('#bhow')
    sb.keyboard.press('PageUp'); sb.wait_for_timeout(900); e10=('b='+B) in sb.url and sb.locator('#bw .w').count()==1
    sb.click('#bsh'); sb.wait_for_timeout(300); sb.keyboard.press('PageUp'); sb.wait_for_timeout(900)
    check('결과 화면 쪽 넘기기: 단추·화살표·쪽 넘김 글쇠 · 쪽마다 그 질문의 QR · 발표 모드에서도', e7 and e8 and e9 and e10 and ('b='+A) in sb.url and 'show=1' in sb.url and sb.locator('#bnv').is_visible() and '1명' in sb.inner_text('#bm'), '%s %s %s %s'%(e7,e8,e9,e10)); sb.close()
    with t.expect_download() as dl: t.locator('.poll[data-code="%s"] [data-act=csv]'%A).click()
    csv=open(dl.value.path(),encoding='utf-8-sig').read()
    check('묶음 답 내려받기: 질문 셋이 한 파일에', '묶음' in dl.value.suggested_filename and csv.count('"질문 ')==3 and '줄넘기' in csv and '둘째 질문' in csv)
    # 선생님과 함께: 뒤 질문은 닫혀 있다가 쪽을 넘기면 열림
    t.reload(); t.wait_for_timeout(900)
    t.locator('.poll[data-code="%s"] [data-act=add]'%C).click(); t.wait_for_timeout(200); t.fill('#mq','넷째 질문'); t.locator('#mo input').nth(0).fill('좋아요'); t.locator('#mo input').nth(1).fill('글쎄요'); t.select_option('#mfl','with'); t.click('#mc'); t.wait_for_timeout(1200)
    D=sibs(A)[3] if len(sibs(A))==4 else ''
    md=lambda c: dbget('polls/%s/meta'%c)
    check('함께 넘어가기로 이으면: 새 질문은 대기(닫힘) · 이미 답이 있는 앞 질문은 열린 채', md(D).get('open') is False and md(D).get('wait') is True and all(md(c).get('open') is True and md(c).get('wait') is None for c in (A,B,C)) and '대기' in t.inner_text('.poll[data-code="%s"]'%D) and [md(c)['flow'] for c in (A,B,C,D)]==['with']*4)
    WW=b.new_context(viewport={'width':390,'height':800}); setup(WW); wq=WW.new_page(); wq.on('pageerror',lambda e: errs.append(str(e))); wq.goto(APP+'?p='+D); wq.wait_for_timeout(600)
    e20='아직 열리지 않은' in wq.inner_text('#jc') and wq.locator('.opt').count()==0 and '질문 4 / 4' in wq.inner_text('#jc')
    r401=0
    try: dbput('polls/%s/votes/%s'%(D,'w%015d'%1),{'c':0,'at':{'.sv':'timestamp'}})
    except Exception as e: r401=getattr(e,'code',0)
    an=b.new_context(viewport={'width':1200,'height':800}); setup(an); ap=an.new_page(); ap.goto(APP+'?b='+C); ap.wait_for_timeout(900); ap.click('#bnx'); ap.wait_for_timeout(900)
    e21=('b='+D) in ap.url and '아직 열기 전' in ap.inner_text('#bm') and md(D).get('open') is False; an.close()
    check('대기 중인 질문: 참여자는 안내만 보고 답을 못 냄 · 다른 사람이 쪽을 넘겨도 안 열림', e20 and r401==401 and e21, '%s %s %s'%(e20,r401,e21))
    ob=T.new_page(); ob.on('pageerror',lambda e: errs.append(str(e))); ob.goto(APP+'?b='+D); ob.wait_for_timeout(1000)
    e22=md(D).get('open') is False and '이 질문 열기' in ob.inner_text('#bop')
    ob.click('#bpv'); ob.wait_for_timeout(900); ob.click('#bnx'); ob.wait_for_timeout(1200)
    e23=md(D).get('open') is True and md(D).get('wait') is None and '아직 열기 전' not in ob.inner_text('#bm') and md(C).get('open') is True
    wq.click('#jrl'); wq.wait_for_timeout(800); e24=wq.locator('.opt').count()==2; wq.locator('.opt').nth(0).click(); wq.click('#js'); wq.wait_for_timeout(600)
    check('만든 사람이 쪽을 넘기면 그 질문이 열림 (바로 열어 볼 때는 안 열림) · 앞 질문은 계속 열림 · 참여자가 이어서 답함', e22 and e23 and e24 and len(dbget('polls/%s/votes'%D))==1 and '1' in ob.inner_text('.b-count'), '%s %s %s'%(e22,e23,e24)); ob.close(); WW.close()
    t.reload(); t.wait_for_timeout(900); d=t.locator('.poll[data-code="%s"] [data-act=del]'%D); d.click(); d.click(); t.wait_for_timeout(1000)
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%B); d.click(); d.click(); t.wait_for_timeout(1000); e11=sibs(A)==[A,C]==sibs(C) and dbget('polls/%s'%B) is None
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%C); d.click(); d.click(); t.wait_for_timeout(1000)
    check('묶음에서 질문을 지우면 남은 순서가 고쳐지고 · 하나만 남으면 묶음이 풀림', e11 and sibs(A)==[] and dbget('polls/%s/meta/flow'%A) is None and '묶음' not in t.inner_text('.poll[data-code="%s"]'%A) and t.locator('.poll[data-code="%s"] [data-act=add]'%A).count()==1)
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%A); d.click(); d.click(); t.wait_for_timeout(900)
    # ===== 확인한 뒤 띄우기 =====
    t.check('#mt1'); t.fill('#mq','하고 싶은 말'); t.check('#mmod'); t.click('#mc'); t.wait_for_timeout(800)
    M=t.locator('.poll').first.get_attribute('data-code')
    for i,a in enumerate([['재밌어요'],['또 해요'],['힘들어요'],['재밌어요']]): dbput('polls/%s/votes/%s'%(M,'m%015d'%i),{'a':a,'at':{'.sv':'timestamp'}})
    mb=T.new_page(); mb.on('pageerror',lambda e: errs.append(str(e))); mb.goto(APP+'?b='+M); mb.wait_for_timeout(1000)
    check('확인한 뒤 띄우기: 처음엔 아무 답도 안 뜨고 · 만든 사람에게 확인할 답 목록', dbget('polls/%s/meta/mod'%M) is True and mb.locator('#bw .w').count()==0 and '확인할 답 3개' in mb.inner_text('#bfb') and '재밌어요 · 2명' in mb.inner_text('#bfl') and '4' in mb.inner_text('.b-count'))
    mb.locator('#bfl button[data-k="재밌어요"][data-a=show]').click(); mb.wait_for_timeout(600); e12=ks(mb)==['재밌어요'] and '2개' in mb.inner_text('#bfb')
    mb.locator('#bfl button[data-k="힘들어요"][data-a=drop]').click(); mb.wait_for_timeout(600); e13=ks(mb)==['재밌어요'] and '1개' in mb.inner_text('#bfb') and sorted(hl(M))==['+재밌어요','힘들어요']
    an=b.new_context(viewport={'width':1200,'height':800}); setup(an); ap=an.new_page(); ap.goto(APP+'?b='+M); ap.wait_for_timeout(900); e14=ks(ap)==['재밌어요'] and ap.locator('#bfb').count()==0 and ap.locator('#bfl .row').count()==0; an.close()
    dbput('polls/%s/votes/%s'%(M,'m%015d'%9),{'a':['최고'],'at':{'.sv':'timestamp'}}); mb.wait_for_timeout(900); e15=ks(mb)==['재밌어요'] and '2개' in mb.inner_text('#bfb')
    mb.click('#ball'); mb.wait_for_timeout(600)
    check('확인한 뒤 띄우기: 띄우기·버리기·모두 띄우기 · 다른 사람에게는 띄운 답만', e12 and e13 and e14 and e15 and ks(mb)==['또해요','재밌어요','최고'] and mb.locator('#bfb').count()==0, '%s %s %s %s %s'%(e12,e13,e14,e15,ks(mb)))
    mb.click('#bsh'); mb.wait_for_timeout(300); e16=not mb.locator('#bfl').is_visible(); mb.close()
    t.reload(); t.wait_for_timeout(800); t.locator('.poll[data-code="%s"] [data-act=edit]'%M).click(); t.wait_for_timeout(200); e17=t.is_checked('#mmod'); t.uncheck('#mmod'); t.click('#mc'); t.wait_for_timeout(800)
    check('확인한 뒤 띄우기: 발표 모드에서는 목록이 안 보임 · 고치기로 끌 수 있음', e16 and e17 and dbget('polls/%s/meta/mod'%M) is None and len(hl(M))>=3)
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%M); d.click(); d.click(); t.wait_for_timeout(900)
    # ===== 사용 안내 · 설문 수 상한 =====
    t.locator('details.guide summary').click(); check('첫 화면 사용 안내', '30개까지' in t.inner_text('details.guide') and '구글 로그인' in t.inner_text('details.guide'))
    for i in range(30):
        c='zz%04d'%i; dbput('polls/%s/meta'%c,{'owner':'teacher1','q':'상한 시험 %d'%i,'opts':['가','나'],'open':True,'ask':False,'res':True,'at':1000+i},'teacher1'); dbput('users/teacher1/polls/%s'%c,1000+i,'teacher1')
    t.reload(); t.wait_for_timeout(1500); n0=len(dbget('users/teacher1/polls?auth=teacher1'.replace('?auth=teacher1','')) or {}) if False else t.locator('.poll').count()
    t.fill('#mq','서른한 번째'); t.locator('#mo input').nth(0).fill('가'); t.locator('#mo input').nth(1).fill('나'); t.click('#mc'); t.wait_for_timeout(600)
    check('설문 수 상한: 30개가 넘으면 더 못 만들고 안내', '30개까지' in t.inner_text('#mm') and t.locator('.poll').count()==n0 and n0>=30)
    t.click('#lo'); t.wait_for_timeout(300); check('로그아웃 → 로그인 단추', t.locator('#lg').count()==1)
    # 연결 정보가 없을 때
    N=b.new_context(); N.route(re.compile(r'.*/config\.js(\?.*)?$'), lambda r: r.fulfill(body='window.HEARIM_CONFIG=null;',content_type='application/javascript')); n1=N.new_page(); n1.goto(APP); n1.wait_for_timeout(300); check('연결 정보 없으면 안내만', '아직 연결 전' in n1.inner_text('#app'))
    check('화면 오류 없음', not errs, str(errs[:3]))
finally:
    web.terminate(); db.terminate()
print('결과:', '모두 통과' if ok else '실패 있음')
