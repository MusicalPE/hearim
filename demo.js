/* 헤아림 미리보기(?demo) — 설치·로그인 없이 지어낸 설문과 퀴즈로 둘러보기
   · 실제 파이어베이스 대신, 이 브라우저 안에만 있는 가짜 데이터베이스를 씀 (dev/mockdb.py 의 규칙을 그대로 옮김)
   · 같은 브라우저의 다른 탭(결과 화면·참여 화면)끼리는 자료가 이어져서, 한 탭에서 답하면 다른 탭 결과 화면에 바로 올라옴
   · 눌러 본 내용은 이 기기에만 남고, 12시간이 지나면 처음 상태로 돌아감. 실제 설문 자료는 건드리지 않음 */
(function(){
  'use strict';
  if (!new URLSearchParams(location.search).has('demo')) return;
  var SEED = {"polls":{"xwk46c":{"meta":{"owner":"demo-teacher","q":"줄넘기는 유산소 운동이다","open":true,"ask":false,"res":false,"at":1795146680759,"opts":{"0":"O","1":"X"},"sib":{"0":"xwk46c","1":"p5nbqc","2":"zedkw9"},"flow":"with","qz":"bell","seats":25,"nshow":true}},"p5nbqc":{"meta":{"owner":"demo-teacher","q":"배구에서 한 팀은 몇 명이 경기할까요?","open":false,"ask":false,"res":false,"at":1795146680760,"opts":{"0":"5명","1":"6명","2":"9명","3":"11명"},"sib":{"0":"xwk46c","1":"p5nbqc","2":"zedkw9"},"flow":"with","qz":"bell","seats":25,"nshow":true,"wait":true}},"zedkw9":{"meta":{"owner":"demo-teacher","q":"피구에서 공을 잡으면 아웃이 아니다","open":false,"ask":false,"res":false,"at":1795146680761,"opts":{"0":"O","1":"X"},"sib":{"0":"xwk46c","1":"p5nbqc","2":"zedkw9"},"flow":"with","qz":"bell","seats":25,"nshow":true,"rv":true,"wait":true}},"wa3eux":{"meta":{"owner":"demo-teacher","q":"줄넘기를 할 때 가장 많이 쓰는 몸의 부분은?","open":true,"ask":false,"res":true,"at":1795146683826,"opts":{"0":"팔","1":"종아리","2":"허리","3":"목"}},"votes":{"nz8kf9tm5n7f2h9h":{"c":1,"at":1795144275454},"q0oi459d43j5p5k8":{"c":1,"at":1795144315454},"aku35s3x10elxbbc":{"c":2,"at":1795144355454},"vg645jcn0ivgxv47":{"c":1,"at":1795144395454},"9ns1v1q9dssw5zv6":{"c":1,"at":1795144435454},"r6wn5hvmutifcz9z":{"c":1,"at":1795144475454},"8dztgacm4d68yjfn":{"c":1,"at":1795144515454},"c3lglc0gaxit9qtl":{"c":2,"at":1795144555454},"0cub1d57ch0z2eay":{"c":1,"at":1795144595454},"j409gf4nja1aahfn":{"c":3,"at":1795144635454},"hi4brp2ldxjfs953":{"c":0,"at":1795144675454},"qdcadafyttk5dux2":{"c":0,"at":1795144715454},"4kjhxk04y2rvsrdv":{"c":0,"at":1795144755454},"ajt1pyyyo2sauqr1":{"c":2,"at":1795144795454},"kcsjjr95w8f895ym":{"c":1,"at":1795144835454},"otdz3nqay38f8weo":{"c":0,"at":1795144875454},"z7q7u46mmnmflsxw":{"c":1,"at":1795144915454},"z7jpc5xgx3fjubwr":{"c":1,"at":1795144955454},"7bgcn5nqr1g2iqcv":{"c":0,"at":1795144995454},"mlyfbdc9x35ezhfq":{"c":1,"at":1795145035454},"uof6zl2kxpolcqwd":{"c":1,"at":1795145075454},"9bdq64dgjuamt2g4":{"c":0,"at":1795145115454},"uxqyhx4yk2pja3mc":{"c":1,"at":1795145155454},"koexi2gybe2vuo4h":{"c":1,"at":1795145195454},"xjvodl29j2jr00pj":{"c":1,"at":1795145235454},"brsvkq5gu34hj6dn":{"c":1,"at":1795145275454}}},"xrvkzj":{"meta":{"owner":"demo-teacher","q":"오늘 체육 수업은 어땠나요?","open":true,"ask":true,"res":true,"at":1795146686392,"opts":{"0":"아주 재밌었어요","1":"재밌었어요","2":"그저 그랬어요","3":"힘들었어요"},"sib":{"0":"xrvkzj","1":"u3jh5h"},"flow":"self"},"votes":{"jpuu3xf6mzkp0ec4":{"c":0,"at":1795144275454},"98uk1geqfng052lo":{"c":2,"at":1795144315454},"i03p8hssrrxqqm2p":{"c":1,"at":1795144355454},"lppjsmuezqp67og3":{"c":1,"at":1795144395454},"cga4o2xcsohdmmex":{"c":2,"at":1795144435454},"6l2qagwncxvjcnqc":{"c":0,"at":1795144475454},"nau0xltenc594e0g":{"c":1,"at":1795144515454},"z9j8fkzr0st0dtw0":{"c":1,"at":1795144555454},"0bxmzzna1k1hfzx3":{"c":2,"at":1795144595454},"kiad9jzfx6kjwsk7":{"c":0,"at":1795144635454},"kegy5mtic4udyfko":{"c":0,"at":1795144675454},"zm4lncz7kywhjpmc":{"c":1,"at":1795144715454},"9cuhy39t0tp1yx26":{"c":1,"at":1795144755454},"2lba53p23l4zgeiw":{"c":1,"at":1795144795454},"1xf266ccifu6fd6y":{"c":0,"at":1795144835454},"ibehmi5skoewqkur":{"c":0,"at":1795144875454},"3jq64nq6puxcmlzk":{"c":1,"at":1795144915454},"ruykqh7dx297gq8z":{"c":0,"at":1795144955454},"xqyxjxvf2olds7qt":{"c":0,"at":1795144995454},"uacojs106xdi5ocb":{"c":0,"at":1795145035454},"dawtg7w8o0tinx4k":{"c":0,"at":1795145075454},"iapj2gejrzqad9w2":{"c":1,"at":1795145115454},"75pkacd8bzlpkdga":{"c":3,"at":1795145155454},"9mj0m760l6tetd48":{"c":3,"at":1795145195454}}},"u3jh5h":{"meta":{"owner":"demo-teacher","q":"다음 시간에 더 하고 싶은 것은?","open":true,"ask":true,"res":true,"at":1795146686393,"opts":{"0":"게임 시간","1":"기능 연습","2":"팀 경기"},"sib":{"0":"xrvkzj","1":"u3jh5h"},"flow":"self"},"votes":{"ay13f2logqochvqd":{"c":0,"at":1795144275454},"r917qsnf6akqpmku":{"c":0,"at":1795144315454},"myvpy8447ab1otnz":{"c":0,"at":1795144355454},"ekjcbhgkwjbbcice":{"c":0,"at":1795144395454},"cexm8eygpnnhccfs":{"c":0,"at":1795144435454},"4gignsuv1qbwqsdx":{"c":0,"at":1795144475454},"u64sb0b17gw4d8nf":{"c":0,"at":1795144515454},"sk1a7msdaw5g5l5w":{"c":0,"at":1795144555454},"6qksno5khf59guwg":{"c":0,"at":1795144595454},"zzf1bxntq186kyo3":{"c":2,"at":1795144635454},"i8cwu7j29uk32qoi":{"c":2,"at":1795144675454},"v3p6mrtjjpu7wkpu":{"c":2,"at":1795144715454},"mqgkgmyjjtt1rmgg":{"c":2,"at":1795144755454},"rny3caz1o6s3bjqz":{"c":2,"at":1795144795454},"ap10oolh31uqg0pz":{"c":2,"at":1795144835454},"kq143b07luay5gcq":{"c":2,"at":1795144875454},"8nkm7wg38n46bx7v":{"c":2,"at":1795144915454},"03nlz6hwdqryzdae":{"c":1,"at":1795144955454},"00wqgotz7oz3nkie":{"c":1,"at":1795144995454},"m49ojw03s9i4wory":{"c":1,"at":1795145035454},"q1l4arwptu451fxj":{"c":1,"at":1795145075454}}},"8fsa33":{"meta":{"owner":"demo-teacher","q":"체육 하면 떠오르는 낱말은?","open":true,"ask":false,"res":true,"at":1795146689111,"type":"text","max":3},"votes":{"2g158z6tnovmizwd":{"a":{"0":"땀","1":"친구","2":"운동장"},"at":1795144275454},"eq1kdfy6spsc3lkr":{"a":{"0":"줄넘기","1":"친구","2":"피구"},"at":1795144315454},"xv9upctnwlavyf4r":{"a":{"0":"체육관","1":"피구","2":"피구"},"at":1795144355454},"p6afqfjzczbttof7":{"a":{"0":"땀","1":"신나요","2":"공"},"at":1795144395454},"yu5jsjc616i76bof":{"a":{"0":"친구","1":"물","2":"친구"},"at":1795144435454},"xgy29db8p5qa3e68":{"a":{"0":"피구","1":"달리기","2":"친구"},"at":1795144475454},"e4qeqpno35ye4scm":{"a":{"0":"줄넘기","1":"농구","2":"땀"},"at":1795144515454},"vqtia4d5rgn5s7s3":{"a":{"0":"줄넘기","1":"줄넘기","2":"친구"},"at":1795144555454},"9mtf4bs3e62rynne":{"a":{"0":"체육관","1":"물","2":"땀"},"at":1795144595454},"7qxi6rhxo55zbka5":{"a":{"0":"협동","1":"줄넘기","2":"친구"},"at":1795144635454},"tj0wyuhvauvzhmas":{"a":{"0":"농구","1":"체육관","2":"피구"},"at":1795144675454},"zyex1rdrgdsjpr16":{"a":{"0":"피구","1":"달리기","2":"줄넘기"},"at":1795144715454},"x1bz99nfd02is5d9":{"a":{"0":"줄넘기","1":"공","2":"물"},"at":1795144755454},"0vstqqzpt49zhkke":{"a":{"0":"친구","1":"축구","2":"친구"},"at":1795144795454},"59o2v21i9mpflv9f":{"a":{"0":"공","1":"땀","2":"응원"},"at":1795144835454},"qmb0y07nyrvd5rxi":{"a":{"0":"줄넘기","1":"운동장","2":"달리기"},"at":1795144875454},"nfrpyz21tbic145a":{"a":{"0":"농구","1":"땀","2":"신나요"},"at":1795144915454},"732pgojj7g3f9cai":{"a":{"0":"줄넘기","1":"피구","2":"줄넘기"},"at":1795144955454},"tiq71hget7myqoaa":{"a":{"0":"운동장","1":"협동","2":"달리기"},"at":1795144995454},"rup47p9pb0tdbm50":{"a":{"0":"피구","1":"재미","2":"체육관"},"at":1795145035454},"1xo5cv0xzmas6en5":{"a":{"0":"줄넘기","1":"피구","2":"운동장"},"at":1795145075454},"mo3oqsg5lo50djzd":{"a":{"0":"공","1":"재미","2":"물"},"at":1795145115454},"j0ddlz2uhfkvml73":{"a":{"0":"공","1":"피구","2":"줄넘기"},"at":1795145155454},"yxv2kgafrfw0h9ny":{"a":{"0":"달리기","1":"재미","2":"농구"},"at":1795145195454},"t1fd4mx82mux4b0p":{"a":{"0":"달리기","1":"물","2":"줄넘기"},"at":1795145235454},"zcyc3edqmevxrvcq":{"a":{"0":"응원","1":"신나요","2":"물"},"at":1795145275454}}},"skz65m":{"meta":{"owner":"demo-teacher","q":"다음 체육 시간에 하고 싶은 활동은?","open":true,"ask":true,"res":true,"at":1795146691141,"opts":{"0":"피구","1":"줄넘기","2":"이어달리기","3":"티볼"}},"votes":{"zdoc9is0j8ht9lgm":{"c":1,"t":"피구는 언제 해도 재밌어요","at":1795144275454},"xg9edn581u33xtpl":{"c":0,"t":"줄넘기 기록을 깨고 싶어요","at":1795144315454},"pft75v2seh60kvj5":{"c":2,"t":"다 같이 뛰는 게 좋아요","at":1795144355454},"0ce9uvw53efr4edt":{"c":0,"t":"티볼을 처음 해 보고 싶어요","at":1795144395454},"2sywb3wkh5dnsipz":{"c":0,"t":"바통 넘기는 게 재밌어요","at":1795144435454},"z5fk2z9ri19r0wyo":{"c":3,"t":"","at":1795144475454},"jfljooa5lqsaj08x":{"c":1,"t":"","at":1795144515454},"ui6d39zzzzg4zdme":{"c":1,"t":"","at":1795144555454},"n2khvdgaj8gxbeny":{"c":3,"t":"","at":1795144595454},"jqwx4hh5344tfjgv":{"c":1,"t":"","at":1795144635454},"q4k7bn7xj8b7tfq7":{"c":1,"t":"","at":1795144675454},"xkwo886vompzom75":{"c":3,"t":"","at":1795144715454},"wbbr4qmw2wxfogo4":{"c":1,"t":"","at":1795144755454},"mvn4a4wfhym4l1vf":{"c":2,"t":"","at":1795144795454},"z3zfkkibj3j4wj99":{"c":0,"t":"","at":1795144835454},"ibag7i1mnbqns6pu":{"c":0,"t":"","at":1795144875454},"q80idw3706i8j76b":{"c":1,"t":"","at":1795144915454},"2lajlj4h9du7794g":{"c":2,"t":"","at":1795144955454},"9dpmrcg629be2u66":{"c":1,"t":"","at":1795144995454},"mr26846p7q9m2i0h":{"c":0,"t":"","at":1795145035454},"z2uep1enthjxjqi3":{"c":1,"t":"","at":1795145075454},"ogz5kok16zv0mwuf":{"c":0,"t":"","at":1795145115454},"xbv932byv7s6ehog":{"c":0,"t":"","at":1795145155454},"fqrclri1qzj865uf":{"c":2,"t":"","at":1795145195454},"rdl1erbfqfoeqh3a":{"c":1,"t":"","at":1795145235454},"v90ric7phkqdlmtt":{"c":0,"t":"","at":1795145275454},"7ns26lrwbqcab69m":{"c":1,"t":"","at":1795145315454}}}},"users":{"demo-teacher":{"polls":{"xwk46c":1795146680759,"p5nbqc":1795146680760,"zedkw9":1795146680761,"wa3eux":1795146683826,"xrvkzj":1795146686392,"u3jh5h":1795146686393,"8fsa33":1795146689111,"skz65m":1795146691141}}},"keys":{"xwk46c":{"a":0},"p5nbqc":{"a":1},"zedkw9":{"a":0},"wa3eux":{"a":1}}}, SEED_AT = 1795146675454, OWNER = 'demo-teacher';
  var KEY = 'hearim-demo-db', AT_KEY = 'hearim-demo-at', PFX = 'hdemo_', URL0 = 'https://hearim-demo.invalid';
  var LS = window.localStorage, DB = {};
  function load(){ try { DB = JSON.parse(LS.getItem(KEY) || 'null') || {}; } catch (e) { DB = {}; } }
  function save(){ try { LS.setItem(KEY, JSON.stringify(DB)); } catch (e) {} }
  // 처음 열거나 12시간이 지났으면 지어낸 자료로 다시 채우고, 시간을 지금에 맞춤
  (function seed(){
    var at = 0; try { at = Number(LS.getItem(AT_KEY)) || 0; } catch (e) {}
    try { if (LS.getItem(KEY) && Date.now() - at < 12 * 3600 * 1000) { load(); return; } } catch (e) {}
    var d = Date.now() - SEED_AT;
    var shift = function(v){ return typeof v === 'number' && v > 1.5e12 && v < 3e12 ? v + d : Array.isArray(v) ? v.map(shift) : (v && typeof v === 'object' ? Object.keys(v).reduce(function(o, k){ o[k] = shift(v[k]); return o; }, {}) : v); };
    DB = shift(SEED);
    try { Object.keys(LS).forEach(function(k){ if (k.indexOf(PFX) === 0) LS.removeItem(k); }); LS.setItem(AT_KEY, String(Date.now())); } catch (e) {}
    save();
  })();
  /* ---- 가짜 데이터베이스 (mockdb.py 와 같은 규칙) ---- */
  var isObj = function(v){ return v && typeof v === 'object' && !Array.isArray(v); };
  function get(path){ var cur = DB; for (var i = 0; i < path.length; i++) { if (!isObj(cur) || !(path[i] in cur)) return null; cur = cur[path[i]]; } return cur === undefined ? null : cur; }
  function put(path, val){
    if (!path.length) { DB = val || {}; return; }
    var cur = DB; for (var i = 0; i < path.length - 1; i++) { if (!isObj(cur[path[i]])) cur[path[i]] = {}; cur = cur[path[i]]; }
    if (val == null) delete cur[path[path.length - 1]]; else cur[path[path.length - 1]] = val;
    for (var j = path.length - 1; j > 0; j--) { var node = get(path.slice(0, j)); if (isObj(node) && !Object.keys(node).length) put(path.slice(0, j), null); }
  }
  function sv(v){
    if (Array.isArray(v)) { var o = {}; v.forEach(function(x, i){ if (x != null) o[String(i)] = sv(x); }); return o; }
    if (isObj(v)) { if (v['.sv'] === 'timestamp' && Object.keys(v).length === 1) return Date.now(); var r = {}; Object.keys(v).forEach(function(k){ r[k] = sv(v[k]); }); return r; }
    return v;
  }
  var vals = function(x){ return Array.isArray(x) ? x : (isObj(x) ? Object.keys(x).map(function(k){ return x[k]; }) : null); };
  function allowed(path, val, auth){
    var m, owner;
    if (path[0] === 'users') return path.length >= 2 && auth === path[1];
    if (path[0] === 'keys') {
      m = path.length >= 2 ? get(['polls', path[1], 'meta']) : null;
      return !!auth && m != null && m.owner === auth && path.length === 2 && (val == null || (isObj(val) && ((Object.keys(val).join() === 'a' && Number.isInteger(val.a) && val.a >= 0 && val.a <= 9) || Object.keys(val).every(function(k){ return k === 'a' || k === 'm' || k === 't'; }))));
    }
    if ((path[0] === 'seats' || path[0] === 'skeys' || path[0] === 'scores') && path.length >= 2) {
      m = get(['polls', path[1], 'meta']); owner = !!auth && m != null && m.owner === auth;
      if (path[0] === 'scores') return owner;
      if (path.length === 2) return owner && val == null;
      if (path.length !== 3 || !/^[0-9]{1,2}$/.test(path[2])) return false;
      if (val == null) return owner;
      var good = typeof val === 'string' && (path[0] === 'seats' ? /^[a-z0-9]{6}$/ : /^[a-z0-9]{16}$/).test(val);
      return good && (get(path) == null || owner);
    }
    if (path[0] !== 'polls' || path.length < 3 || !/^[a-z0-9]{6}$/.test(path[1])) return false;
    m = get(['polls', path[1], 'meta']);
    if (path[2] === 'meta') { if (!auth) return false; if (m == null) return path.length === 3 && isObj(val) && val.owner === auth; return m.owner === auth; }
    if (path[2] === 'votes') {
      owner = !!auth && m != null && m.owner === auth;
      if (path.length === 3) return val == null && owner;
      if (!/^[a-z0-9]{12,24}$/.test(path[3])) return false;
      if (val == null) return owner;
      if (!(path.length === 4 && m != null && m.open === true && m.rev == null && isObj(val))) return false;
      if ('a' in val) { var a = vals(val.a); return !!a && a.length >= 1 && a.length <= 5 && a.every(function(x){ return typeof x === 'string' && x.length >= 1 && x.length <= 20; }); }
      if ('m' in val) { var mm = vals(val.m); return !!mm && mm.length >= 1 && mm.length <= 10 && mm.every(function(x){ return Number.isInteger(x) && x >= 0 && x <= 9; }) && String(val.t || '').length <= 200; }
      return Number.isInteger(val.c) && val.c >= 0 && val.c <= 9 && String(val.t || '').length <= 200;
    }
    return false;
  }
  function canRead(path, auth){
    var m;
    if (path[0] === 'users' && (path.length < 2 || auth !== path[1])) return false;
    if (path.length === 1 && path[0] === 'polls') return false;
    if (path[0] === 'skeys' || (path[0] === 'scores' && path.length < 3)) { m = path.length >= 2 ? get(['polls', path[1], 'meta']) : null; if (!(path[0] === 'skeys' && auth && m != null && m.owner === auth) && !(path[0] === 'scores' && path.length >= 3)) return false; }
    if (path[0] === 'keys') { m = path.length >= 2 ? get(['polls', path[1], 'meta']) : null; if (!(auth && m != null && m.owner === auth)) return false; }
    return true;
  }
  var split = function(p){ return String(p || '').split('/').filter(Boolean); };
  var clone = function(v){ return v == null ? null : JSON.parse(JSON.stringify(v)); };
  function read(path, auth){ load(); if (!canRead(path, auth)) { var e = new Error('PERMISSION_DENIED'); e.code = 'PERMISSION_DENIED'; throw e; } return clone(get(path)); }
  function write(path, val, auth){ load(); val = sv(val); if (!allowed(path, val, auth)) { var e = new Error('PERMISSION_DENIED'); e.code = 'PERMISSION_DENIED'; throw e; } put(path, val); save(); notify(); return clone(val); }
  /* ---- 참여 화면이 쓰는 주소 읽고 쓰기(fetch) ---- */
  var realFetch = window.fetch.bind(window);
  window.fetch = function(input, opt){
    var u = typeof input === 'string' ? input : (input && input.url) || '';
    if (u.indexOf(URL0) !== 0) return realFetch(input, opt);
    var rest = u.slice(URL0.length).split('?')[0].replace(/\.json$/, ''), path = split(rest), m = ((opt && opt.method) || 'GET').toUpperCase();
    return new Promise(function(ok){ setTimeout(function(){
      var status = 200, body;
      try { body = m === 'GET' ? read(path, '') : write(path, m === 'DELETE' ? null : JSON.parse(opt.body || 'null'), ''); }
      catch (e) { status = 401; body = { error: 'Permission denied' }; }
      ok(new Response(JSON.stringify(body), { status: status, headers: { 'Content-Type': 'application/json' } }));
    }, 60); });
  };
  /* ---- 만들기·결과 화면이 쓰는 파이어베이스 SDK 흉내 ---- */
  var uid = OWNER, authCbs = [], subs = [];
  function notify(){ setTimeout(function(){ subs.forEach(function(s){ var v; try { v = read(s.path, uid); } catch (e) { return; } var j = JSON.stringify(v); if (j !== s.last) { s.last = j; s.cb(snap(s.path, v)); } }); }, 0); }
  window.addEventListener('storage', function(e){ if (e.key === KEY) notify(); });
  function snap(path, v){ return { val: function(){ return clone(v); }, exists: function(){ return v != null; }, key: path[path.length - 1] || null }; }
  function ref(p){
    var path = split(p), mine = [];
    var later = function(fn){ return new Promise(function(ok, no){ setTimeout(function(){ try { ok(fn()); } catch (e) { no(e); } }, 30); }); };
    return {
      key: path[path.length - 1] || null,
      child: function(c){ return ref(path.concat(split(c)).join('/')); },
      set: function(v){ return later(function(){ write(path, v, uid); }); },
      remove: function(){ return later(function(){ write(path, null, uid); }); },
      once: function(){ return later(function(){ return snap(path, read(path, uid)); }); },
      on: function(ev, cb, err){ var s = { path: path, cb: cb, last: undefined }; subs.push(s); mine.push(s); setTimeout(function(){ try { var v = read(path, uid); s.last = JSON.stringify(v); cb(snap(path, v)); } catch (e) { if (err) err(e); } }, 30); return cb; },
      off: function(){ subs = subs.filter(function(s){ return mine.indexOf(s) < 0; }); mine = []; }
    };
  }
  var user = function(){ return uid ? { uid: uid, displayName: '미리보기 선생님' } : null; };
  var fireAuth = function(){ authCbs.forEach(function(cb){ setTimeout(function(){ cb(user()); }, 0); }); };
  function auth(){ return {
    onAuthStateChanged: function(cb){ authCbs.push(cb); setTimeout(function(){ cb(user()); }, 0); return function(){}; },
    signInWithPopup: function(){ uid = OWNER; fireAuth(); return Promise.resolve({ user: user() }); },
    signOut: function(){ uid = ''; fireAuth(); return Promise.resolve(); },
    get currentUser(){ return user(); }
  }; }
  auth.GoogleAuthProvider = function(){};
  function database(){ return { ref: ref }; }
  database.ServerValue = { TIMESTAMP: { '.sv': 'timestamp' } };
  var fb = { apps: [1], initializeApp: function(){}, auth: auth, database: database };
  window.HEARIM_DEMO = { firebase: fb, prefix: PFX };
  // 실제 연결 주소 대신 가짜 주소를 쓰게 함 (실제 설문 자료에 닿지 않게)
  window.HEARIM_CONFIG = Object.assign({}, window.HEARIM_CONFIG || {}, { databaseURL: URL0, apiKey: 'demo' });
  // 붙여 넣어 만들기(2.7.0): 칸을 열면 예시 글을 미리 채워, 그대로 '질문 만들기'만 눌러 보게 함
  var PASTE = '1. 오늘 체육 시간에 가장 재미있었던 활동은?\n- 피구\n- 줄넘기\n- 이어달리기\n\n2. 다음 시간에 해 보고 싶은 운동을 적어 주세요 (적어서 내기)\n\n3. 준비 운동에서 해 본 것을 모두 골라 주세요 (여러 개)\n- 체조\n- 스트레칭\n- 가볍게 달리기\n- 줄넘기';
  document.addEventListener('click', function(e){
    var t = e.target && e.target.closest && e.target.closest('#qpaste'); if (!t) return;
    setTimeout(function(){ var a = document.getElementById('qpt'), w = document.getElementById('qpw'); if (a && w && !w.hidden && !a.value) a.value = PASTE; }, 0);
  }, true);
  // 안내 띠
  document.addEventListener('DOMContentLoaded', function(){
    var b = document.createElement('div');
    b.className = 'demo-bar';
    b.textContent = '미리보기 · 지어낸 설문과 퀴즈예요. 결과 화면과 참여 화면을 다른 탭으로 열어 답하면 바로 올라와요. 눌러 본 내용은 이 기기에만 남아요.';
    b.style.cssText = 'background:#0B6E70;color:#fff;font-size:13px;line-height:1.5;text-align:center;padding:7px 12px;position:relative;z-index:50';
    document.body.insertBefore(b, document.body.firstChild);
  });
})();
