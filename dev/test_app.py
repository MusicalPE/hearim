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
    with t.expect_download() as dl: t.locator('.poll [data-act=csv]').first.click()
    csv=open(dl.value.path(),encoding='utf-8-sig').read()
    check('답 내려받기 (6줄 · 연락처 같은 건 없음)', csv.count('\n')==7 and '주 500회 적금' in csv and '하루 빠져도' in csv, dl.value.suggested_filename)
    t.locator('.poll [data-act=open]').first.click(); t.wait_for_timeout(600); check('다시 받기', dbget('polls/%s/meta/open'%code) is True and '받는 중' in t.inner_text('.poll'))
    bd.wait_for_timeout(600); bd.click('#bcl'); check('답 지우기는 한 번 더 눌러야', '한 번 더' in bd.inner_text('#bcl') and len(dbget('polls/%s/votes'%code))==6)
    bd.click('#bcl'); bd.wait_for_timeout(800); check('답 지우기 → 0명', dbget('polls/%s/votes'%code) is None and '0' in bd.inner_text('.b-count'))
    t.locator('.poll [data-act=del]').first.click(); t.locator('.poll [data-act=del]').first.click(); t.wait_for_timeout(900)
    check('설문 지우기', dbget('polls/%s'%code) is None and '아직 만든 설문이 없어요' in t.inner_text('#my'))
    t.click('#lo'); t.wait_for_timeout(300); check('로그아웃 → 로그인 단추', t.locator('#lg').count()==1)
    # 연결 정보가 없을 때
    N=b.new_context(); n1=N.new_page(); n1.goto(APP); n1.wait_for_timeout(300); check('연결 정보 없으면 안내만', '아직 연결 전' in n1.inner_text('#app'))
    check('화면 오류 없음', not errs, str(errs[:3]))
finally:
    web.terminate(); db.terminate()
print('결과:', '모두 통과' if ok else '실패 있음')
