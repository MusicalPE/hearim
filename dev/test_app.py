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
    # 그래프 모양
    e0='가로 막대' in bd.inner_text('#bgr') and bd.locator('.bar').count()==4
    bd.click('#bgr'); bd.wait_for_timeout(250)
    hs=bd.evaluate("()=>[...document.querySelectorAll('.cols .stick')].map(e=>e.getBoundingClientRect().height)")
    e1='세로 막대' in bd.inner_text('#bgr') and bd.locator('.cols .col').count()==4 and bd.locator('.cols .col.lead').count()==1 and bd.locator('.col-labs span').count()==4 and hs.count(max(hs))==1 and '3명' in bd.inner_text('.cols .col.lead') and 'g=col' in bd.url
    if SHOTS: bd.set_viewport_size({'width':1600,'height':900}); bd.wait_for_timeout(700); bd.screenshot(path=SHOTS+'/ha_col.png')
    bd.click('#bgr'); bd.wait_for_timeout(250)
    nz=sum(1 for x in bd.evaluate("()=>[...document.querySelectorAll('.pie-leg div span:last-child')].map(e=>e.textContent)") if not x.startswith('0명'))
    e2='원 그래프' in bd.inner_text('#bgr') and bd.locator('svg.pie path').count()==nz and bd.locator('.pie-leg div').count()==4 and '3명 · 50%' in bd.inner_text('.pie-leg') and 'g=pie' in bd.url and bd.locator('#bj svg').is_visible()
    if SHOTS: bd.wait_for_timeout(300); bd.screenshot(path=SHOTS+'/ha_pie.png'); bd.set_viewport_size({'width':1100,'height':900})
    check('그래프 모양: 가로 막대 → 세로 막대 → 원 그래프 (주소에 g= 로 적힘)', e0 and e1 and e2, '%s %s %s %s'%(e0,e1,e2,hs))
    gp=bd.context.new_page(); gp.goto(APP+'?b='+code+'&g=col&show=1'); gp.wait_for_timeout(900); e3=gp.locator('.cols .col').count()==4 and not gp.locator('.b-top').is_visible()
    gp.keyboard.press('g'); gp.wait_for_timeout(250); e4=gp.locator('svg.pie').count()==1; gp.close()
    bd.click('#bgr'); bd.wait_for_timeout(250)
    check('그래프 모양: 주소로 바로 열기 · 발표 모드에서는 g 글쇠로 바꿈 · 다시 가로 막대', e3 and e4 and bd.locator('.bar').count()==4 and 'g=' not in bd.url and bd.locator('.cols').count()==0)
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
    check('고치기: 칸에 내용이 채워지고 · 답이 있어 보기 빼기는 잠김', t.input_value('#mq')=='어떻게 보여 주면 모두가 꾸준히 뛸까요?' and t.locator('#mo input').count()==4 and t.locator('#mo button:disabled').count()==4 and '6명' in t.inner_text('#qs') and t.input_value('#ml')=='https://musicalpe.github.io/apps/' and '고친 내용 저장' in t.inner_text('#mc'))
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
    # ===== 퀴즈: 함께 풀기 (정답 넣기 · 정답 보이기) =====
    def getc(p,auth=''):
        try: return json.loads(urllib.request.urlopen(DBU+'/'+p+'.json'+('?auth='+auth if auth else '')).read())
        except Exception as e: return getattr(e,'code',0)
    t.reload(); t.wait_for_timeout(800)
    k0=t.locator('#mtw').is_visible() and not t.locator('#manw').is_visible() and not t.locator('#mox').is_visible() and not t.locator('#mqzw').is_visible() and t.locator('#maskw').is_visible() and '설문 만들기' in t.inner_text('#mc')
    t.click('#tb1'); t.wait_for_timeout(100)
    k1=(not t.locator('#mtw').is_visible()) and t.locator('#manw').is_visible() and t.locator('#mox').is_visible() and t.locator('#mqzw').is_visible() and not t.locator('#maskw').is_visible() and '퀴즈 만들기' in t.inner_text('#mc') and '퀴즈 만들기' in t.inner_text('#mh')
    t.fill('#mq','줄넘기는 유산소 운동이다'); t.click('#mox'); t.wait_for_timeout(100); t.click('#mc'); t.wait_for_timeout(300); k2='정답을 골라 주세요' in t.inner_text('#mm')
    t.click('#tb0'); k3=t.locator('#mtw').is_visible() and not t.locator('#manw').is_visible(); t.click('#tb1'); t.wait_for_timeout(100)
    check('만들기 갈래: 설문 만들기(기본)에는 정답·푸는 방식 없음 · 퀴즈 만들기에는 정답이 꼭 있어야 함', k0 and k1 and k2 and k3, '%s %s %s %s'%(k0,k1,k2,k3))
    e0=[i.input_value() for i in t.locator('#mo input').all()]==['O','X'] and t.locator('#mans option').count()==3
    t.select_option('#mans','0'); t.click('#mc'); t.wait_for_timeout(900)
    Z=t.locator('.poll').first.get_attribute('data-code'); zm=dbget('polls/%s/meta'%Z)
    check('퀴즈 만들기: OX로 채우기 · 정답은 만든 사람만 읽는 칸에 (설문 내용에는 없음 · 다른 사람은 못 읽음)', e0 and getc('keys/'+Z,'teacher1')=={'a':0} and getc('keys/'+Z)==401 and getc('keys/'+Z,'teacher2')==401 and 'rev' not in zm and 'a' not in zm and (list(zm['opts'].values()) if isinstance(zm['opts'],dict) else zm['opts'])==['O','X'])
    zb=T.new_page(); zb.on('pageerror',lambda e: errs.append(str(e))); zb.goto(APP+'?b='+Z); zb.wait_for_timeout(1100)
    za=b.new_context(viewport={'width':1200,'height':800}); setup(za); zv=za.new_page(); zv.goto(APP+'?b='+Z); zv.wait_for_timeout(900)
    P1=b.new_context(viewport={'width':390,'height':800}); setup(P1); p1=P1.new_page(); p1.on('pageerror',lambda e: errs.append(str(e))); p1.goto(APP+'?p='+Z); p1.wait_for_timeout(500); p1.locator('.opt').nth(0).click(); p1.click('#js'); p1.wait_for_timeout(500)
    P2=b.new_context(viewport={'width':390,'height':800}); setup(P2); p2=P2.new_page(); p2.on('pageerror',lambda e: errs.append(str(e))); p2.goto(APP+'?p='+Z); p2.wait_for_timeout(500); p2.locator('.opt').nth(1).click(); p2.click('#js'); p2.wait_for_timeout(500)
    dbput('polls/%s/votes/%s'%(Z,'z%015d'%1),{'c':0,'at':{'.sv':'timestamp'}}); zb.wait_for_timeout(800)
    check('정답 보이기 전: 만든 사람에게만 단추 · 어디에도 정답 표시 없음 · 참여자는 답 바꾸기 가능', '정답 보이기' in zb.inner_text('#bans') and zv.locator('#bans').count()==0 and zb.locator('.okt').count()==0 and zv.locator('.okt').count()==0 and '정답' not in p1.inner_text('#jc') and p1.locator('#jch').count()==1 and '3' in zb.inner_text('.b-count'))
    zb.click('#bans'); zb.wait_for_timeout(800)
    check('정답 보이기: 정답 막대에 표시와 정답률 · 다른 사람 화면에도 보임', dbget('polls/%s/meta/rev'%Z)==0 and zb.locator('.bar.ok').count()==1 and '정답' in zb.inner_text('.bar.ok') and '정답률 67%' in zb.inner_text('.b-count') and '정답 숨기기' in zb.inner_text('#bans') and zv.locator('.bar.ok').count()==1)
    zb.click('#bgr'); zb.wait_for_timeout(250); e1=zb.locator('.cols .col.ok').count()==1 and zb.locator('.col-labs .okt').count()==1
    zb.click('#bgr'); zb.wait_for_timeout(250); e2=zb.locator('.pie-leg .okt').count()==1; zb.click('#bgr'); zb.wait_for_timeout(250)
    p1.click('#jre'); p1.wait_for_timeout(700); p2.click('#jre'); p2.wait_for_timeout(700)
    check('정답 보이기: 세로 막대·원 그래프에도 표시 · 참여자는 결과 새로 보기로 맞았는지 확인 · 답 바꾸기는 사라짐', e1 and e2 and '맞았어요' in p1.inner_text('#jc') and '아쉬워요' in p2.inner_text('#jc') and '정답은 O' in p2.inner_text('#jc').replace('\n',' ') and p1.locator('#jch').count()==0 and p2.locator('#jr .bar.ok').count()==1)
    P3=b.new_context(viewport={'width':390,'height':800}); setup(P3); p3=P3.new_page(); p3.goto(APP+'?p='+Z); p3.wait_for_timeout(600); r401=0
    try: dbput('polls/%s/votes/%s'%(Z,'z%015d'%2),{'c':0,'at':{'.sv':'timestamp'}})
    except Exception as e: r401=getattr(e,'code',0)
    check('정답이 보인 뒤에는 새로 답할 수 없음 (안내와 정답만)', '정답이 공개되어' in p3.inner_text('#jc') and p3.locator('.opt').count()==0 and r401==401 and len(dbget('polls/%s/votes'%Z))==3); P3.close()
    zb.keyboard.press('a'); zb.wait_for_timeout(800); e3=dbget('polls/%s/meta/rev'%Z) is None and zb.locator('.okt').count()==0 and zv.locator('.okt').count()==0
    zv.keyboard.press('a'); zv.wait_for_timeout(500)
    check('정답 숨기기 (a 글쇠) · 다른 사람은 정답을 보이게 할 수 없음', e3 and dbget('polls/%s/meta/rev'%Z) is None); za.close(); P1.close(); P2.close(); zb.close()
    t.reload(); t.wait_for_timeout(900); t.locator('.poll[data-code="%s"] [data-act=edit]'%Z).click(); t.wait_for_timeout(500)
    e4=t.input_value('#mans')=='0'; t.select_option('#mans','1'); t.click('#mc'); t.wait_for_timeout(900); e5=getc('keys/'+Z,'teacher1')=={'a':1}
    t.locator('.poll[data-code="%s"] [data-act=edit]'%Z).click(); t.wait_for_timeout(500); t.click('#tb0'); t.click('#mc'); t.wait_for_timeout(900)
    check('퀴즈 고치기: 정답이 채워져 있고 · 바꾸기 · 설문 갈래로 바꿔 저장하면 정답이 지워짐', e4 and e5 and getc('keys/'+Z,'teacher1') is None and len(dbget('polls/%s/votes'%Z))==3)
    t.locator('.poll[data-code="%s"] [data-act=edit]'%Z).click(); t.wait_for_timeout(500); t.click('#tb1'); t.select_option('#mans','0'); t.click('#mc'); t.wait_for_timeout(900)
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%Z); d.click(); d.click(); t.wait_for_timeout(1000)
    check('퀴즈 지우기: 정답도 함께 지워짐', dbget('polls/%s'%Z) is None and getc('keys/'+Z,'__admin') is None)
    # ===== 퀴즈: 혼자 풀기 (번호 입장 · 맞은 개수 · 분포) =====
    sibs=lambda c: (lambda v: (list(v.values()) if isinstance(v,dict) else v) or [])(dbget('polls/%s/meta/sib'%c))
    t.reload(); t.wait_for_timeout(800); t.click('#tb1')
    t.fill('#mq','줄넘기는 유산소 운동이다'); t.click('#mox'); t.select_option('#mans','0'); t.select_option('#mqz','solo'); t.wait_for_timeout(100)
    e0=t.locator('#mqs').is_visible(); t.fill('#msn','5'); t.click('#mc'); t.wait_for_timeout(900)
    Q1=t.locator('.poll').first.get_attribute('data-code'); q1=dbget('polls/%s/meta'%Q1)
    qn=lambda i: t.locator('#qs .qb').nth(i)
    t.locator('.poll[data-code="%s"] [data-act=edit]'%Q1).click(); t.wait_for_timeout(700); t.click('#qadd'); t.wait_for_timeout(100)
    e1=t.input_value('#mqz')=='solo' and t.input_value('#msn')=='5' and t.input_value('#mans')=='0' and '퀴즈 고치기' in t.inner_text('#mh') and not t.locator('#mfw').is_visible()
    qn(1).locator('.q-q').fill('줄을 돌리는 힘은 주로 어디에서?')
    for i,o in enumerate(['어깨','허리','손목']):
        if i>=2: qn(1).locator('.q-add').click()
        qn(1).locator('.q-o input').nth(i).fill(o)
    t.click('#mc'); t.wait_for_timeout(300); e1=e1 and '질문 2: 정답을 골라 주세요' in t.inner_text('#mm')
    qn(1).locator('.q-ans').select_option('2'); t.click('#mc'); t.wait_for_timeout(1500)
    Q2=sibs(Q1)[1] if len(sibs(Q1))==2 else ''; q2=dbget('polls/%s/meta'%Q2) if Q2 else {}
    check('혼자 풀기 만들기: 학생 수 · 결과 보여 주기는 꺼짐 · 이은 질문도 같은 방식(스스로 넘어가기)', e0 and e1 and q1.get('qz')=='solo' and q1.get('seats')==5 and q1.get('res') is False and q2.get('qz')=='solo' and q2.get('seats')==5 and q2.get('flow')=='self' and getc('keys/'+Q2,'teacher1')=={'a':2})
    def student(num, a1, a2):
        C=b.new_context(viewport={'width':390,'height':800}); setup(C); pg=C.new_page(); pg.on('pageerror',lambda e: errs.append(str(e))); pg.goto(APP+'?p='+Q1); pg.wait_for_timeout(700)
        info={'seats':pg.locator('.seat').count(),'dis':pg.locator('.seat:disabled').count()}
        pg.locator('.seat[data-n="%d"]'%num).click(); pg.click('#jsn'); pg.wait_for_timeout(800)
        info['form']=pg.inner_text('#jc')
        pg.locator('.opt').nth(a1).click(); pg.click('#js'); pg.wait_for_timeout(600); info['done1']=pg.inner_text('#jc'); info['jr']=pg.locator('#jr').count()
        if a2 is not None:
            pg.click('#jnx'); pg.wait_for_timeout(800); pg.locator('.opt').nth(a2).click(); pg.click('#js'); pg.wait_for_timeout(700); info['done2']=pg.inner_text('#jc')
        return pg, info
    s1,i1=student(3,0,2); s2,i2=student(1,1,2); s3,i3=student(5,0,None)
    r401=0
    try: dbput('seats/%s/3'%Q1,'abc123')
    except Exception as e: r401=getattr(e,'code',0)
    seats=dbget('seats/%s'%Q1); skeys=getc('skeys/'+Q1,'teacher1')
    check('번호 고르기: 번호 5개 · 먼저 고른 번호는 다른 친구가 못 고름 · 화면에 내 번호', i1['seats']==5 and i1['dis']==0 and i2['dis']==1 and i3['dis']==2 and '3번으로 들어왔어요' in i1['form'] and '3번으로 들어왔어요' in i1['done1'] and '질문 1 / 2' in i1['form'] and r401==401 and sorted(seats.keys() if isinstance(seats,dict) else [])==['1','3','5'], '%s %s'%(i2,seats))
    check('번호 열쇠는 만든 사람만 읽음 · 풀 때는 결과가 안 보이고 다음 질문으로 · 다 풀면 기다리라는 안내', getc('skeys/'+Q1)==401 and getc('skeys/'+Q1,'teacher2')==401 and len(skeys)==3 and i1['jr']==0 and '다음 질문' in i1['done1'] and '다 풀었어요' in i1['done2'] and '맞았어요' not in i1['done2'] and len(dbget('polls/%s/votes'%Q1))==3 and len(dbget('polls/%s/votes'%Q2))==2)
    qb=T.new_page(); qb.on('pageerror',lambda e: errs.append(str(e))); qb.goto(APP+'?b='+Q1); qb.wait_for_timeout(1200)
    qa=b.new_context(viewport={'width':1200,'height':800}); setup(qa); qv=qa.new_page(); qv.goto(APP+'?b='+Q1); qv.wait_for_timeout(900)
    e2=qb.locator('.bar').count()==0 and '푸는 중' in qb.inner_text('#bm') and '들어온 번호 3명 / 5명' in qb.inner_text('.b-seats').replace('\n',' ') and [x.inner_text() for x in qb.locator('.b-seats span').all()]==['1','3','5'] and qv.locator('.b-seats span').count()==3 and qb.locator('#bsc').count()==1 and qb.locator('#btb').count()==1 and qv.locator('#bsc').count()==0 and qv.locator('#btb').count()==0 and qv.locator('#bds').count()==0
    qb.click('#bsc'); qb.wait_for_timeout(1500)
    pid=lambda nn: skeys[str(nn)] if isinstance(skeys,dict) else skeys[nn]
    sc=[dbget('scores/%s/%s'%(Q1,pid(nn))) for nn in (3,1,5)]; dist=dbget('scores/%s/dist'%Q1)
    dd=list(dist['d'].values()) if isinstance(dist['d'],dict) else dist['d']
    check('결과 알려 주기: 번호마다 맞은 개수(3번 2개 · 1번 1개 · 5번 1개) · 분포 저장 · 점수는 통째로 못 읽음', e2 and sc==[{'c':2,'n':2},{'c':1,'n':2},{'c':1,'n':2}] and dd==[0,2,1] and dist['k']==3 and getc('scores/'+Q1)==401, '%s %s'%(sc,dd))
    qv.wait_for_timeout(900); e3=qv.locator('#bds').count()==1; qv.click('#bds'); qv.wait_for_timeout(300)
    check('분포 화면: 맞은 개수별 사람 수와 문제별 정답률만 (번호 없음) · 다른 사람도 볼 수 있음', '퀴즈 결과' in qb.inner_text('#bm') and qb.locator('.cols .col').count()==3 and '2명' in qb.inner_text('.cols') and '정답률 67%' in qb.inner_text('.b-rates') and '정답률 100%' in qb.inner_text('.b-rates') and '번' not in qb.inner_text('.cols') and e3 and qv.locator('.cols .col').count()==3 and qv.locator('table.qt').count()==0)
    s1.click('#jsc'); s1.wait_for_timeout(700); s2.click('#jsc'); s2.wait_for_timeout(700)
    check('참여자: 내 결과 보기로 맞은 개수만 확인', '2문제 중 2개' in s1.inner_text('#jq') and '2문제 중 1개' in s2.inner_text('#jq'))
    v2=dbget('polls/%s/votes/%s'%(Q1,pid(1)))['c']
    e7=s1.locator('#jrt').count()==0 and s2.locator('#jrt').count()==1 and s2.locator('#jch').count()==0
    s2.click('#jrt'); s2.wait_for_timeout(900); e8='다시 풀기 1 / 1' in s2.inner_text('#jc') and '줄넘기는 유산소 운동이다' in s2.inner_text('#jc')
    s2.locator('.opt').nth(1).click(); s2.wait_for_timeout(200); e9='다시 골라' in s2.inner_text('#jm') and s2.locator('.opt').nth(1).is_disabled()
    s2.locator('.opt').nth(0).click(); s2.wait_for_timeout(1400); e10='다 풀었어요' in s2.inner_text('#jc')
    s2.click('#jbk'); s2.wait_for_timeout(700)
    s3.goto(APP+'?p='+Q1); s3.wait_for_timeout(1000); s3.click('#jrt'); s3.wait_for_timeout(900); e11='질문 2' in s3.inner_text('#jc') and s3.locator('.opt').count()==3
    check('틀린 문제 다시 풀기: 틀린 사람에게만 · 맞을 때까지 골라 봄 · 안 푼 문제도 나옴 · 처음 낸 답과 점수는 그대로', e7 and e8 and e9 and e10 and e11 and v2==1 and dbget('polls/%s/votes/%s'%(Q1,pid(1)))['c']==1 and dbget('scores/%s/%s'%(Q1,pid(1)))=={'c':1,'n':2} and '2문제 중 1개' in s2.inner_text('#jq'), '%s %s %s %s %s'%(e7,e8,e9,e10,e11))
    qb.click('#bqv'); qb.wait_for_timeout(300); qb.click('#btb'); qb.wait_for_timeout(1200)
    tb=qb.inner_text('table.qt') if qb.locator('table.qt').count() else ''
    e4='3번' in tb and '선생님만' in qb.inner_text('#bm') and qb.locator('table.qt tr').count()==4
    # 번호 하나만 풀기 (5번)
    p5=pid(5); rb=qb.locator('[data-rel="5"]'); rb.click(); rb.click(); qb.wait_for_timeout(1500)
    st=dbget('seats/%s'%Q1); e12=sorted(st.keys())==['1','3'] and len(getc('skeys/'+Q1,'teacher1'))==2 and dbget('polls/%s/votes/%s'%(Q1,p5)) is None and dbget('scores/%s/%s'%(Q1,p5)) is None and len(dbget('polls/%s/votes'%Q1))==2 and qb.locator('table.qt tr').count()==3 and dbget('scores/%s/%s'%(Q1,pid(3)))=={'c':2,'n':2}
    N5=b.new_context(viewport={'width':390,'height':800}); setup(N5); n5=N5.new_page(); n5.goto(APP+'?p='+Q1); n5.wait_for_timeout(700); e13=n5.locator('.seat:disabled').count()==2; n5.locator('.seat[data-n="5"]').click(); n5.click('#jsn'); n5.wait_for_timeout(800)
    s3.goto(APP+'?p='+Q1); s3.wait_for_timeout(900); e14=s3.locator('.seat').count()==5 and s3.locator('.seat:disabled').count()==3
    s1.goto(APP+'?p='+Q1); s1.wait_for_timeout(900); e15=s1.locator('.seat').count()==0 and '3번으로 들어왔어요' in s1.inner_text('#jc')
    check('번호 하나만 풀기: 그 번호의 번호표·답·점수만 지워짐 · 다른 아이는 그대로 · 풀린 번호는 다시 고를 수 있고, 예전 기기는 번호를 다시 고르게 됨', e12 and e13 and e14 and e15, '%s %s %s %s'%(e12,e13,e14,e15)); N5.close()
    qb.click('#bsh'); qb.wait_for_timeout(400); e5=qb.locator('table.qt').count()==0; qb.click('#bx'); qb.wait_for_timeout(300)
    check('번호별 결과: 만든 사람만 · 발표 모드로 가면 표가 사라짐', e4 and e5)
    s1.goto(APP+'?p='+Q1); s1.wait_for_timeout(800); e6=s1.locator('.seat').count()==0 and '고마워요' in s1.inner_text('#jc') and '3번' not in '' 
    armed_rs=qb.locator('#brs'); armed_rs.click(); armed_rs.click(); qb.wait_for_timeout(1500)
    s1.goto(APP+'?p='+Q1); s1.wait_for_timeout(800)
    check('같은 기기로 다시 오면 번호를 다시 고르지 않음 · 퀴즈 처음부터: 번호·답·결과가 모두 지워지고 다시 번호 고르기', e6 and dbget('seats/%s'%Q1) is None and getc('skeys/'+Q1,'__admin') is None and getc('scores/'+Q1,'__admin') is None and dbget('polls/%s/votes'%Q1) is None and dbget('polls/%s/votes'%Q2) is None and s1.locator('.seat').count()==5 and s1.locator('.seat:disabled').count()==0)
    for x in (s1,s2,s3): x.context.close()
    qa.close(); qb.close()
    t.reload(); t.wait_for_timeout(900)
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%Q1); d.click(); d.click(); t.wait_for_timeout(1500)
    check('묶음 지우기: 질문 전체와 정답이 함께 지워짐', dbget('polls/%s'%Q1) is None and dbget('polls/%s'%Q2) is None and getc('keys/'+Q2,'__admin') is None and t.locator('.poll[data-code="%s"]'%Q1).count()==0)
    # ===== 골든벨 (번호 입장 · 틀리면 탈락 · 부활 문제) =====
    t.reload(); t.wait_for_timeout(800); t.click('#tb1'); qn=lambda i: t.locator('#qs .qb').nth(i)
    t.select_option('#mqz','bell'); t.wait_for_timeout(100); g0=t.locator('#mbw').is_visible() and t.locator('#mqs').is_visible() and not t.locator('#mres').is_visible()
    t.fill('#msn','4'); t.fill('#mq','골든벨 하나'); t.click('#mox'); t.select_option('#mans','0')
    t.click('#qadd'); qn(1).locator('.q-q').fill('골든벨 둘'); qn(1).locator('.q-add').click()
    for i,o in enumerate(['가','나','다']): qn(1).locator('.q-o input').nth(i).fill(o)
    qn(1).locator('.q-ans').select_option('1')
    t.click('#qadd'); qn(2).locator('.q-q').fill('골든벨 부활'); qn(2).locator('.q-ox').click(); qn(2).locator('.q-ans').select_option('1'); qn(2).locator('.q-rv').check()
    g1=not qn(0).locator('.q-rvw').is_visible() and qn(1).locator('.q-rvw').is_visible() and not t.locator('#mfw').is_visible()
    t.click('#mc'); t.wait_for_timeout(1800)
    G1=t.locator('.poll').first.get_attribute('data-code'); gs=sibs(G1); gm=[dbget('polls/%s/meta'%c) for c in gs]; G2,G3=(gs+['',''])[1:3]
    check('골든벨 만들기: 푸는 방식 골든벨 · 부활 문제는 둘째부터 · 선생님과 함께로 저장(뒤 문제는 대기)', g0 and g1 and len(gs)==3 and all(m.get('qz')=='bell' and m.get('flow')=='with' and m.get('nshow') is True and m.get('seats')==4 for m in gm) and [m.get('rv') for m in gm]==[None,None,True] and [m.get('wait') for m in gm]==[None,True,True] and '골든벨' in t.inner_text('.poll[data-code="%s"]'%G1) and '부활 문제' in t.inner_text('.poll[data-code="%s"] .qlist'%G1), str([(m.get('qz'),m.get('rv'),m.get('wait')) for m in gm]))
    gb=T.new_page(); gb.on('pageerror',lambda e: errs.append(str(e))); gb.goto(APP+'?b='+G1); gb.wait_for_timeout(1200)
    def bst(num):
        C=b.new_context(viewport={'width':390,'height':800}); setup(C); pg=C.new_page(); pg.on('pageerror',lambda e: errs.append(str(e))); pg.goto(APP+'?p='+G1); pg.wait_for_timeout(700)
        pg.locator('.seat[data-n="%d"]'%num).click(); pg.click('#jsn'); pg.wait_for_timeout(900); return pg
    def ans(pg,i): pg.locator('.opt').nth(i).click(); pg.click('#js'); pg.wait_for_timeout(700)
    jc=lambda pg: pg.inner_text('#jc')
    b1,b2,b3=bst(1),bst(2),bst(3); g2='1번으로 들어왔어요' in jc(b1) and '질문 1 / 3' in jc(b1)
    ans(b1,0); ans(b2,1); g3='기다려요' in jc(b1) and b1.locator('#jch').count()==1
    gb.wait_for_timeout(500); g4=gb.locator('.bar').count()==0 and '답하는 중' in gb.inner_text('#bm') and '2' in gb.inner_text('.b-count') and gb.locator('.b-alive').count()==0 and gb.locator('#btb').count()==1 and gb.locator('#bsc').count()==0
    gb.click('#bans'); gb.wait_for_timeout(4500)
    bsum=dbget('scores/%s/bell'%G1); gk=getc('skeys/'+G1,'teacher1'); gp=lambda nn: gk[str(nn)] if isinstance(gk,dict) else gk[nn]
    check('골든벨 1번 문제: 답하는 동안 그래프 숨김 · 정답을 보이면 맞은 친구만 살아남음(안 낸 친구도 탈락) · 아이 화면이 스스로 바뀜', g2 and g3 and g4 and '살아남았어요' in jc(b1) and '맞았어요' in jc(b1) and '탈락했어요' in jc(b2) and '탈락했어요' in jc(b3) and bsum['a']==1 and bsum['k']==3 and dbget('scores/%s/%s'%(G1,gp(2)))=={'o':1,'i':0} and dbget('scores/%s/%s'%(G1,gp(1)))=={'o':0,'i':0}, '%s | %s | %s'%(jc(b1)[-60:],jc(b3)[-60:],bsum))
    al=gb.inner_text('.b-alive').replace('\n',' ')
    check('골든벨 큰 화면: 남은 사람 수 · 살아남은 번호 표시(탈락 번호는 흐리게) · 정답 뒤 그래프', '남은 사람 1' in al and '/ 3명' in al and gb.locator('.b-seats span').count()==3 and gb.locator('.b-seats span.gone').count()==2 and gb.locator('.b-seats span:not(.gone)').inner_text()=='1' and gb.locator('.bar').count()==2, al)
    gb.click('#bnx'); gb.wait_for_timeout(5000)
    g5=('p='+G2) in b1.url and ('p='+G2) in b2.url and b1.locator('.opt').count()==3 and b2.locator('.opt').count()==0 and '이번 문제는 지켜봐요' in jc(b2) and dbget('polls/%s/meta/open'%G2) is True
    ans(b1,1); gb.click('#bans'); gb.wait_for_timeout(4500); g6='살아남았어요' in jc(b1) and dbget('scores/%s/bell'%G1)['a']==1
    check('골든벨 2번 문제: 쪽을 넘기면 아이 화면도 다음 문제로 · 탈락한 친구는 못 풀고 지켜봄', g5 and g6, '%s %s | %s'%(g5,g6,jc(b2)[-80:]))
    gb.click('#bnx'); gb.wait_for_timeout(5000)
    g7='부활 문제' in gb.inner_text('.b-q') and '살아남은 친구는 잠깐 쉬어요' in jc(b1) and b1.locator('.opt').count()==0 and b2.locator('.opt').count()==2 and '부활 문제' in jc(b2)
    ans(b2,1); ans(b3,0); gb.click('#bans'); gb.wait_for_timeout(4500); bsum=dbget('scores/%s/bell'%G1); ns=list(bsum['ns'].values()) if isinstance(bsum.get('ns'),dict) else bsum.get('ns')
    check('골든벨 부활 문제: 탈락한 친구만 풀고 · 맞히면 다시 살아남 · 틀리면 그대로 · 끝 안내', g7 and '다시 살아났어요' in jc(b2) and '아직 탈락' in jc(b3) and '살아남았어요' in jc(b1) and '끝까지 살아남았어요' in jc(b2) and '골든벨이 끝났어요' in jc(b3) and bsum['a']==2 and ns==[1,2] and '남은 사람 2' in gb.inner_text('.b-alive').replace('\n',' ') and gb.locator('.b-seats span.gone').count()==1, '%s | %s | %s'%(g7,jc(b2)[-70:],bsum))
    # 처음부터 · 남은 수만 보여 주기
    r=gb.locator('#brs'); r.click(); r.click(); gb.wait_for_timeout(1800)
    g8=dbget('seats/'+G1) is None and dbget('scores/%s/bell'%G1) is None and [dbget('polls/%s/meta/wait'%c) for c in gs]==[None,True,True] and [dbget('polls/%s/meta/open'%c) for c in gs]==[True,False,False] and all(dbget('polls/%s/meta/rev'%c) is None for c in gs) and ('b='+G1) in gb.url and gb.locator('.b-alive').count()==0
    b1.wait_for_timeout(4500); g9=('p='+G1) in b1.url and b1.locator('.seat').count()==4
    t.reload(); t.wait_for_timeout(900); t.locator('.poll[data-code="%s"] [data-act=edit]'%G1).click(); t.wait_for_timeout(800)
    g10=t.input_value('#mqz')=='bell' and t.input_value('#mns')=='1' and qn(2).locator('.q-rv').is_checked() and not qn(1).locator('.q-rv').is_checked() and qn(2).locator('.q-ans').input_value()=='1'
    t.select_option('#mns','0'); t.click('#mc'); t.wait_for_timeout(1500); g11=all(dbget('polls/%s/meta/nshow'%c) is None for c in gs) and [dbget('polls/%s/meta/wait'%c) for c in gs]==[None,True,True] and dbget('polls/%s/meta/rv'%G3) is True
    b1.locator('.seat[data-n="4"]').click(); b1.click('#jsn'); b1.wait_for_timeout(900); ans(b1,1); gb.wait_for_timeout(600); gb.click('#bans'); gb.wait_for_timeout(4500); bsum=dbget('scores/%s/bell'%G1)
    check('골든벨: 퀴즈 처음부터(번호·결과 지우고 뒤 문제 다시 대기, 아이는 번호부터) · 고치기에 그대로 채워짐 · 남은 사람 수만 보여 주기', g8 and g9 and g10 and g11 and bsum['a']==0 and bsum['k']==1 and 'ns' not in bsum and '남은 사람 0' in gb.inner_text('.b-alive').replace('\n',' ') and gb.locator('.b-seats').count()==0 and '탈락했어요' in jc(b1), '%s %s %s %s %s'%(g8,g9,g10,g11,bsum))
    for x in (b1,b2,b3): x.context.close()
    gb.close(); d=t.locator('.poll[data-code="%s"] [data-act=del]'%G1); d.click(); d.click(); t.wait_for_timeout(1500)
    # ===== 한 칸에서 여러 질문을 한 번에 만들기 =====
    t.reload(); t.wait_for_timeout(800); qn=lambda i: t.locator('#qs .qb').nth(i)
    n0=t.locator('#qs .qb').count()==1 and not qn(0).locator('.q-del').is_visible() and not t.locator('#mfw').is_visible()
    t.fill('#mq','하나째'); t.locator('#mo input').nth(0).fill('가'); t.locator('#mo input').nth(1).fill('나')
    t.click('#qadd'); t.click('#qadd'); t.wait_for_timeout(100)
    qn(1).locator('.q-t1').check(); qn(1).locator('.q-q').fill('둘째'); qn(1).locator('.q-max').select_option('2')
    qn(2).locator('.q-o input').nth(0).fill('예'); t.click('#mc'); t.wait_for_timeout(300); n1='질문 3: 질문을 적어 주세요' in t.inner_text('#mm')
    qn(2).locator('.q-q').fill('셋째'); t.click('#mc'); t.wait_for_timeout(300); n2='질문 3: 보기를 2개 넘게' in t.inner_text('#mm')
    qn(2).locator('.q-o input').nth(1).fill('아니오'); t.click('#mc'); t.wait_for_timeout(1600)
    M1=t.locator('.poll').first.get_attribute('data-code'); ms=sibs(M1); mm=[dbget('polls/%s/meta'%c) for c in ms]
    check('여러 질문을 한 번에 만들기: 질문 더하기 · 질문마다 모자란 곳 안내 · 저장하면 번호 셋이 묶음으로', n0 and n1 and n2 and len(ms)==3 and ms[0]==M1 and [m['q'] for m in mm]==['하나째','둘째','셋째'] and mm[1].get('type')=='text' and mm[1].get('max')==2 and all(sibs(c)==ms for c in ms) and all(m.get('flow')=='self' and m['open'] is True for m in mm) and '3개가 한 묶음' in t.inner_text('#mm') and t.locator('#qs .qb').count()==1 and t.input_value('#mq')=='' and '외 2개' in t.inner_text('.poll[data-code="%s"]'%M1))
    ob=t.locator('.poll[data-code="%s"] [data-act=open]'%M1); ob.click(); t.wait_for_timeout(900); n3=all(dbget('polls/%s/meta/open'%c) is False for c in ms) and '마감' in t.inner_text('.poll[data-code="%s"] .tag'%M1)
    t.locator('.poll[data-code="%s"] [data-act=open]'%M1).click(); t.wait_for_timeout(900); n4=all(dbget('polls/%s/meta/open'%c) is True for c in ms)
    d=t.locator('.poll[data-code="%s"] [data-act=del]'%M1); d.click(); d.click(); t.wait_for_timeout(1500)
    check('묶음 카드: 마감하기·다시 받기·지우기가 질문 전체에', n3 and n4 and all(dbget('polls/%s'%c) is None for c in ms))
    # ===== 질문 잇기 (묶음) =====
    sibs=lambda c: (lambda v: (list(v.values()) if isinstance(v,dict) else v) or [])(dbget('polls/%s/meta/sib'%c))
    t.reload(); t.wait_for_timeout(800)
    t.fill('#mq','첫째 질문'); t.locator('#mo input').nth(0).fill('가'); t.locator('#mo input').nth(1).fill('나'); t.fill('#ml','https://musicalpe.github.io/apps/'); t.click('#mc'); t.wait_for_timeout(800)
    A=t.locator('.poll').first.get_attribute('data-code')
    qn=lambda i: t.locator('#qs .qb').nth(i)
    eA=lambda: (t.locator('.poll[data-code="%s"] [data-act=edit]'%A).click(), t.wait_for_timeout(500))
    eA(); x0=not t.locator('#mfw').is_visible() and not qn(0).locator('.q-del').is_visible(); t.click('#qadd'); t.wait_for_timeout(100)
    e0=x0 and '설문 고치기' in t.inner_text('#mh') and t.locator('#mfw').is_visible() and A in t.inner_text('#me') and '고친 내용 저장' in t.inner_text('#mc') and t.locator('#qs .qb').count()==2 and qn(1).locator('.q-del').is_visible() and t.locator('#mq').count()==1
    qn(1).locator('.q-t1').check(); qn(1).locator('.q-q').fill('둘째 질문'); t.click('#mc'); t.wait_for_timeout(1300)
    B=[c for c in sibs(A) if c!=A][0] if len(sibs(A))==2 else ''
    check('질문 잇기: 둘째 질문이 묶음으로 이어짐 (두 설문 모두 순서 목록·넘어가는 방식)', e0 and sibs(A)==[A,B] and sibs(B)==[A,B] and dbget('polls/%s/meta/flow'%A)=='self' and dbget('polls/%s/meta/flow'%B)=='self' and dbget('polls/%s/meta/type'%B)=='text' and '고쳤어요' in t.inner_text('#mm') and '설문 만들기' in t.inner_text('#mh') and dbget('polls/%s/meta/q'%A)=='첫째 질문')
    eA(); e1=t.locator('#qs .qb').count()==2 and qn(1).locator('.q-q').input_value()=='둘째 질문' and qn(1).locator('.q-t1').is_checked() and qn(1).locator('.q-t0').is_disabled()
    t.click('#qadd'); qn(2).locator('.q-q').fill('셋째 질문'); qn(2).locator('.q-o input').nth(0).fill('예'); qn(2).locator('.q-o input').nth(1).fill('아니오'); t.select_option('#mfl','with'); t.click('#mc'); t.wait_for_timeout(1500)
    C=sibs(A)[2] if len(sibs(A))==3 else ''
    card=t.inner_text('.poll[data-code="%s"]'%A)
    check('질문 더하기: 셋째까지 · 넘어가는 방식은 묶음 전체에 · 목록에는 카드 하나에 질문 순서대로', e1 and sibs(A)==[A,B,C]==sibs(B)==sibs(C) and [dbget('polls/%s/meta/flow'%c) for c in (A,B,C)]==['with']*3 and t.locator('.poll[data-code="%s"]'%B).count()==0 and '질문 3개' in card and '외 2개' in card and t.locator('.poll[data-code="%s"] .qlist li'%A).count()==3 and card.index('둘째 질문')<card.index('셋째 질문'), card[:120])
    # 선생님과 함께 넘어가기
    W=b.new_context(viewport={'width':390,'height':800}); setup(W); wp=W.new_page(); wp.on('pageerror',lambda e: errs.append(str(e))); wp.goto(APP+'?p='+A); wp.wait_for_timeout(500)
    e2='질문 1 / 3' in wp.inner_text('#jc'); wp.locator('.opt').nth(0).click(); wp.click('#js'); wp.wait_for_timeout(500)
    check('함께 넘어가기: 답을 내면 다음 QR을 기다리라는 안내 (다음 단추·끝 주소 없음)', e2 and wp.locator('#jnx').count()==0 and 'QR을 찍어' in wp.inner_text('#jc') and '앱 모음' not in wp.inner_text('#jc')); W.close()
    # 고치기로 스스로 넘어가기로 바꿈
    eA(); e3=t.locator('#mfw').is_visible() and t.input_value('#mfl')=='with' and t.locator('#qs .qb').count()==3
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
    eA(); t.click('#qadd'); qn(3).locator('.q-q').fill('넷째 질문'); qn(3).locator('.q-o input').nth(0).fill('좋아요'); qn(3).locator('.q-o input').nth(1).fill('글쎄요'); t.select_option('#mfl','with'); t.click('#mc'); t.wait_for_timeout(1600)
    D=sibs(A)[3] if len(sibs(A))==4 else ''
    md=lambda c: dbget('polls/%s/meta'%c)
    check('함께 넘어가기로 이으면: 새 질문은 대기(닫힘) · 이미 답이 있는 앞 질문은 열린 채', md(D).get('open') is False and md(D).get('wait') is True and all(md(c).get('open') is True and md(c).get('wait') is None for c in (A,B,C)) and '대기' in t.inner_text('.poll[data-code="%s"] .qlist li:nth-child(4)'%A) and [md(c)['flow'] for c in (A,B,C,D)]==['with']*4)
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
    t.reload(); t.wait_for_timeout(900)
    def dropq(i):
        eA(); d=qn(i).locator('.q-del'); d.click(); d.click(); t.wait_for_timeout(200); t.click('#mc'); t.wait_for_timeout(1500)
    dropq(3); e10=dbget('polls/%s'%D) is None and sibs(A)==[A,B,C]
    dropq(1); e11=sibs(A)==[A,C]==sibs(C) and dbget('polls/%s'%B) is None and dbget('polls/%s/meta/q'%C)=='셋째 질문' and len(dbget('polls/%s/votes'%A))>=2
    dropq(1)
    check('고치기에서 질문을 지우면 남은 순서가 고쳐지고(답이 있으면 두 번 눌러야 지워짐) · 하나만 남으면 묶음이 풀림', e10 and e11 and dbget('polls/%s'%C) is None and sibs(A)==[] and dbget('polls/%s/meta/flow'%A) is None and '외 ' not in t.inner_text('.poll[data-code="%s"]'%A) and t.locator('.poll[data-code="%s"] .qlist'%A).count()==0, '%s %s'%(e10,e11))
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
    t.locator('details.guide summary').click(); check('첫 화면 사용 안내', '100개까지' in t.inner_text('details.guide') and '구글 로그인' in t.inner_text('details.guide'))
    for i in range(100):
        c='zz%04d'%i; dbput('polls/%s/meta'%c,{'owner':'teacher1','q':'상한 시험 %d'%i,'opts':['가','나'],'open':True,'ask':False,'res':True,'at':1000+i},'teacher1'); dbput('users/teacher1/polls/%s'%c,1000+i,'teacher1')
    t.reload(); t.wait_for_timeout(5000); n0=len(dbget('users/teacher1/polls?auth=teacher1'.replace('?auth=teacher1','')) or {}) if False else t.locator('.poll').count()
    t.fill('#mq','서른한 번째'); t.locator('#mo input').nth(0).fill('가'); t.locator('#mo input').nth(1).fill('나'); t.click('#mc'); t.wait_for_timeout(600)
    check('설문 수 상한: 100개가 넘으면 더 못 만들고 안내', '100개까지' in t.inner_text('#mm') and t.locator('.poll').count()==n0 and n0>=100)
    t.click('#lo'); t.wait_for_timeout(300); check('로그아웃 → 로그인 단추', t.locator('#lg').count()==1)
    # 연결 정보가 없을 때
    N=b.new_context(); N.route(re.compile(r'.*/config\.js(\?.*)?$'), lambda r: r.fulfill(body='window.HEARIM_CONFIG=null;',content_type='application/javascript')); n1=N.new_page(); n1.goto(APP); n1.wait_for_timeout(300); check('연결 정보 없으면 안내만', '아직 연결 전' in n1.inner_text('#app'))
    check('화면 오류 없음', not errs, str(errs[:3]))
finally:
    web.terminate(); db.terminate()
print('결과:', '모두 통과' if ok else '실패 있음')
