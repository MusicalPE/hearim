// 시험용 가짜 파이어베이스 SDK — 가짜 데이터베이스(mockdb.py)에 주소로 읽고 쓰며, 0.25초마다 다시 읽어 실시간을 흉내 냄
(function(){
  var cfg = null, uid = null, authCbs = [];
  try { uid = localStorage.getItem('stub_uid') || null; } catch (e) {}
  function url(p){ return cfg.databaseURL.replace(/\/$/, '') + '/' + p + '.json' + (uid ? '?auth=' + uid : ''); }
  function req(p, m, body){ return fetch(url(p), { method: m, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) }).then(function(r){ return r.json().then(function(j){ if (!r.ok) throw new Error(j && j.error || 'PERMISSION_DENIED'); return j; }); }); }
  function snap(p, v){ return { val: function(){ return v; }, exists: function(){ return v != null; }, key: p.split('/').pop() }; }
  function ref(p){
    var timer = 0;
    return {
      child: function(c){ return ref(p + '/' + c); },
      set: function(v){ return req(p, 'PUT', v); },
      remove: function(){ return req(p, 'DELETE'); },
      once: function(){ return req(p, 'GET').then(function(v){ return snap(p, v); }); },
      on: function(ev, cb){ var last; (function tick(){ req(p, 'GET').then(function(v){ var s = JSON.stringify(v); if (s !== last) { last = s; cb(snap(p, v)); } }).catch(function(){}).then(function(){ timer = setTimeout(tick, 250); }); })(); return cb; },
      off: function(){ clearTimeout(timer); }
    };
  }
  function fire(){ var u = uid ? { uid: uid, displayName: '시험 선생님' } : null; authCbs.forEach(function(cb){ setTimeout(function(){ cb(u); }, 0); }); }
  function auth(){ return {
    onAuthStateChanged: function(cb){ authCbs.push(cb); setTimeout(function(){ cb(uid ? { uid: uid, displayName: '시험 선생님' } : null); }, 0); },
    signInWithPopup: function(){ uid = window.__STUB_LOGIN_AS || 'teacher1'; try { localStorage.setItem('stub_uid', uid); } catch (e) {} fire(); return Promise.resolve({ user: { uid: uid } }); },
    signOut: function(){ uid = null; try { localStorage.removeItem('stub_uid'); } catch (e) {} fire(); return Promise.resolve(); }
  }; }
  auth.GoogleAuthProvider = function(){};
  function database(){ return { ref: ref }; }
  database.ServerValue = { TIMESTAMP: { '.sv': 'timestamp' } };
  window.firebase = { apps: [], initializeApp: function(c){ cfg = c; this.apps.push(1); }, auth: auth, database: database };
})();
