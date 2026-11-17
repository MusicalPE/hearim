# 시험용 가짜 실시간 데이터베이스 (주소로 읽고 쓰기 + 규칙 흉내): python3 mockdb.py [포트]
# 규칙 흉내: 설문 meta 는 주인(auth=uid)만, 답은 open 일 때만, 답 지우기는 주인만. 실제 규칙은 database.rules.json
import json, sys, time, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
DB = {}
def get(path):
    cur = DB
    for k in path:
        if not isinstance(cur, dict) or k not in cur: return None
        cur = cur[k]
    return cur
def put(path, val):
    if not path: DB.clear(); DB.update(val or {}); return
    cur = DB
    for k in path[:-1]: cur = cur.setdefault(k, {})
    if val is None: cur.pop(path[-1], None)
    else: cur[path[-1]] = val
    for i in range(len(path) - 1, 0, -1):   # 빈 가지는 없앰 (실제 데이터베이스처럼)
        node = get(path[:i])
        if node == {}: put(path[:i], None)
def sv(v):
    if isinstance(v, dict):
        if v == {'.sv': 'timestamp'}: return int(time.time() * 1000)
        return {k: sv(x) for k, x in v.items()}
    if isinstance(v, list): return {str(i): sv(x) for i, x in enumerate(v) if x is not None}
    return v
def allowed(path, val, auth):
    if path[:1] == ['__reset']: return True
    if path[:1] == ['users']: return len(path) >= 2 and auth == path[1]
    if path[:1] != ['polls'] or len(path) < 3 or not re.match(r'^[a-z0-9]{6}$', path[1]): return False
    meta = get(['polls', path[1], 'meta'])
    if path[2] == 'meta':
        if not auth: return False
        if meta is None: return len(path) == 3 and isinstance(val, dict) and val.get('owner') == auth
        return meta.get('owner') == auth
    if path[2] == 'votes':
        owner = bool(auth) and meta is not None and meta.get('owner') == auth
        if len(path) == 3: return val is None and owner
        if not re.match(r'^[a-z0-9]{12,24}$', path[3]): return False
        if val is None: return owner
        if not (len(path) == 4 and meta is not None and meta.get('open') is True and isinstance(val, dict)): return False
        if 'a' in val:   # 적어서 내기: 답 1~5개, 20자까지
            a = val['a']; a = list(a.values()) if isinstance(a, dict) else a
            return isinstance(a, list) and 1 <= len(a) <= 5 and all(isinstance(x, str) and 1 <= len(x) <= 20 for x in a) and set(val) <= {'a', 'at'}
        return isinstance(val.get('c'), int) and 0 <= val['c'] <= 9 and len(str(val.get('t', ''))) <= 200
    return False
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def out(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def parts(self):
        u = urlparse(self.path); p = u.path
        if p.endswith('.json'): p = p[:-5]
        return [x for x in p.split('/') if x], (parse_qs(u.query).get('auth') or [''])[0]
    def do_OPTIONS(self):
        self.send_response(204); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Methods', 'GET,PUT,PATCH,DELETE,OPTIONS'); self.send_header('Access-Control-Allow-Headers', 'Content-Type'); self.end_headers()
    def do_GET(self):
        path, auth = self.parts()
        if path[:1] == ['users'] and (len(path) < 2 or auth != path[1]): return self.out(401, {'error': 'Permission denied'})
        if path == ['polls']: return self.out(401, {'error': 'Permission denied'})
        self.out(200, get(path))
    def write(self, val):
        path, auth = self.parts()
        if path == ['__reset']: DB.clear(); return self.out(200, {})
        if not allowed(path, val, auth): return self.out(401, {'error': 'Permission denied'})
        put(path, val); self.out(200, val)
    def do_PUT(self):
        n = int(self.headers.get('Content-Length') or 0); self.write(sv(json.loads(self.rfile.read(n) or b'null')))
    def do_DELETE(self): self.write(None)
ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8931), H).serve_forever()
