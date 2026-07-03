from flask import Flask, render_template_string, request, session, redirect, jsonify, send_file
import json, os, random, string, time, hashlib, collections, re, shutil, threading
from datetime import datetime, timezone, timedelta
try:
    import requests as _req_tg
    _TG_OK = True
except ImportError:
    _req_tg = None
    _TG_OK = False

try:
    from bs4 import BeautifulSoup as _BS4
    _BS4_OK = True
except ImportError:
    _BS4_OK = False
    _BS4 = None

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'server_key_bi_mat_2026_vinhvien')
app.permanent_session_lifetime = timedelta(days=365)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

import urllib.request as _ureq, urllib.parse

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        from flask import make_response
        resp = make_response('', 204)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        return resp

@app.route('/healthz')
def healthz():
    return jsonify({"status": "ok", "db": os.path.exists(DB_FILE)}), 200

def _keep_alive_worker():
    import time as _time; _time.sleep(60)
    while True:
        _time.sleep(14*60)
        try:
            host = os.environ.get('RENDER_EXTERNAL_URL','')
            if host: _ureq.urlopen(host.rstrip('/')+'/healthz', timeout=10)
        except: pass

def _keep_alive_worker2():
    import time as _t2; _t2.sleep(420)
    while True:
        _t2.sleep(14*60)
        try:
            host2 = os.environ.get('RENDER_EXTERNAL_URL','')
            if host2: _ureq.urlopen(host2.rstrip('/')+'/healthz', timeout=10)
        except: pass

def _keep_alive_worker3():
    import time as _t3; _t3.sleep(270)
    while True:
        _t3.sleep(14*60)
        try:
            host3 = os.environ.get('RENDER_EXTERNAL_URL','')
            if host3: _ureq.urlopen(host3.rstrip('/')+'/healthz', timeout=10)
        except: pass

threading.Thread(target=_keep_alive_worker, daemon=True).start()
threading.Thread(target=_keep_alive_worker2, daemon=True).start()
threading.Thread(target=_keep_alive_worker3, daemon=True).start()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = '/data' if os.path.isdir('/data') else BASE_DIR
DB_FILE = os.path.join(DATA_DIR, "database_keys.json")
WEB_LOG_FILE = os.path.join(DATA_DIR, "web_access.log")
os.makedirs(DATA_DIR, exist_ok=True)
VN_TZ = timezone(timedelta(hours=7))
_WEB_LOG_LOCK = threading.Lock()

def get_real_ip():
    if request.headers.get('CF-Connecting-IP'): return request.headers.get('CF-Connecting-IP')
    if request.headers.get('X-Forwarded-For'): return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def load_db():
    """Load database. Tries backup on parse error. Raises exception if all fail (e.g. DB corrupted with no backup)."""
    for path in [DB_FILE, DB_FILE + '.bak']:
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "___ADMIN_CONFIG___" not in data:
                data["___ADMIN_CONFIG___"] = {"user": "vkhanh", "pass": "1"}
            return data
        except Exception:
            continue
    if not os.path.exists(DB_FILE) and not os.path.exists(DB_FILE + '.bak'):
        # Fresh install
        return {"___ADMIN_CONFIG___": {"user": "vkhanh", "pass": "1"}}
    raise OSError("DB load failed — all copies corrupted")

def save_db(data):
    tmp = DB_FILE + '.tmp'; bak = DB_FILE + '.bak'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        if os.path.exists(DB_FILE): shutil.copy2(DB_FILE, bak)
        shutil.move(tmp, DB_FILE)
    except Exception as e:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except: pass

def format_ts(ts):
    if not ts: return '—'
    try: return datetime.fromtimestamp(float(ts), VN_TZ).strftime('%d/%m/%Y %H:%M')
    except: return '—'

def format_full_ts(ts):
    if not ts: return 'Chưa kích hoạt'
    try: return datetime.fromtimestamp(float(ts), VN_TZ).strftime('%d/%m/%Y %H:%M:%S')
    except: return '—'

def get_time_left_str(exp):
    if exp == -1: return 'Vĩnh Viễn'
    now = time.time()
    if now > exp: return 'Hết hạn'
    diff = int(exp - now)
    d = diff // 86400; h = (diff % 86400) // 3600; m = (diff % 3600) // 60
    if d > 0: return f'{d}n {h}g {m}p'
    if h > 0: return f'{h}g {m}p'
    return f'{m}p'

@app.route('/nhac.mp3')
def play_music():
    f = os.path.join(BASE_DIR, 'nhac.mp3')
    if os.path.exists(f): return send_file(f, mimetype='audio/mp3')
    return jsonify({"status":"missing"}), 404

@app.route('/nhac2.mp3')
def play_music2():
    f = os.path.join(BASE_DIR, 'nhac2.mp3')
    if os.path.exists(f): return send_file(f, mimetype='audio/mp3')
    return jsonify({"status":"missing"}), 404

@app.route('/nhac3.mp3')
def play_music3():
    f = os.path.join(BASE_DIR, 'nhac3.mp3')
    if os.path.exists(f): return send_file(f, mimetype='audio/mp3')
    return jsonify({"status":"missing"}), 404

# ── Main Route ──
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        k = request.form.get('key','').strip()
        db = load_db()
        if k in db and not k.startswith("___"):
            info = db[k]; now = time.time()
            if isinstance(info.get('used_devices',[]), list):
                new_devs = {}
                for d in info.get('used_devices',[]): new_devs[d] = info.get('expiry_time', 0)
                info['used_devices'] = new_devs; save_db(db)
            if info['status'] == 'Đã kích hoạt':
                is_full = len(info['used_devices']) >= info['max_devices']
                _np = [e for e in info['used_devices'].values() if e != -1]
                if is_full and len(_np) > 0 and all(now > e for e in _np):
                    info['status'] = "Hết hạn"; save_db(db)
            return jsonify({
                "exists": True, "key": k, "key_status": info['status'],
                "duration": f"{info['duration_val']} {info['duration_unit']}" if info['duration_unit'] != 'permanent' else "Vĩnh viễn",
                "max_devices": info['max_devices'], "used_devices": len(info['used_devices']),
                "created_at": format_ts(info.get('created_at',0)),
                "activated_time": format_ts(info.get('activated_time')) if info.get('activated_time') else "Chưa kích hoạt",
                "dev_dict": info['used_devices']
            })
        return jsonify({"exists": False, "msg": "Mã Key không tồn tại trên hệ thống máy chủ!"})
    return render_template_string(UI_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    db = load_db()
    admin_cfg = db.get("___ADMIN_CONFIG___", {"user":"vkhanh","pass":"1"})
    if request.form.get('user') == admin_cfg['user'] and request.form.get('pass') == admin_cfg['pass']:
        session.clear(); session.permanent = True
        session['is_admin'] = True; session['admin_user'] = admin_cfg['user']; session['admin_pass'] = admin_cfg['pass']
        session.modified = True
        real_ip = get_real_ip()
        if real_ip:
            saved_owners = db.get('___OWNER_IPS___', [])
            if real_ip not in saved_owners:
                saved_owners.append(real_ip); db['___OWNER_IPS___'] = saved_owners; save_db(db)
        return jsonify({"status":"success"})
    return jsonify({"status":"error","message":"Sai thông tin tài khoản hoặc mật khẩu quản trị!"})

@app.route('/api/change_admin', methods=['POST'])
def change_admin():
    db = load_db(); admin_cfg = db.get("___ADMIN_CONFIG___", {"user":"vkhanh","pass":"1"})
    if not session.get('is_admin') or session.get('admin_pass') != admin_cfg['pass']:
        return jsonify({"status":"error"}), 401
    new_u = request.form.get('u','').strip(); new_p = request.form.get('p','').strip()
    if new_u and new_p:
        db["___ADMIN_CONFIG___"] = {"user":new_u,"pass":new_p}; save_db(db)
        session['admin_user'] = new_u; session['admin_pass'] = new_p
        return jsonify({"status":"success"})
    return jsonify({"status":"error","message":"Tài khoản và mật khẩu không được để trống!"})

@app.before_request
def check_admin_changed():
    if request.method == 'OPTIONS': return
    if session.get('is_admin'):
        try:
            db = load_db()
            admin_cfg = db.get("___ADMIN_CONFIG___", None)
            # Only clear if we successfully loaded a config that explicitly doesn't match
            if admin_cfg and (session.get('admin_pass') != admin_cfg.get('pass') or session.get('admin_user') != admin_cfg.get('user')):
                session.clear()
        except Exception:
            # If DB load fails, keep session alive - don't log out admin due to temporary DB errors
            pass

@app.route('/admin', methods=['POST'])
def admin_add_key():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    db = load_db(); mode = request.form.get('mode','random')
    time_val = request.form.get('v','1').strip(); time_unit = request.form.get('u')
    max_dev = int(request.form.get('d',1))
    if mode == 'custom' and request.form.get('c_key','').strip():
        key_name = request.form.get('c_key').strip()
    else:
        p1 = "".join(random.choices(string.ascii_uppercase+string.digits, k=3))
        p2 = "".join(random.choices(string.ascii_uppercase+string.digits, k=3))
        pref_map = {"permanent":"VIP","ngày":f"{time_val}DAY","phút":f"{time_val}P","tiếng":f"{time_val}H","tháng":f"{time_val}M","năm":f"{time_val}Y"}
        key_name = f"{pref_map.get(time_unit,'KEY')}-{p1}-{p2}"
    db[key_name] = {"duration_val":int(time_val) if time_unit!="permanent" else 0,"duration_unit":time_unit,"max_devices":max_dev,"status":"Chưa kích hoạt","activated_time":None,"created_at":time.time(),"used_devices":{}}
    save_db(db)
    return jsonify({"status":"success","key":key_name})

@app.route('/api/list_keys', methods=['GET'])
def list_keys():
    if not session.get('is_admin'): return jsonify([]), 401
    db = load_db(); now = time.time(); res = []
    for k, v in db.items():
        if k.startswith("___"): continue
        if isinstance(v.get('used_devices',[]), list):
            new_devs = {}
            for d in v.get('used_devices',[]): new_devs[d] = v.get('expiry_time',0)
            v['used_devices'] = new_devs; save_db(db)
        if v['status'] == "Đã kích hoạt":
            is_full = len(v['used_devices']) >= v['max_devices']
            _np2 = [e for e in v['used_devices'].values() if e != -1]
            if is_full and len(_np2) > 0 and all(now > e for e in _np2):
                v['status'] = "Hết hạn"; save_db(db)
        dev_list = [{"device_id":did,"expiry":exp} for did, exp in v['used_devices'].items()]
        age_hours = (now - v.get('created_at',now)) / 3600
        res.append({"key":k,"status":v['status'],"han_dung":f"{v['duration_val']} {v['duration_unit']}" if v['duration_unit']!='permanent' else "Vĩnh viễn","thiet_bi":f"{len(v['used_devices'])}/{v['max_devices']}","activated_time_str":format_full_ts(v.get('activated_time')),"created_at_str":format_ts(v.get('created_at')),"creator_info":v.get('creator_info','Admin Gốc'),"devices":dev_list,"is_free":k.startswith("FREE-"),"created_at_ts":v.get('created_at',0),"age_hours":round(age_hours,1)})
    return jsonify(res)

@app.route('/delete/<key>')
def delete(key):
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    db = load_db()
    if key in db:
        del db[key]
        ip_map = db.get("___IP_KEY_MAP___",{})
        to_remove = [ip for ip, k in ip_map.items() if k == key]
        for ip in to_remove: del ip_map[ip]
        db["___IP_KEY_MAP___"] = ip_map; save_db(db)
    return jsonify({"status":"success"})

@app.route('/reset/<key>')
def reset_key(key):
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    db = load_db()
    if key in db:
        db[key]['status'] = "Chưa kích hoạt"; db[key]['activated_time'] = None; db[key]['used_devices'] = {}; save_db(db)
    return jsonify({"status":"success"})

@app.route('/admin/free_setup', methods=['POST'])
def admin_free_setup():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    db = load_db()
    db["___FREE_CONFIG___"] = {"val":request.form.get('v'),"unit":request.form.get('u'),"dev":request.form.get('d')}
    save_db(db); return jsonify({"status":"success"})

@app.route('/admin/get_free_config', methods=['GET'])
def admin_get_free_config():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    db = load_db(); cfg = db.get("___FREE_CONFIG___", {"val":"12","unit":"tiếng","dev":"1"})
    return jsonify({"status":"success","val":str(cfg.get('val','12')),"unit":str(cfg.get('unit','tiếng')),"dev":str(cfg.get('dev','1'))})

@app.route('/api/gen_free_task', methods=['POST'])
def gen_free_task():
    db = load_db(); cfg = db.get("___FREE_CONFIG___",{"val":12,"unit":"tiếng","dev":9999})
    client_ip_info = request.form.get('ip_info','Không quét được Client'); server_ip = get_real_ip()
    final_info = f"SV IP: {server_ip} | {client_ip_info}"
    ip_map = db.get("___IP_KEY_MAP___",{})
    existing_key = ip_map.get(server_ip)
    if existing_key and existing_key in db:
        existing_info = db[existing_key]; age_hours = (time.time() - existing_info.get('created_at',0)) / 3600
        if age_hours < 12 or existing_info.get('status') == 'Đã kích hoạt':
            return jsonify({"status":"success","key":existing_key,"reused":True})
    k = f"FREE-{''.join(random.choices(string.ascii_uppercase+string.digits, k=5))}"
    db[k] = {"duration_val":int(cfg['val']),"duration_unit":cfg['unit'],"max_devices":int(cfg['dev']),"status":"Chưa kích hoạt","activated_time":None,"created_at":time.time(),"used_devices":{},"creator_info":final_info,"client_ip":server_ip}
    ip_map[server_ip] = k; db["___IP_KEY_MAP___"] = ip_map; save_db(db)
    return jsonify({"status":"success","key":k,"reused":False})

@app.route('/api/regen_free_key', methods=['POST'])
def regen_free_key():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    target_ip = request.form.get('ip','').strip(); db = load_db()
    cfg = db.get("___FREE_CONFIG___",{"val":12,"unit":"tiếng","dev":9999})
    ip_map = db.get("___IP_KEY_MAP___",{})
    old_key = ip_map.get(target_ip)
    if old_key and old_key in db: del db[old_key]
    k = f"FREE-{''.join(random.choices(string.ascii_uppercase+string.digits, k=5))}"
    db[k] = {"duration_val":int(cfg['val']),"duration_unit":cfg['unit'],"max_devices":int(cfg['dev']),"status":"Chưa kích hoạt","activated_time":None,"created_at":time.time(),"used_devices":{},"creator_info":f"Tái tạo bởi Admin | IP: {target_ip}","client_ip":target_ip}
    ip_map[target_ip] = k; db["___IP_KEY_MAP___"] = ip_map; save_db(db)
    return jsonify({"status":"success","key":k})

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.get_json(silent=True) or {}
    key = (data.get('key','') or request.form.get('key','')).strip()
    hwid = (data.get('hwid','') or data.get('device_id','') or request.form.get('hwid','') or request.form.get('device_id','')).strip()
    if not key or not hwid: return jsonify({"status":"error","message":"Missing key or hwid"})
    db = load_db()
    if key not in db or key.startswith("___"): return jsonify({"status":"invalid","message":"Key does not exist"})
    info = db[key]; now = time.time()
    if isinstance(info.get('used_devices',[]), list):
        new_devs = {}
        for d in info.get('used_devices',[]): new_devs[d] = info.get('expiry_time',0)
        info['used_devices'] = new_devs
    val, unit = info['duration_val'], info['duration_unit']; sec = -1
    if unit=="phút": sec=val*60
    elif unit=="tiếng": sec=val*3600
    elif unit=="ngày": sec=val*86400
    elif unit=="tháng": sec=val*30*86400
    elif unit=="năm": sec=val*365*86400
    is_permanent = (sec==-1)
    if info['status'] == "Hết hạn":
        return jsonify({"status":"expired","message":"Key này đã hết hạn","key_status":"Hết hạn","time_left":"Hết hạn"})
    is_first = (info['status'] == "Chưa kích hoạt")
    if is_first: info['status'] = "Đã kích hoạt"; info['activated_time'] = now
    if hwid in info['used_devices']:
        dev_exp = info['used_devices'][hwid]
        if dev_exp != -1 and now > dev_exp:
            _np = [e for e in info['used_devices'].values() if e != -1]
            is_full = len(info['used_devices']) >= info['max_devices']
            if is_full and len(_np) > 0 and all(now > e for e in _np): info['status'] = "Hết hạn"
            save_db(db)
            return jsonify({"status":"expired","message":"Key đã hết hạn","expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp),"is_permanent":False})
        save_db(db)
        return jsonify({"status":"success","message":"Key hợp lệ","time_left":get_time_left_str(dev_exp),"expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp) if dev_exp!=-1 else "Vĩnh Viễn","is_permanent":(dev_exp==-1),"is_new_device":False})
    else:
        if len(info['used_devices']) >= info['max_devices']:
            save_db(db)
            return jsonify({"status":"device_limit","message":f"Đã đạt giới hạn thiết bị ({info['max_devices']} thiết bị)","max_devices":info['max_devices'],"used_devices":len(info['used_devices'])})
        dev_exp = -1 if is_permanent else (now+sec)
        info['used_devices'][hwid] = dev_exp; save_db(db)
        return jsonify({"status":"success","message":"Thiết bị đã được đăng ký","time_left":get_time_left_str(dev_exp),"expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp) if dev_exp!=-1 else "Vĩnh Viễn","is_permanent":is_permanent,"is_new_device":True,"activated_now":is_first})

@app.route('/api/check_expiry', methods=['GET','POST','OPTIONS'])
def api_check_expiry():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"}), 200
    data = request.get_json(silent=True) or {}
    key = (data.get('key','') or request.values.get('key','')).strip()
    hwid = (data.get('hwid','') or data.get('device_id','') or request.values.get('hwid','') or request.values.get('device_id','')).strip()
    if not key: return jsonify({"status":"error","message":"Thiếu tham số 'key'"}), 400
    if not hwid: return jsonify({"status":"error","message":"Thiếu tham số 'hwid'"}), 400
    db = load_db()
    if key not in db or key.startswith("___"): return jsonify({"status":"invalid","message":"Key không tồn tại"})
    info = db[key]; now = time.time()
    devices = info.get('used_devices',{})
    if isinstance(devices, list): devices = {d: info.get('expiry_time',0) for d in devices}
    key_status = info.get('status','Chưa kích hoạt')
    if key_status == "Hết hạn": return jsonify({"status":"expired","message":"Key đã bị đánh dấu hết hạn"})
    if key_status == "Chưa kích hoạt": return jsonify({"status":"not_activated","message":"Key chưa được kích hoạt"})
    if hwid not in devices: return jsonify({"status":"device_not_found","message":f"Device chưa đăng ký","registered_count":len(devices),"max_devices":info.get('max_devices',1)})
    dev_exp = devices[hwid]
    if dev_exp == -1: return jsonify({"status":"valid","time_left":"∞","expiry_timestamp":-1,"expiry_str":"Vĩnh Viễn","is_permanent":True})
    if now > dev_exp: return jsonify({"status":"expired","expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp),"is_permanent":False})
    return jsonify({"status":"valid","time_left":get_time_left_str(dev_exp),"expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp),"is_permanent":False})

@app.route('/api/check-device', methods=['GET','POST','OPTIONS'])
def api_check_device():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"}), 200
    data = request.get_json(silent=True) or {}
    device_id = (data.get('device_id','') or data.get('deviceId','') or request.form.get('device_id','') or request.args.get('device_id','')).strip()
    key = (data.get('key','') or request.form.get('key','') or request.args.get('key','')).strip()
    note = (data.get('note','') or request.form.get('note','') or request.args.get('note','')).strip()
    caller_ip = get_real_ip()
    if not check_rate_limit(caller_ip, max_req=10, window=30): return jsonify({"status":"error","message":"Quá nhiều yêu cầu"}), 429
    if not device_id: return jsonify({"status":"error","message":"Missing device_id"}), 400
    db = load_db(); now = time.time()
    approved = db.get("___APPROVED_DEVICES___",{})
    if device_id in approved:
        dinfo = approved[device_id]; exp = dinfo.get('expiry',-1)
        if exp == 0: exp = -1
        if exp != -1 and now > exp:
            tg_notify(f"📱 CHECK-DEVICE HẾT HẠN\nDevice: {device_id}\nIP: {caller_ip}")
            return jsonify({"status":"expired","message":"Device approval expired","expiry_timestamp":exp,"expiry_str":format_ts(exp),"is_permanent":False,"time_left":"Hết hạn"})
        tg_notify(f"✅ CHECK-DEVICE HỢP LỆ\nDevice: {device_id}\nIP: {caller_ip}")
        return jsonify({"status":"approved","expiry":exp,"expiry_timestamp":exp,"is_permanent":(exp==-1),"time_left":get_time_left_str(exp),"expiry_str":format_ts(exp) if exp!=-1 else "Vĩnh Viễn"})
    found_key = None; found_exp = None
    if key and key in db and not key.startswith("___"):
        kinfo = db[key]
        if device_id in kinfo.get('used_devices',{}):
            found_key = key; found_exp = kinfo['used_devices'][device_id]
    if not found_key:
        for k, v in db.items():
            if k.startswith("___") or not isinstance(v, dict): continue
            if device_id in v.get('used_devices',{}):
                found_key = k; found_exp = v['used_devices'][device_id]; break
    if found_key:
        if found_exp != -1 and now > found_exp:
            return jsonify({"status":"expired","message":"Key on this device has expired","key":found_key,"expiry_timestamp":found_exp,"expiry_str":format_ts(found_exp),"is_permanent":False,"time_left":"Hết hạn"})
        return jsonify({"status":"approved","key":found_key,"expiry_timestamp":found_exp,"is_permanent":(found_exp==-1),"time_left":get_time_left_str(found_exp),"expiry_str":format_ts(found_exp) if found_exp!=-1 else "Vĩnh Viễn"})
    return jsonify({"status":"not_found","message":"Device not found in system"})

@app.route('/check-ip-key')
def check_ip_key_page():
    return render_template_string(CHECK_IP_KEY_HTML)

@app.route('/api/get_key_ip_info', methods=['POST'])
def get_key_ip_info():
    k = request.form.get('key','').strip(); db = load_db()
    if not k or k not in db or k.startswith("___"):
        return jsonify({"exists":False,"msg":"Key không tồn tại!"})
    info = db[k]; now = time.time()
    devices = [{"device_id":did,"expiry":exp,"expiry_str":format_ts(exp) if (isinstance(exp,(int,float)) and exp!=-1) else "Vĩnh viễn"} for did, exp in info.get('used_devices',{}).items()]
    return jsonify({"exists":True,"key":k,"status":info.get('status','—'),"client_ip":info.get('client_ip',''),"creator_info":info.get('creator_info','Không có thông tin'),"activated_time":format_ts(info.get('activated_time')) if info.get('activated_time') else "Chưa kích hoạt","created_at":format_ts(info.get('created_at',0)),"devices":devices,"duration":f"{info['duration_val']} {info['duration_unit']}" if info.get('duration_unit')!='permanent' else "Vĩnh viễn"})

@app.route('/api/check_free_key_status', methods=['POST'])
def check_free_key_status():
    k = request.form.get('key',''); db = load_db()
    if k in db:
        info = db[k]; now = time.time()
        if info['status'] == 'Đã kích hoạt':
            _np3 = [e for e in info['used_devices'].values() if e != -1]
            if len(_np3) > 0 and all(now > e for e in _np3): return jsonify({"valid":False})
        return jsonify({"valid":True})
    return jsonify({"valid":False})

@app.route('/nhan-key-free')
def nhan_key_free_page(): return render_template_string(FREE_KEY_HTML)

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/api/check_key', methods=['GET','POST'])
def api_check_key():
    data = request.get_json(silent=True) or {}
    k = (data.get('key','') or request.values.get('key','')).strip()
    device_id = (data.get('hwid','') or data.get('device_id','') or request.values.get('device_id','') or request.values.get('hwid','')).strip()
    if not k or not device_id: return jsonify({"status":"error","message":"Thiếu key hoặc device_id"})
    db = load_db()
    if k not in db or k.startswith("___"): return jsonify({"status":"invalid","message":"Key không tồn tại"})
    info = db[k]; now = time.time()
    if isinstance(info.get('used_devices',[]), list):
        new_devs = {}
        for d in info.get('used_devices',[]): new_devs[d] = info.get('expiry_time',0)
        info['used_devices'] = new_devs
    val, unit = info['duration_val'], info['duration_unit']; sec = -1
    if unit=="phút": sec=val*60
    elif unit=="tiếng": sec=val*3600
    elif unit=="ngày": sec=val*86400
    elif unit=="tháng": sec=val*30*86400
    elif unit=="năm": sec=val*365*86400
    is_permanent = (sec==-1)
    if info['status'] == "Hết hạn": return jsonify({"status":"expired","message":"Key đã hết hạn"})
    is_first = (info['status'] == "Chưa kích hoạt")
    if is_first: info['status'] = "Đã kích hoạt"; info['activated_time'] = now
    if device_id in info['used_devices']:
        dev_exp = info['used_devices'][device_id]
        if dev_exp != -1 and now > dev_exp:
            _np = [e for e in info['used_devices'].values() if e != -1]
            is_full = len(info['used_devices']) >= info['max_devices']
            if is_full and len(_np) > 0 and all(now > e for e in _np): info['status'] = "Hết hạn"
            save_db(db)
            return jsonify({"status":"expired","message":"Key đã hết hạn","expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp)})
        save_db(db)
        return jsonify({"status":"success","time_left":get_time_left_str(dev_exp),"expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp) if dev_exp!=-1 else "Vĩnh Viễn","is_permanent":(dev_exp==-1),"is_new_device":False})
    else:
        if len(info['used_devices']) < info['max_devices']:
            dev_exp = -1 if is_permanent else (now+sec)
            info['used_devices'][device_id] = dev_exp; save_db(db)
            return jsonify({"status":"success","time_left":get_time_left_str(dev_exp),"expiry_timestamp":dev_exp,"expiry_str":format_ts(dev_exp) if dev_exp!=-1 else "Vĩnh Viễn","is_permanent":is_permanent,"is_new_device":True})
        save_db(db); return jsonify({"status":"device_limit","message":f"Đã đạt giới hạn thiết bị ({info['max_devices']})"})

@app.route('/api/submit_device_request', methods=['POST','OPTIONS'])
def submit_device_request():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"}), 200
    data = request.get_json(silent=True) or {}
    device_id = (data.get('device_id','') or request.form.get('device_id','')).strip()
    val = (data.get('val','') or request.form.get('val','1')).strip()
    unit = (data.get('unit','') or request.form.get('unit','ngày')).strip()
    note = (data.get('note','') or request.form.get('note','')).strip()
    if not device_id: return jsonify({"status":"error","msg":"Thiếu Device ID!"})
    db = load_db(); requests_map = db.get("___DEVICE_REQUESTS___",{})
    for rid, rinfo in requests_map.items():
        if rinfo.get('device_id') == device_id and rinfo.get('status') == 'pending':
            return jsonify({"status":"exists","msg":"Device ID đang chờ duyệt rồi!"})
    approved = db.get("___APPROVED_DEVICES___",{})
    if device_id in approved:
        exp = approved[device_id].get('expiry',0)
        if exp == -1 or time.time() < exp:
            return jsonify({"status":"already_approved","msg":"Device ID đã được duyệt và còn hạn!"})
    req_id = str(int(time.time()*1000))+"-"+"".join(random.choices(string.ascii_uppercase+string.digits, k=4))
    requests_map[req_id] = {"device_id":device_id,"val":val,"unit":unit,"note":note,"status":"pending","submitted_at":time.time(),"ip":get_real_ip()}
    db["___DEVICE_REQUESTS___"] = requests_map; save_db(db)
    return jsonify({"status":"success","req_id":req_id})

@app.route('/api/list_device_requests', methods=['GET','OPTIONS'])
def list_device_requests():
    if request.method == 'OPTIONS': return jsonify([]), 200
    if not session.get('is_admin'): return jsonify([]), 401
    db = load_db(); requests_map = db.get("___DEVICE_REQUESTS___",{})
    result = [{"req_id":rid,"device_id":rinfo.get('device_id',''),"val":rinfo.get('val','1'),"unit":rinfo.get('unit','ngày'),"note":rinfo.get('note',''),"submitted_at_str":format_ts(rinfo.get('submitted_at',0)),"submitted_at_ts":rinfo.get('submitted_at',0),"ip":rinfo.get('ip','—')} for rid, rinfo in requests_map.items() if rinfo.get('status')=='pending']
    result.sort(key=lambda x: x['submitted_at_ts'], reverse=True)
    return jsonify(result)

@app.route('/api/approve_device_request', methods=['POST','OPTIONS'])
def approve_device_request():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"}), 200
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    req_id = request.form.get('req_id','').strip(); val = request.form.get('val','').strip(); unit = request.form.get('unit','').strip()
    db = load_db(); requests_map = db.get("___DEVICE_REQUESTS___",{})
    if req_id not in requests_map: return jsonify({"status":"error","msg":"Yêu cầu không tồn tại!"})
    rinfo = requests_map[req_id]; device_id = rinfo['device_id']; now = time.time()
    val_int = int(val) if val and val.isdigit() else int(rinfo.get('val',1))
    u = unit if unit else rinfo.get('unit','ngày'); sec = -1
    if u=="phút": sec=val_int*60
    elif u=="tiếng": sec=val_int*3600
    elif u=="ngày": sec=val_int*86400
    elif u=="tháng": sec=val_int*30*86400
    elif u=="năm": sec=val_int*365*86400
    expiry = -1 if sec==-1 else (now+sec)
    approved = db.get("___APPROVED_DEVICES___",{})
    approved[device_id] = {"expiry":expiry,"approved_at":now,"val":val_int,"unit":u,"note":rinfo.get('note',''),"ip":rinfo.get('ip','')}
    db["___APPROVED_DEVICES___"] = approved; requests_map[req_id]['status'] = 'approved'; db["___DEVICE_REQUESTS___"] = requests_map; save_db(db)
    return jsonify({"status":"success"})

@app.route('/api/reject_device_request', methods=['POST'])
def reject_device_request():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    req_id = request.form.get('req_id','').strip(); db = load_db()
    requests_map = db.get("___DEVICE_REQUESTS___",{})
    if req_id in requests_map: requests_map[req_id]['status'] = 'rejected'; db["___DEVICE_REQUESTS___"] = requests_map; save_db(db)
    return jsonify({"status":"success"})

@app.route('/api/list_approved_devices', methods=['GET'])
def list_approved_devices():
    if not session.get('is_admin'): return jsonify([]), 401
    db = load_db(); approved = db.get("___APPROVED_DEVICES___",{}); now = time.time()
    result = []
    for did, dinfo in approved.items():
        exp = dinfo.get('expiry',0)
        result.append({"device_id":did,"expiry":exp,"expiry_str":format_ts(exp) if exp!=-1 else "Vĩnh viễn","time_left":"Vĩnh viễn" if exp==-1 else get_time_left_str(exp),"is_expired":(exp!=-1 and now>exp),"approved_at":format_ts(dinfo.get('approved_at',0)),"val":dinfo.get('val',''),"unit":dinfo.get('unit',''),"note":dinfo.get('note',''),"ip":dinfo.get('ip','—')})
    return jsonify(result)

@app.route('/api/delete_approved_device', methods=['POST'])
def delete_approved_device():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    device_id = request.form.get('device_id','').strip(); db = load_db()
    approved = db.get("___APPROVED_DEVICES___",{})
    if device_id in approved: del approved[device_id]; db["___APPROVED_DEVICES___"] = approved; save_db(db)
    return jsonify({"status":"success"})

@app.route('/api/extend_approved_device', methods=['POST'])
def extend_approved_device():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    device_id = request.form.get('device_id','').strip(); val = request.form.get('val','').strip(); unit = request.form.get('unit','').strip()
    db = load_db(); approved = db.get("___APPROVED_DEVICES___",{})
    if device_id not in approved: return jsonify({"status":"error","msg":"Device ID không tồn tại!"})
    dinfo = approved[device_id]; now = time.time(); val_int = int(val) if val and val.isdigit() else 1; sec = 0
    if unit=="phút": sec=val_int*60
    elif unit=="tiếng": sec=val_int*3600
    elif unit=="ngày": sec=val_int*86400
    elif unit=="tháng": sec=val_int*30*86400
    elif unit=="năm": sec=val_int*365*86400
    cur_exp = dinfo.get('expiry',now)
    new_exp = -1 if cur_exp==-1 else (max(cur_exp,now)+sec)
    dinfo['expiry'] = new_exp; dinfo['val'] = val_int; dinfo['unit'] = unit
    approved[device_id] = dinfo; db["___APPROVED_DEVICES___"] = approved; save_db(db)
    return jsonify({"status":"success"})

@app.route('/api/check_device_approval', methods=['POST','GET','OPTIONS'])
def check_device_approval():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"}), 200
    data = request.get_json(silent=True) or {}
    device_id = (data.get('device_id','') or request.form.get('device_id','') or request.args.get('device_id','')).strip()
    if not device_id: return jsonify({"status":"error","msg":"Thiếu Device ID"})
    db = load_db(); approved = db.get("___APPROVED_DEVICES___",{})
    if device_id not in approved: return jsonify({"status":"not_found","msg":"Device ID chưa được duyệt"})
    dinfo = approved[device_id]; exp = dinfo.get('expiry',0); now = time.time()
    if exp != -1 and now > exp: return jsonify({"status":"expired","msg":"Device ID đã hết hạn","expiry_timestamp":exp,"expiry_str":format_ts(exp),"is_permanent":False,"time_left":"Hết hạn"})
    return jsonify({"status":"approved","expiry":exp,"expiry_timestamp":exp,"is_permanent":(exp==-1),"time_left":get_time_left_str(exp),"expiry_str":format_ts(exp) if exp!=-1 else "Vĩnh viễn"})

@app.route('/api/direct_activate_device', methods=['POST'])
def direct_activate_device():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    device_id = request.form.get('device_id','').strip(); expiry_date = request.form.get('expiry_date','').strip()
    if not device_id: return jsonify({"status":"error","msg":"Thiếu Device ID"})
    db = load_db(); approved = db.get("___APPROVED_DEVICES___",{}); now = time.time(); expiry = -1
    if expiry_date:
        try: expiry = datetime.strptime(expiry_date,'%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp()
        except: expiry = -1
    approved[device_id] = {"expiry":expiry,"approved_at":now,"val":0,"unit":"permanent" if expiry==-1 else "ngày","note":"Kích hoạt trực tiếp bởi Admin","ip":get_real_ip()}
    db["___APPROVED_DEVICES___"] = approved; save_db(db)
    return jsonify({"status":"success"})

@app.route('/dang-ky-thiet-bi')
def device_registration_page():
    return render_template_string(DEVICE_REG_HTML)

@app.route('/api/add_device_id', methods=['POST'])
def add_device_id():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    device_id = request.form.get('device_id','').strip(); val = request.form.get('val','1').strip(); unit = request.form.get('unit','ngày').strip()
    if not device_id: return jsonify({"status":"error","msg":"Vui lòng nhập Device ID!"})
    db = load_db(); approved = db.get("___APPROVED_DEVICES___",{}); now = time.time()
    val_int = int(val) if val and val.isdigit() else 1; sec = -1
    if unit=="phút": sec=val_int*60
    elif unit=="tiếng": sec=val_int*3600
    elif unit=="ngày": sec=val_int*86400
    elif unit=="tháng": sec=val_int*30*86400
    elif unit=="năm": sec=val_int*365*86400
    expiry = -1 if sec==-1 else (now+sec)
    approved[device_id] = {"expiry":expiry,"approved_at":now,"val":val_int,"unit":unit,"note":"Thêm ID trực tiếp","ip":get_real_ip()}
    db["___APPROVED_DEVICES___"] = approved; save_db(db)
    return jsonify({"status":"success"})

# ── Rate Limiter ──
LINK4M_API_KEY = os.environ.get('LINK4M_API_KEY', '69cb3ea598c5fa4c2c4c414d')
_RATE_LIMITER = {}; _RATE_LOCK = threading.Lock()

def check_rate_limit(ip, max_req=20, window=60):
    now = time.time()
    with _RATE_LOCK:
        times = _RATE_LIMITER.get(ip,[])
        times = [t for t in times if now-t < window]
        if len(times) >= max_req: _RATE_LIMITER[ip] = times; return False
        times.append(now); _RATE_LIMITER[ip] = times; return True

def shorten_with_link4m(long_url):
    try:
        for encoded_url in [urllib.parse.quote(long_url, safe=''), long_url]:
            api_url = f"https://link4m.co/api-shorten/v2?api={LINK4M_API_KEY}&url={encoded_url}"
            try:
                req = _ureq.Request(api_url, headers={'User-Agent':'Mozilla/5.0'})
                resp = _ureq.urlopen(req, timeout=15); raw = resp.read().decode('utf-8', errors='replace')
                data = json.loads(raw)
                if data.get('status') == 'success':
                    su = data.get('shortenedUrl','') or data.get('shorten_url','')
                    if su and su.startswith('http'): return su, None
                err_msg = data.get('message') or data.get('error') or str(data)
                return '', f"Link4m API lỗi: {err_msg}"
            except: continue
        return '', "Không kết nối được Link4m API"
    except Exception as e:
        return '', f"Lỗi hệ thống: {str(e)}"

def check_vpn_or_proxy(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,proxy,hosting"
        resp = _ureq.urlopen(url, timeout=5); data = json.loads(resp.read().decode())
        if data.get('status') == 'success': return bool(data.get('proxy') or data.get('hosting'))
    except: pass
    return False

@app.route('/api/getkey', methods=['GET','POST','OPTIONS'])
def api_getkey():
    if request.method == 'OPTIONS': return jsonify({"status":"ok"}), 200
    ip = get_real_ip()
    if not check_rate_limit(ip, max_req=5, window=30):
        return jsonify({"status":"error","message":"Quá nhiều yêu cầu. Thử lại sau 30 giây!"}), 429
    db = load_db(); now = time.time()
    ip_free_history = db.get("___FREE_IP_HISTORY___",{})
    ip_records = [t for t in ip_free_history.get(ip,[]) if now-t < 86400]
    if len(ip_records) >= 3:
        return jsonify({"status":"error","message":f"IP {ip} đã lấy đủ 3 key hôm nay. Thử lại sau 24 giờ!"}), 429
    token = ''.join(random.choices(string.ascii_uppercase+string.digits, k=20))
    host = os.environ.get('RENDER_EXTERNAL_URL', request.host_url.rstrip('/'))
    dest_url = f"{host}/nhan-key-free?token={token}"
    short_url, err = shorten_with_link4m(dest_url)
    if not short_url: return jsonify({"status":"error","message":f"Không tạo được link Link4m. {err}"}), 503
    tokens = db.get("___GETKEY_TOKENS___",{}); tokens = {k: v for k, v in tokens.items() if now-v.get('created_at',0) < 3600}
    tokens[token] = {"ip":ip,"created_at":now,"status":"pending","is_admin":False}
    db["___GETKEY_TOKENS___"] = tokens
    stats = db.get("___FREE_KEY_STATS___",{"total_bypasses":0}); stats["total_bypasses"] = stats.get("total_bypasses",0)+1
    db["___FREE_KEY_STATS___"] = stats; save_db(db)
    tg_notify(f"🔗 LINK4M MỚI\n📍 IP: {ip}\n🌐 Link: {short_url}")
    return jsonify({"status":"success","link":short_url,"token":token})

@app.route('/api/getkey_public_config', methods=['GET'])
def getkey_public_config():
    db = load_db()
    cfg = db.get("___FREE_CONFIG___", {"val":"12","unit":"tiếng","dev":"1"})
    return jsonify({"val":str(cfg.get('val','12')),"unit":str(cfg.get('unit','tiếng')),"dev":str(cfg.get('dev','1'))})

@app.route('/admin/gen_key_link', methods=['POST'])
def admin_gen_key_link():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    ip = get_real_ip(); db = load_db(); now = time.time()
    token = ''.join(random.choices(string.ascii_uppercase+string.digits, k=20))
    host = os.environ.get('RENDER_EXTERNAL_URL', request.host_url.rstrip('/'))
    dest_url = f"{host}/nhan-key-free?token={token}"
    short_url, err = shorten_with_link4m(dest_url)
    if not short_url: return jsonify({"status":"error","message":f"Không tạo được link. {err}"}), 503
    tokens = db.get("___GETKEY_TOKENS___",{}); tokens = {k: v for k, v in tokens.items() if now-v.get('created_at',0) < 3600}
    tokens[token] = {"ip":ip,"created_at":now,"status":"pending","is_admin":True}
    db["___GETKEY_TOKENS___"] = tokens
    stats = db.get("___FREE_KEY_STATS___",{"total_bypasses":0}); stats["total_bypasses"] = stats.get("total_bypasses",0)+1
    db["___FREE_KEY_STATS___"] = stats; save_db(db)
    tg_notify(f"🔗 LINK4M MỚI (Admin Panel)\n📍 Admin IP: {ip}\n🌐 Link: {short_url}")
    return jsonify({"status":"success","link":short_url,"token":token})

@app.route('/api/confirm_bypass', methods=['POST'])
def confirm_bypass():
    token = request.form.get('token','').strip(); client_ip_info = request.form.get('ip_info','').strip()
    server_ip = get_real_ip()
    if not check_rate_limit(server_ip, max_req=8, window=60):
        return jsonify({"status":"error","message":"Quá nhiều yêu cầu. Thử lại sau 1 phút!"})
    if not token: return jsonify({"status":"error","message":"Token không hợp lệ!"})
    db = load_db(); now = time.time(); tokens = db.get("___GETKEY_TOKENS___",{})
    if token not in tokens: return jsonify({"status":"error","message":"Link đã hết hạn hoặc không hợp lệ!"})
    token_info = tokens[token]
    if now - token_info.get('created_at',0) > 3600: return jsonify({"status":"error","message":"Link đã hết hạn (quá 1 giờ)!"})
    if token_info.get('status') == 'used':
        existing_key = token_info.get('key','')
        if existing_key and existing_key in db: return jsonify({"status":"success","key":existing_key,"reused":True,"msg":"Bạn đã nhận key này rồi!"})
        return jsonify({"status":"error","message":"Link này đã được sử dụng! Vui lòng lấy link mới."})
    is_admin_token = token_info.get('is_admin',False)
    if not is_admin_token:
        elapsed = now - token_info.get('created_at',now)
        if elapsed < 20:
            tg_notify(f"🚨 BYPASS PHÁT HIỆN!\n📍 IP: {server_ip}\n⏱ Elapsed: {elapsed:.1f}s")
            return jsonify({"status":"error","message":"⚠️ Phát hiện hành vi bypass link! Bạn phải thực sự vượt link rút gọn."})
        ip_free_history = db.get("___FREE_IP_HISTORY___",{})
        ip_records = [t for t in ip_free_history.get(server_ip,[]) if now-t < 86400]
        if len(ip_records) >= 3: return jsonify({"status":"error","message":"IP này đã đạt giới hạn 3 key/ngày. Thử lại sau 24 giờ!"})
        if check_vpn_or_proxy(server_ip): return jsonify({"status":"error","message":"Phát hiện VPN hoặc Proxy! Vui lòng tắt VPN và thử lại."})
    cfg = db.get("___FREE_CONFIG___",{"val":12,"unit":"tiếng","dev":9999})
    key_name = f"FREE-{''.join(random.choices(string.ascii_uppercase+string.digits, k=12))}"
    final_info = f"SV IP: {server_ip} | Token: {token[:8]}... | {client_ip_info}"
    db[key_name] = {"duration_val":int(cfg.get('val',12)),"duration_unit":cfg.get('unit','tiếng'),"max_devices":int(cfg.get('dev',9999)),"status":"Chưa kích hoạt","activated_time":None,"created_at":now,"used_devices":{},"creator_info":final_info,"client_ip":server_ip}
    tokens[token]['status'] = 'used'; tokens[token]['key'] = key_name; db["___GETKEY_TOKENS___"] = tokens
    if not is_admin_token:
        ip_free_history = db.get("___FREE_IP_HISTORY___",{})
        ip_records = [t for t in ip_free_history.get(server_ip,[]) if now-t < 86400]
        ip_records.append(now); ip_free_history[server_ip] = ip_records; db["___FREE_IP_HISTORY___"] = ip_free_history
    ip_map = db.get("___IP_KEY_MAP___",{}); ip_map[server_ip] = key_name; db["___IP_KEY_MAP___"] = ip_map
    save_db(db)
    tg_notify(f"🎉 KEY FREE MỚI CẤP!\n🔑 Key: {key_name}\n📍 IP: {server_ip}\n⏰ {cfg.get('val',12)} {cfg.get('unit','tiếng')}")
    return jsonify({"status":"success","key":key_name,"reused":False,"han_dung":str(cfg.get('val',12)),"thiet_bi":str(cfg.get('dev',1))})

@app.route('/api/key_stats', methods=['GET'])
def api_key_stats():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    db = load_db(); now = time.time(); total = activated = expired = not_activated = free_total = 0
    for k, v in db.items():
        if k.startswith("___") or not isinstance(v,dict): continue
        total += 1
        if k.startswith("FREE-"): free_total += 1
        st = v.get('status','')
        if st == "Đã kích hoạt":
            _np = [e for e in v.get('used_devices',{}).values() if e != -1]
            is_full = len(v.get('used_devices',{})) >= v.get('max_devices',1)
            expired += 1 if (is_full and len(_np) > 0 and all(now > e for e in _np)) else 0
            if not (is_full and len(_np) > 0 and all(now > e for e in _np)): activated += 1
        elif st == "Hết hạn": expired += 1
        else: not_activated += 1
    stats = db.get("___FREE_KEY_STATS___",{"total_bypasses":0})
    return jsonify({"total":total,"activated":activated,"expired":expired,"not_activated":not_activated,"free_total":free_total,"total_bypasses":stats.get("total_bypasses",0)})

@app.route('/api/web_logs', methods=['GET'])
def api_web_logs():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    try:
        limit = int(request.args.get('limit', 200))
        if not os.path.exists(WEB_LOG_FILE):
            return jsonify({"lines":[],"total":0})
        with open(WEB_LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        lines = [l.rstrip('\n') for l in all_lines[-limit:]]
        lines.reverse()
        return jsonify({"lines":lines,"total":len(all_lines)})
    except Exception as e:
        return jsonify({"lines":[],"total":0,"error":str(e)})

@app.route('/api/clear_web_logs', methods=['POST'])
def api_clear_web_logs():
    if not session.get('is_admin'): return jsonify({"status":"error"}), 401
    try:
        with _WEB_LOG_LOCK:
            with open(WEB_LOG_FILE,'w', encoding='utf-8') as f: f.write('')
        return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","msg":str(e)})

# ── SoundCloud Search (improved) ──
_SC_CLIENT_ID_CACHE = [None, 0]
_SC_CACHE_LOCK = threading.Lock()

def _get_sc_client_id():
    """Lấy client_id từ SoundCloud JS assets."""
    with _SC_CACHE_LOCK:
        if _SC_CLIENT_ID_CACHE[0] and time.time() - _SC_CLIENT_ID_CACHE[1] < 3600:
            return _SC_CLIENT_ID_CACHE[0]
    if not _TG_OK or _req_tg is None:
        return None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        resp = _req_tg.get('https://soundcloud.com', headers=headers, timeout=12)
        # Find JS asset URLs
        urls = re.findall(r'https://a-v2\.sndcdn\.com/assets/[^"\'>\s]+\.js', resp.text)
        if not urls:
            urls = re.findall(r'src="(https://[^"]*\.js)"', resp.text)
        # Try last few JS files to find client_id
        for url in reversed(urls[-5:]):
            try:
                r2 = _req_tg.get(url, headers=headers, timeout=10)
                # Multiple patterns to find client_id
                patterns = [
                    r'client_id\s*:\s*"([a-zA-Z0-9]{32,})"',
                    r'"client_id","([a-zA-Z0-9]{32,})"',
                    r'client_id=([a-zA-Z0-9]{32,})',
                    r'&client_id=([a-zA-Z0-9]{32,})',
                    r'client_id%22%3A%22([a-zA-Z0-9]{32,})',
                ]
                for pat in patterns:
                    m = re.search(pat, r2.text)
                    if m:
                        cid = m.group(1)
                        with _SC_CACHE_LOCK:
                            _SC_CLIENT_ID_CACHE[0] = cid
                            _SC_CLIENT_ID_CACHE[1] = time.time()
                        return cid
            except Exception:
                continue
    except Exception:
        pass
    return None

def _sc_search(query, limit=10):
    """Tìm kiếm nhạc trên SoundCloud qua API v2."""
    if not _TG_OK or _req_tg is None:
        return []
    try:
        client_id = _get_sc_client_id()
        if client_id:
            # Try API v2 search directly
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Origin': 'https://soundcloud.com',
                'Referer': 'https://soundcloud.com/',
            }
            api_url = f"https://api-v2.soundcloud.com/search/tracks?q={urllib.parse.quote(query)}&client_id={client_id}&limit={limit}&offset=0&linked_partitioning=1"
            resp = _req_tg.get(api_url, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get('collection', [])[:limit]:
                    title = item.get('title', '')
                    permalink = item.get('permalink_url', '')
                    cover = item.get('artwork_url', '') or item.get('user', {}).get('avatar_url', '')
                    if cover:
                        cover = cover.replace('-large', '-t300x300').replace('large', 't300x300')
                    if title and permalink:
                        results.append({
                            "title": title,
                            "url": permalink,
                            "cover": cover,
                            "user": item.get('user', {}).get('username', ''),
                            "duration": item.get('duration', 0)
                        })
                if results:
                    return results
    except Exception:
        pass

    # Fallback: scrape search page with improved parsing
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        }
        q_enc = urllib.parse.quote(query)
        url = f"https://soundcloud.com/search?q={q_enc}"
        resp = _req_tg.get(url, headers=headers, timeout=15)
        results = []

        # Try hydration JSON parsing
        m = re.search(r'window\.__sc_hydration\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
        if m:
            try:
                hydration = json.loads(m.group(1))
                for item in hydration:
                    d = item.get('data', {})
                    if isinstance(d, dict) and d.get('kind') == 'track':
                        title = d.get('title', '')
                        permalink = d.get('permalink_url', '')
                        cover = d.get('artwork_url', '') or d.get('user', {}).get('avatar_url', '')
                        if cover:
                            cover = cover.replace('large', 't300x300')
                        if title and permalink:
                            results.append({
                                "title": title,
                                "url": permalink,
                                "cover": cover,
                                "user": d.get('user', {}).get('username', ''),
                                "duration": d.get('duration', 0)
                            })
                    elif isinstance(d, list):
                        for track in d:
                            if isinstance(track, dict) and track.get('kind') == 'track':
                                title = track.get('title', '')
                                permalink = track.get('permalink_url', '')
                                cover = track.get('artwork_url', '') or track.get('user', {}).get('avatar_url', '')
                                if cover:
                                    cover = cover.replace('large', 't300x300')
                                if title and permalink:
                                    results.append({
                                        "title": title,
                                        "url": permalink,
                                        "cover": cover,
                                        "user": track.get('user', {}).get('username', ''),
                                        "duration": track.get('duration', 0)
                                    })
                            if len(results) >= limit:
                                break
                    if len(results) >= limit:
                        break
            except Exception:
                pass

        # BS4 fallback
        if not results and _BS4_OK and _BS4:
            soup = _BS4(resp.text, 'html.parser')
            items = soup.select('li.searchList__item')
            for item in items[:limit]:
                try:
                    title_el = item.select_one('.soundTitle__title') or item.select_one('a.sc-link-primary')
                    href_el = item.select_one('a.soundTitle__title') or item.select_one('a[href*="/"]')
                    img_el = item.select_one('img.image__full') or item.select_one('img[src]')
                    if not title_el or not href_el: continue
                    title = title_el.get_text(strip=True)
                    href = href_el.get('href','')
                    if not href.startswith('http'): href = 'https://soundcloud.com' + href
                    cover = ''
                    if img_el:
                        src = img_el.get('src','') or img_el.get('data-src','')
                        if src and 'data:' not in src:
                            cover = src.replace('large', 't300x300')
                    results.append({"title":title,"url":href,"cover":cover,"user":"","duration":0})
                except Exception:
                    continue

        return results[:limit]
    except Exception:
        return []

def _sc_get_stream_url(track_url):
    """Lấy stream URL từ SoundCloud track."""
    if not _TG_OK or _req_tg is None:
        return None
    try:
        client_id = _get_sc_client_id()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        if client_id:
            # Try resolve API
            resolve_url = f'https://api-v2.soundcloud.com/resolve?url={urllib.parse.quote(track_url)}&client_id={client_id}'
            try:
                resp = _req_tg.get(resolve_url, headers=headers, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    # Get progressive stream
                    for transcode in data.get('media', {}).get('transcodings', []):
                        fmt = transcode.get('format', {})
                        if fmt.get('protocol') == 'progressive':
                            stream_resp = _req_tg.get(
                                f"{transcode['url']}?client_id={client_id}",
                                headers=headers, timeout=10
                            )
                            url = stream_resp.json().get('url')
                            if url: return url
                    # Try HLS if progressive not found
                    for transcode in data.get('media', {}).get('transcodings', []):
                        fmt = transcode.get('format', {})
                        if fmt.get('protocol') == 'hls':
                            stream_resp = _req_tg.get(
                                f"{transcode['url']}?client_id={client_id}",
                                headers=headers, timeout=10
                            )
                            url = stream_resp.json().get('url')
                            if url: return url
            except Exception:
                pass

        # Fallback: scrape the track page
        page_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        resp = _req_tg.get(track_url, headers=page_headers, timeout=12)

        # Try stream URL from page
        m = re.search(r'"stream_url"\s*:\s*"([^"]+)"', resp.text)
        if not m: m = re.search(r'"streamUrl"\s*:\s*"([^"]+)"', resp.text)
        if m:
            raw_url = m.group(1)
            if client_id:
                sep = '&' if '?' in raw_url else '?'
                raw_url += f'{sep}client_id={client_id}'
            r2 = _req_tg.get(raw_url, headers=headers, timeout=10, allow_redirects=True)
            return r2.url

        # Try track ID approach
        m2 = re.search(r'"id"\s*:\s*(\d+)', resp.text)
        if m2 and client_id:
            track_id = m2.group(1)
            api_url = f"https://api-v2.soundcloud.com/tracks/{track_id}/streams?client_id={client_id}"
            r3 = _req_tg.get(api_url, headers=headers, timeout=10)
            if r3.status_code == 200:
                data = r3.json()
                for key in ['http_mp3_128_url', 'hls_mp3_128_url', 'preview_mp3_128_url']:
                    if data.get(key): return data[key]
    except Exception:
        pass
    return None

@app.route('/api/search_music', methods=['GET','POST'])
def api_search_music():
    q = (request.args.get('q','') or request.form.get('q','')).strip()
    if not q: return jsonify({"results":[],"error":"Vui lòng nhập từ khóa"})
    results = _sc_search(q, limit=10)
    return jsonify({"results":results})

_SC_ALLOWED_HOSTS = {'soundcloud.com', 'www.soundcloud.com', 'm.soundcloud.com', 'on.soundcloud.com'}

@app.route('/api/get_stream', methods=['GET','POST'])
def api_get_stream():
    track_url = (request.args.get('url','') or request.form.get('url','')).strip()
    if not track_url: return jsonify({"stream_url":None,"error":"Thiếu URL bài hát"})
    try:
        parsed = urllib.parse.urlparse(track_url)
        if parsed.scheme not in ('http','https') or parsed.netloc.lower().lstrip('www.') not in _SC_ALLOWED_HOSTS and parsed.netloc.lower() not in _SC_ALLOWED_HOSTS:
            return jsonify({"stream_url":None,"error":"URL không hợp lệ. Chỉ hỗ trợ SoundCloud."})
    except Exception:
        return jsonify({"stream_url":None,"error":"URL không hợp lệ."})
    stream_url = _sc_get_stream_url(track_url)
    if stream_url: return jsonify({"stream_url":stream_url})
    return jsonify({"stream_url":None,"error":"Không lấy được link stream. Thử bài khác!"})

# ── Telegram Bot ──
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8605090305:AAGMxGBN8dHw3Txi4F8K0Z4WsuBD2ETPBFs')
TELEGRAM_ADMIN_ID = int(os.environ.get('TELEGRAM_ADMIN_ID', '8401914033'))
_TG_OFFSET = [0]

def tg_send(chat_id, text, parse_mode='HTML'):
    if not _TG_OK or _req_tg is None: return
    try:
        _req_tg.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',json={'chat_id':chat_id,'text':text[:4000],'parse_mode':parse_mode,'disable_web_page_preview':True},timeout=10)
    except: pass

def tg_notify(text): tg_send(TELEGRAM_ADMIN_ID, text)

def _tg_handle_cmd(chat_id, text):
    if chat_id != TELEGRAM_ADMIN_ID:
        tg_send(chat_id,'⛔ Bạn không có quyền sử dụng bot này.\nLiên hệ @vkhanh3010 để được hỗ trợ.'); return
    parts = text.strip().split(); cmd = parts[0].lower().split('@')[0] if parts else ''; args = parts[1:]
    if cmd in ('/start','/menu','/help'):
        tg_send(chat_id,"""🤖 <b>BOT QUẢN LÝ KEY SERVER — VĂN KHÁNH</b>

/stats — Thống kê tổng quan keys
/keys — 10 VIP keys mới nhất
/freekeys — 10 Free keys mới nhất
/newkey [time] [unit] [devices] — Tạo key VIP
/delkey [KEY] — Xóa key
/resetkey [KEY] — Reset key
/genlink — Tạo link Link4m mới
/approvedev [id] [val] [unit] — Duyệt thiết bị
/revokedev [id] — Thu hồi thiết bị
/listdev — Danh sách thiết bị đã duyệt
/pendingdev — Yêu cầu duyệt đang chờ
/iplog — Nhật ký IP lấy key free
/ddos — Kiểm tra rate limit
/resetip [IP] — Reset giới hạn IP
/status — Trạng thái server""")
    elif cmd == '/stats':
        try:
            db = load_db(); now = time.time(); total = activated = expired = not_act = free_total = 0
            for k, v in db.items():
                if k.startswith('___') or not isinstance(v,dict): continue
                total += 1
                if k.startswith('FREE-'): free_total += 1
                st = v.get('status','')
                if st == 'Đã kích hoạt': activated += 1
                elif st == 'Hết hạn': expired += 1
                else: not_act += 1
            stats = db.get('___FREE_KEY_STATS___',{'total_bypasses':0})
            tg_send(chat_id,f"📊 <b>THỐNG KÊ</b>\n\n🗄 Tổng keys: <b>{total}</b>\n✅ Đã kích hoạt: <b>{activated}</b>\n❌ Hết hạn: <b>{expired}</b>\n⏳ Chưa kích hoạt: <b>{not_act}</b>\n🎁 Keys Free: <b>{free_total}</b>\n🔗 Lượt tạo link4m: <b>{stats.get('total_bypasses',0)}</b>")
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/status':
        try:
            db_size = os.path.getsize(DB_FILE)/1024 if os.path.exists(DB_FILE) else 0
            host = os.environ.get('RENDER_EXTERNAL_URL','localhost')
            with _RATE_LOCK: rl_count = len(_RATE_LIMITER)
            now_vn = datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S')
            tg_send(chat_id,f"🟢 <b>SERVER STATUS</b>\n\n🌐 Host: <code>{host}</code>\n📦 DB Size: <b>{db_size:.1f} KB</b>\n🛡 IPs đang theo dõi: <b>{rl_count}</b>\n⏰ Thời gian VN: <b>{now_vn}</b>")
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/keys':
        try:
            db = load_db(); vip_keys = [(k,v) for k,v in db.items() if not k.startswith('___') and isinstance(v,dict) and not k.startswith('FREE-')]
            vip_keys.sort(key=lambda x: x[1].get('created_at',0), reverse=True)
            if not vip_keys: tg_send(chat_id,'📭 Chưa có VIP key nào.'); return
            lines = ['🔑 <b>10 VIP KEYS MỚI NHẤT:</b>\n']
            for k, v in vip_keys[:10]:
                st = v.get('status','?'); icon = '✅' if st=='Đã kích hoạt' else ('❌' if st=='Hết hạn' else '⏳')
                lines.append(f'{icon} <code>{k}</code>\n   ⏰ {v.get("duration_val",0)} {v.get("duration_unit","?")} | 📱 {v.get("max_devices",1)} TB')
            tg_send(chat_id,'\n'.join(lines))
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/freekeys':
        try:
            db = load_db(); free_keys = [(k,v) for k,v in db.items() if not k.startswith('___') and isinstance(v,dict) and k.startswith('FREE-')]
            free_keys.sort(key=lambda x: x[1].get('created_at',0), reverse=True)
            if not free_keys: tg_send(chat_id,'📭 Chưa có Free key nào.'); return
            lines = ['🎁 <b>10 FREE KEYS MỚI NHẤT:</b>\n']
            for k, v in free_keys[:10]:
                st = v.get('status','?'); icon = '✅' if st=='Đã kích hoạt' else ('❌' if st=='Hết hạn' else '⏳')
                lines.append(f'{icon} <code>{k}</code>\n   📍 {v.get("client_ip","?")} | {format_ts(v.get("created_at",0))}')
            tg_send(chat_id,'\n'.join(lines))
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/newkey':
        try:
            if len(args) < 2: tg_send(chat_id,'❌ Cú pháp: /newkey [time] [unit] [devices]\nVí dụ: /newkey 7 ngày 1'); return
            time_val = args[0]; time_unit = args[1]; max_dev = int(args[2]) if len(args) > 2 else 1
            if time_unit not in ('phút','tiếng','ngày','tháng','năm','permanent'): tg_send(chat_id,'❌ Đơn vị: phút, tiếng, ngày, tháng, năm'); return
            db = load_db(); p1=''.join(random.choices(string.ascii_uppercase+string.digits, k=3)); p2=''.join(random.choices(string.ascii_uppercase+string.digits, k=3))
            pfx={'ngày':f'{time_val}D','tiếng':f'{time_val}H','phút':f'{time_val}P','tháng':f'{time_val}M','năm':f'{time_val}Y','permanent':'VIP'}
            key_name = f"{pfx.get(time_unit,'KEY')}-{p1}-{p2}"
            db[key_name]={'duration_val':int(time_val) if time_unit!='permanent' else 0,'duration_unit':time_unit,'max_devices':max_dev,'status':'Chưa kích hoạt','activated_time':None,'created_at':time.time(),'used_devices':{},'creator_info':'Tạo bởi Admin Bot'}
            save_db(db); tg_send(chat_id,f'✅ <b>Tạo key thành công!</b>\n\n🔑 Key: <code>{key_name}</code>\n⏰ Hạn: {time_val} {time_unit}\n📱 Thiết bị: {max_dev}')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/delkey':
        if not args: tg_send(chat_id,'❌ Cú pháp: /delkey [KEY]'); return
        key = args[0]
        try:
            db = load_db()
            if key in db and not key.startswith('___'): del db[key]; save_db(db); tg_send(chat_id,f'✅ Đã xóa key: <code>{key}</code>')
            else: tg_send(chat_id,f'❌ Key không tồn tại: <code>{key}</code>')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/resetkey':
        if not args: tg_send(chat_id,'❌ Cú pháp: /resetkey [KEY]'); return
        key = args[0]
        try:
            db = load_db()
            if key in db and not key.startswith('___'):
                db[key]['status']='Chưa kích hoạt'; db[key]['activated_time']=None; db[key]['used_devices']={}; save_db(db); tg_send(chat_id,f'✅ Đã reset key: <code>{key}</code>')
            else: tg_send(chat_id,f'❌ Key không tồn tại: <code>{key}</code>')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/genlink':
        try:
            now = time.time(); token=''.join(random.choices(string.ascii_uppercase+string.digits, k=20))
            host = os.environ.get('RENDER_EXTERNAL_URL','https://localhost'); dest_url=f"{host}/nhan-key-free?token={token}"
            short_url, err = shorten_with_link4m(dest_url)
            if not short_url: tg_send(chat_id,f'❌ Không tạo được link: {err}'); return
            db=load_db(); tokens=db.get('___GETKEY_TOKENS___',{}); tokens={k:v for k,v in tokens.items() if now-v.get('created_at',0)<3600}
            tokens[token]={'ip':'ADMIN_BOT','created_at':now-60,'status':'pending','is_admin':True}; db['___GETKEY_TOKENS___']=tokens
            stats=db.get('___FREE_KEY_STATS___',{'total_bypasses':0}); stats['total_bypasses']=stats.get('total_bypasses',0)+1; db['___FREE_KEY_STATS___']=stats; save_db(db)
            tg_send(chat_id,f'🔗 <b>Link Link4m mới (Admin bypass):</b>\n\n<code>{short_url}</code>\n\n⏰ Hết hạn sau 1 giờ\n✅ Admin bypass — không cần VPN check')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/iplog':
        try:
            db=load_db(); ip_history=db.get('___FREE_IP_HISTORY___',{}); now=time.time()
            if not ip_history: tg_send(chat_id,'📭 Chưa có nhật ký IP nào.'); return
            lines=['📋 <b>NHẬT KÝ IP LẤY KEY FREE:</b>\n']
            recent=[(ip,times) for ip,times in ip_history.items() if any(now-t<86400 for t in times)]
            recent.sort(key=lambda x:max(x[1]),reverse=True)
            for ip_addr,times in recent[:20]:
                count=len([t for t in times if now-t<86400]); last=format_ts(max(times))
                lines.append(f'📍 <code>{ip_addr}</code> — {count} key | {last}')
            tg_send(chat_id,'\n'.join(lines) if len(lines)>1 else '📭 Không có dữ liệu trong 24h.')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/ddos':
        try:
            with _RATE_LOCK: rl_copy=dict(_RATE_LIMITER)
            now=time.time(); high=[(ip_addr,len([t for t in times if now-t<60])) for ip_addr,times in rl_copy.items()]
            high=[(ip_addr,cnt) for ip_addr,cnt in high if cnt>=3]; high.sort(key=lambda x:x[1],reverse=True)
            if not high: tg_send(chat_id,'✅ Không phát hiện hoạt động DDoS bất thường.'); return
            lines=[f'⚠️ <b>RATE LIMIT ALERT ({len(high)} IPs):</b>\n']
            for ip_addr,cnt in high[:15]: lines.append(f'🔴 <code>{ip_addr}</code> — {cnt} req/60s')
            tg_send(chat_id,'\n'.join(lines))
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/resetip':
        if not args: tg_send(chat_id,'❌ Cú pháp: /resetip [IP]'); return
        target_ip=args[0]
        try:
            db=load_db(); changed=[]
            ih=db.get('___FREE_IP_HISTORY___',{})
            if target_ip in ih: del ih[target_ip]; changed.append('IP history'); db['___FREE_IP_HISTORY___']=ih
            im=db.get('___IP_KEY_MAP___',{})
            if target_ip in im: del im[target_ip]; changed.append('IP-key map'); db['___IP_KEY_MAP___']=im
            with _RATE_LOCK:
                if target_ip in _RATE_LIMITER: del _RATE_LIMITER[target_ip]; changed.append('Rate limit')
            if changed: save_db(db); tg_send(chat_id,f'✅ Đã reset IP <code>{target_ip}</code>\nĐã xóa: {", ".join(changed)}')
            else: tg_send(chat_id,f'⚠️ IP <code>{target_ip}</code> không có gì để reset.')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/approvedev':
        if len(args)<3: tg_send(chat_id,'❌ Cú pháp: /approvedev [device_id] [val] [unit]'); return
        did=args[0]; val_arg=args[1]; unit_arg=args[2]
        try:
            db=load_db(); approved=db.get("___APPROVED_DEVICES___",{}); now=time.time()
            val_int=int(val_arg) if val_arg.isdigit() else 7; sec=-1
            if unit_arg=="phút": sec=val_int*60
            elif unit_arg=="tiếng": sec=val_int*3600
            elif unit_arg=="ngày": sec=val_int*86400
            elif unit_arg=="tháng": sec=val_int*30*86400
            elif unit_arg=="năm": sec=val_int*365*86400
            exp_ts=-1 if sec==-1 else (now+sec)
            approved[did]={"expiry":exp_ts,"approved_at":now,"val":val_int,"unit":unit_arg,"note":"Duyệt qua Telegram Bot","ip":"BOT"}
            db["___APPROVED_DEVICES___"]=approved; save_db(db)
            tg_send(chat_id,f'✅ <b>ĐÃ DUYỆT DEVICE ID</b>\n🔧 Device: <code>{did}</code>\n⏳ {val_int} {unit_arg}\n⏰ Hết hạn: {"Vĩnh viễn" if exp_ts==-1 else format_ts(exp_ts)}')
        except Exception as e: tg_send(chat_id,f'❌ Lỗi: {e}')
    elif cmd == '/revokedev':
        if not args: tg_send(chat_id,'❌ Cú pháp: /revokedev [device_id]'); return
        did=args[0]; db=load_db(); approved=db.get("___APPROVED_DEVICES___",{})
        if did in approved: del approved[did]; db["___APPROVED_DEVICES___"]=approved; save_db(db); tg_send(chat_id,f'✅ <b>ĐÃ THU HỒI</b>\n🔧 Device: <code>{did}</code>')
        else: tg_send(chat_id,f'⚠️ Device ID <code>{did}</code> không tồn tại.')
    elif cmd == '/listdev':
        db=load_db(); approved=db.get("___APPROVED_DEVICES___",{}); now_ts=time.time()
        if not approved: tg_send(chat_id,'📋 Chưa có thiết bị nào được duyệt.'); return
        lines=['📋 <b>DANH SÁCH DEVICE ĐÃ DUYỆT</b>\n']; count=0
        for did, dinfo in approved.items():
            exp=dinfo.get('expiry',-1); is_perm=(exp==-1)
            status_icon='✅' if (is_perm or exp>now_ts) else '❌'
            time_str='Vĩnh viễn' if is_perm else ('Hết hạn' if exp<now_ts else get_time_left_str(exp))
            short_id=did[:16]+'...' if len(did)>16 else did
            lines.append(f'{status_icon} <code>{short_id}</code>\n   ⏳ {time_str}'); count+=1
            if count>=30: lines.append(f'\n... và {len(approved)-30} thiết bị khác'); break
        lines.append(f'\n<b>Tổng: {len(approved)} thiết bị</b>'); tg_send(chat_id,'\n'.join(lines))
    elif cmd == '/pendingdev':
        db=load_db(); pending=db.get("___DEVICE_REQUESTS___",{}); pending_list=[(rid,rinfo) for rid,rinfo in pending.items() if rinfo.get('status')=='pending']
        if not pending_list: tg_send(chat_id,'📥 Không có yêu cầu nào đang chờ duyệt.'); return
        lines=[f'📥 <b>YÊU CẦU DUYỆT ({len(pending_list)} yêu cầu)</b>\n']; count=0
        for rid, rinfo in pending_list:
            did=rinfo.get('device_id','—'); short_id=did[:16]+'...' if len(did)>16 else did
            lines.append(f'🔧 <code>{short_id}</code>\n   ⏳ {rinfo.get("val",7)} {rinfo.get("unit","ngày")} | 🌐 {rinfo.get("ip","—")}'); count+=1
            if count>=10: lines.append(f'\n... và {len(pending_list)-10} yêu cầu khác'); break
        tg_send(chat_id,'\n'.join(lines))
    else:
        if text.startswith('/'): tg_send(chat_id,f'❓ Lệnh không hợp lệ: <code>{cmd}</code>\nGõ /start để xem menu.')

def _tg_poll_worker():
    import time as _tt; _tt.sleep(10)
    while True:
        try:
            if not _TG_OK or _req_tg is None: _tt.sleep(30); continue
            resp = _req_tg.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates',params={'offset':_TG_OFFSET[0],'timeout':25,'allowed_updates':['message']},timeout=32)
            data = resp.json()
            if data.get('ok'):
                for upd in data.get('result',[]):
                    _TG_OFFSET[0] = upd['update_id']+1
                    try:
                        msg = upd.get('message',{})
                        if msg:
                            cid = msg.get('chat',{}).get('id',0); txt = msg.get('text','').strip()
                            if txt: _tg_handle_cmd(cid,txt)
                    except: pass
        except: _tt.sleep(5)

threading.Thread(target=_tg_poll_worker, daemon=True).start()

# ════════════════════════════════════════════════════════
# HTML TEMPLATES
# ════════════════════════════════════════════════════════

UI_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Key Server — Văn Khánh</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
/* ── RESET & BASE ── */
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
*:focus{outline:none!important}
button:focus,a:focus,input:focus,select:focus,textarea:focus{outline:none!important;box-shadow:none}
:root{
  --bg:#f1f5f9;--panel:#ffffff;--card:#f8fafc;--border:#e2e8f0;--border-focus:#3b82f6;
  --blue:#2563eb;--blue-light:#eff6ff;--blue-hover:#1d4ed8;
  --green:#16a34a;--green-light:#f0fdf4;
  --red:#dc2626;--red-light:#fef2f2;
  --amber:#d97706;--amber-light:#fffbeb;
  --purple:#7c3aed;--purple-light:#f5f3ff;
  --text:#0f172a;--text2:#334155;--muted:#64748b;--subtle:#94a3b8;
  --shadow:0 1px 3px rgba(0,0,0,.1),0 1px 2px rgba(0,0,0,.06);
  --shadow-md:0 4px 6px rgba(0,0,0,.07),0 2px 4px rgba(0,0,0,.06);
  --shadow-lg:0 10px 15px rgba(0,0,0,.07),0 4px 6px rgba(0,0,0,.05);
}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;overflow-x:hidden}

/* ── LOADING SCREEN ── */
#pageLoader{position:fixed;inset:0;z-index:9999;background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;transition:opacity .5s ease,visibility .5s ease}
#pageLoader.hidden{opacity:0;visibility:hidden;pointer-events:none}
.loader-logo{width:72px;height:72px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:1.8rem;color:#fff;margin-bottom:20px;animation:loaderPulse 1.5s ease-in-out infinite;box-shadow:0 0 40px rgba(59,130,246,.5)}
@keyframes loaderPulse{0%,100%{transform:scale(1);box-shadow:0 0 40px rgba(59,130,246,.5)}50%{transform:scale(1.08);box-shadow:0 0 60px rgba(59,130,246,.8)}}
.loader-title{font-size:1.4rem;font-weight:800;color:#fff;margin-bottom:6px;letter-spacing:-.5px}
.loader-sub{font-size:.82rem;color:rgba(255,255,255,.5);margin-bottom:28px}
.loader-bar-wrap{width:180px;height:4px;background:rgba(255,255,255,.15);border-radius:99px;overflow:hidden}
.loader-bar{height:100%;width:0%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:99px;animation:loaderFill 1.8s ease-out forwards}
@keyframes loaderFill{0%{width:0%}60%{width:75%}100%{width:100%}}
.loader-dots{display:flex;gap:6px;margin-top:16px}
.loader-dot{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.3);animation:dotBounce 1.2s ease-in-out infinite}
.loader-dot:nth-child(2){animation-delay:.15s}
.loader-dot:nth-child(3){animation-delay:.3s}
@keyframes dotBounce{0%,80%,100%{transform:scale(0.8);opacity:.5}40%{transform:scale(1.2);opacity:1}}

/* ── TOP NAV ── */
.topnav{position:fixed;top:0;left:0;right:0;z-index:100;height:56px;background:var(--panel);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 16px;gap:12px;box-shadow:var(--shadow)}
.nav-logo{display:flex;align-items:center;gap:9px;font-weight:800;font-size:.95rem;color:var(--blue);letter-spacing:-.3px}
.nav-logo-icon{width:32px;height:32px;background:var(--blue);border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:.85rem;flex-shrink:0}
.nav-links{display:flex;align-items:center;gap:4px;margin-left:auto}
.nav-link{display:inline-flex;align-items:center;gap:6px;padding:7px 12px;border-radius:8px;font-size:.82rem;font-weight:600;color:var(--muted);cursor:pointer;border:none;background:transparent;transition:.15s;font-family:'Inter',sans-serif;text-decoration:none;white-space:nowrap}
.nav-link:hover{color:var(--text);background:#f1f5f9}
.nav-link.active{color:var(--blue);background:var(--blue-light);font-weight:700}
.nav-link.nav-admin{color:var(--blue);border:1px solid var(--border-focus);background:var(--blue-light)}
.nav-link.nav-logout{color:var(--red);border:1px solid #fca5a5;background:var(--red-light)}

/* ── HAMBURGER (RIGHT SIDE) ── */
.hamburger-btn{display:none;flex-direction:column;gap:5px;cursor:pointer;padding:8px;margin-left:auto;border:none;background:transparent;position:relative;z-index:201}
.hamburger-btn span{display:block;width:22px;height:2px;background:var(--text2);border-radius:2px;transition:.28s cubic-bezier(.4,0,.2,1)}
.hamburger-btn.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
.hamburger-btn.open span:nth-child(2){opacity:0;transform:translateX(8px)}
.hamburger-btn.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}

/* ── MOBILE MENU (SLIDES FROM RIGHT) ── */
.mobile-overlay{display:none;position:fixed;inset:0;z-index:198;background:rgba(0,0,0,.4);backdrop-filter:blur(2px)}
.mobile-overlay.open{display:block}
.mobile-menu{position:fixed;top:0;right:-300px;bottom:0;width:280px;z-index:199;background:var(--panel);border-left:1px solid var(--border);padding:70px 16px 24px;flex-direction:column;gap:4px;box-shadow:-4px 0 20px rgba(0,0,0,.15);transition:right .32s cubic-bezier(.4,0,.2,1);overflow-y:auto;display:flex}
.mobile-menu.open{right:0}
.mobile-menu .nav-link{padding:12px 14px;justify-content:flex-start;font-size:.88rem;border-radius:10px}
.mobile-menu-title{font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;padding:8px 14px 4px;margin-top:8px}
.mobile-menu-divider{height:1px;background:var(--border);margin:8px 0}

/* ── MAIN ── */
.main{max-width:600px;margin:0 auto;padding:68px 12px 40px}

/* ── CARDS ── */
.card{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:14px;box-shadow:var(--shadow)}
.card-hd{display:flex;align-items:center;gap:9px;margin-bottom:16px;font-weight:700;font-size:.9rem;color:var(--text)}
.ic-card{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:.88rem;flex-shrink:0}
.ic-blue{background:var(--blue-light);color:var(--blue)}
.ic-green{background:var(--green-light);color:var(--green)}
.ic-red{background:var(--red-light);color:var(--red)}
.ic-amber{background:var(--amber-light);color:var(--amber)}
.ic-purple{background:var(--purple-light);color:var(--purple)}

/* ── FORM ELEMENTS ── */
.fg{margin-bottom:12px}
.fg label{display:block;font-size:.76rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.fg input,.fg select,.fg textarea{width:100%;padding:11px 14px;background:#fff;border:1.5px solid var(--border);border-radius:10px;color:var(--text);font-size:.9rem;font-family:'Inter',sans-serif;outline:none;transition:.15s}
.fg input:focus,.fg select:focus,.fg textarea:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(37,99,235,.1)}
.fg textarea{resize:vertical;min-height:70px}
.row2{display:flex;gap:10px}.row2>*{flex:1}

/* ── BUTTONS ── */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:11px 18px;border-radius:10px;font-weight:700;font-size:.88rem;cursor:pointer;border:none;transition:.15s;font-family:'Inter',sans-serif;letter-spacing:.2px}
.btn-primary{background:var(--blue);color:#fff;width:100%}
.btn-primary:hover:not(:disabled){background:var(--blue-hover);transform:translateY(-1px);box-shadow:0 4px 12px rgba(37,99,235,.35)}
.btn-primary:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-green{background:var(--green);color:#fff}
.btn-green:hover:not(:disabled){background:#15803d;transform:translateY(-1px)}
.btn-red{background:var(--red);color:#fff}
.btn-red:hover:not(:disabled){background:#b91c1c;transform:translateY(-1px)}
.btn-outline{background:#fff;color:var(--text2);border:1.5px solid var(--border)}
.btn-outline:hover{background:#f8fafc;border-color:var(--text2)}
.btn-sm{padding:6px 11px;font-size:.76rem;border-radius:7px;border:1.5px solid var(--border);background:#fff;color:var(--text2);cursor:pointer;font-weight:600;font-family:'Inter',sans-serif;transition:.15s;display:inline-flex;align-items:center;gap:5px}
.btn-sm:hover{background:#f1f5f9}
.btn-sm-blue{color:var(--blue);border-color:#bfdbfe;background:var(--blue-light)}
.btn-sm-blue:hover{background:#dbeafe}
.btn-sm-red{color:var(--red);border-color:#fca5a5;background:var(--red-light)}
.btn-sm-red:hover{background:#fee2e2}
.btn-sm-green{color:var(--green);border-color:#86efac;background:var(--green-light)}
.btn-sm-green:hover{background:#dcfce7}
.btn-sm-amber{color:var(--amber);border-color:#fcd34d;background:var(--amber-light)}
.btn-sm-amber:hover{background:#fef9c3}

/* ── BADGES ── */
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:.72rem;font-weight:700}
.badge-blue{background:var(--blue-light);color:var(--blue)}
.badge-green{background:var(--green-light);color:var(--green)}
.badge-red{background:var(--red-light);color:var(--red)}
.badge-amber{background:var(--amber-light);color:var(--amber)}
.badge-gray{background:#f1f5f9;color:var(--muted)}
.badge-purple{background:var(--purple-light);color:var(--purple)}

/* ── SPINNER ── */
@keyframes spin{to{transform:rotate(360deg)}}
.spinner{width:22px;height:22px;border:2.5px solid #e2e8f0;border-top-color:var(--blue);border-radius:50%;animation:spin .75s linear infinite;flex-shrink:0}
.spinner-sm{width:16px;height:16px;border-width:2px}
.spinner-white{border-color:rgba(255,255,255,.3);border-top-color:#fff}

/* ── ANIM ── */
@keyframes drawCheck{to{stroke-dashoffset:0}}
@keyframes popIn{from{transform:scale(0)}50%{transform:scale(1.2)}to{transform:scale(1)}}
.anim-success,.anim-fail{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;animation:popIn .4s cubic-bezier(.34,1.56,.64,1) both}
.anim-success{background:var(--green-light);border:2px solid #86efac}
.anim-success svg{stroke:var(--green)}
.anim-fail{background:var(--red-light);border:2px solid #fca5a5}
.anim-fail svg{stroke:var(--red)}
.check-circle{stroke-dasharray:100;stroke-dashoffset:100;animation:drawCheck .5s .2s ease forwards;stroke-linecap:round;stroke-linejoin:round;stroke-width:2.5;fill:none}

/* ── TOAST ── */
@keyframes toastIn{from{opacity:0;transform:translateY(20px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes toastOut{to{opacity:0;transform:translateY(10px)}}
.toast-container{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px;align-items:center;pointer-events:none;width:min(400px,90vw)}
.toast{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 18px;box-shadow:var(--shadow-lg);font-size:.85rem;font-weight:600;display:flex;align-items:center;gap:10px;animation:toastIn .35s cubic-bezier(.34,1.56,.64,1) both;pointer-events:all;width:100%}
.toast.t-success{border-color:#86efac;background:var(--green-light);color:var(--green)}
.toast.t-error{border-color:#fca5a5;background:var(--red-light);color:var(--red)}
.toast.t-info{border-color:#bfdbfe;background:var(--blue-light);color:var(--blue)}
.toast.t-warn{border-color:#fcd34d;background:var(--amber-light);color:var(--amber)}

/* ── ALERT ── */
.alert{border-radius:10px;padding:13px 16px;font-size:.85rem;font-weight:600;display:none;margin-top:10px;align-items:flex-start;gap:9px}
.alert.show{display:flex}
.alert-success{background:var(--green-light);border:1px solid #86efac;color:var(--green)}
.alert-error{background:var(--red-light);border:1px solid #fca5a5;color:var(--red)}
.alert-info{background:var(--blue-light);border:1px solid #bfdbfe;color:var(--blue)}
.alert-warn{background:var(--amber-light);border:1px solid #fcd34d;color:var(--amber)}

/* ── TABS ── */
.tab{display:none}
.tab.active{display:block;animation:tabIn .35s cubic-bezier(.22,1,.36,1) both}
@keyframes tabIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}

/* ── SOCIAL BUTTONS ── */
.social-btn{display:flex;align-items:center;gap:12px;padding:13px 16px;border-radius:12px;border:1.5px solid var(--border);text-decoration:none;color:var(--text);font-weight:600;font-size:.88rem;margin-bottom:8px;transition:.15s;background:#fff;-webkit-tap-highlight-color:transparent}
.social-btn:hover{border-color:#93c5fd;background:var(--blue-light);transform:translateX(3px)}
.social-btn .s-icon{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:1.05rem;flex-shrink:0;pointer-events:none}
.social-btn .s-text{display:flex;flex-direction:column;gap:1px;pointer-events:none}
.social-btn .s-label{font-size:.7rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.3px}
.social-btn .s-name{font-size:.88rem;font-weight:700}
.social-btn .s-arrow{margin-left:auto;color:var(--subtle);font-size:.78rem;pointer-events:none}
.s-tg .s-icon{background:#e8f4fd;color:#229ED9}
.s-tt .s-icon{background:#f3f3f3;color:#000}
.s-yt .s-icon{background:#fee2e2;color:#dc2626}
.s-fb .s-icon{background:#eff6ff;color:#1877f2}

/* ── VIP MUSIC PLAYER ── */
.music-card{background:linear-gradient(135deg,#0f0e2b 0%,#1a1740 40%,#0d1b3e 100%);border-radius:20px;padding:20px;margin-bottom:14px;color:#fff;position:relative;overflow:hidden;border:1px solid rgba(139,92,246,.2)}
.music-card::before{content:'';position:absolute;top:-50%;right:-30%;width:280px;height:280px;background:radial-gradient(circle,rgba(139,92,246,.15) 0%,transparent 70%);pointer-events:none}
.music-card::after{content:'';position:absolute;bottom:-40%;left:-20%;width:200px;height:200px;background:radial-gradient(circle,rgba(59,130,246,.12) 0%,transparent 70%);pointer-events:none}
.music-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.music-header-title{font-size:.72rem;font-weight:700;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:1px}
.music-header-icon{display:flex;gap:4px;align-items:center}
.music-dot{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.2)}
.music-dot.active{background:#a5b4fc;animation:dotPulse 1.5s ease-in-out infinite}
@keyframes dotPulse{0%,100%{opacity:.5;transform:scale(1)}50%{opacity:1;transform:scale(1.3)}}
.music-tracks{display:flex;gap:8px;margin-bottom:18px}
.track-btn{flex:1;padding:10px 8px;border-radius:10px;border:1.5px solid rgba(255,255,255,.1);background:rgba(255,255,255,.06);cursor:pointer;text-align:center;transition:.2s;-webkit-tap-highlight-color:transparent}
.track-btn .t-num{font-size:.6rem;font-weight:800;color:rgba(255,255,255,.4);margin-bottom:3px;text-transform:uppercase;letter-spacing:.5px}
.track-btn .t-name{font-size:.72rem;font-weight:700;color:rgba(255,255,255,.6);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track-btn:hover{border-color:rgba(255,255,255,.3);background:rgba(255,255,255,.12)}
.track-btn.playing{border-color:#818cf8;background:rgba(129,140,248,.2);box-shadow:0 0 12px rgba(129,140,248,.3)}
.track-btn.playing .t-num{color:#818cf8}
.track-btn.playing .t-name{color:#fff;font-weight:800}
.music-now-playing{display:flex;align-items:center;gap:16px;margin-bottom:18px;position:relative;z-index:1}
.vinyl-wrap{position:relative;width:68px;height:68px;flex-shrink:0}
.vinyl{width:68px;height:68px;border-radius:50%;background:conic-gradient(#1a1740 0deg,#0d1433 30deg,#1e1b4b 60deg,#0f0e2b 90deg,#1a1740 120deg,#0d1433 150deg,#1e1b4b 180deg,#0f0e2b 210deg,#1a1740 240deg,#0d1433 270deg,#1e1b4b 300deg,#0f0e2b 330deg,#1a1740 360deg);border:3px solid rgba(165,180,252,.25);display:flex;align-items:center;justify-content:center;box-shadow:0 0 25px rgba(139,92,246,.3),0 0 50px rgba(139,92,246,.1)}
.vinyl-c{width:20px;height:20px;background:linear-gradient(135deg,#818cf8,#a78bfa);border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 0 8px rgba(167,139,250,.8)}
.vinyl.spin{animation:vspin 3s linear infinite}
@keyframes vspin{to{transform:rotate(360deg)}}
.vinyl-rings{position:absolute;inset:0;border-radius:50%;border:1px solid rgba(165,180,252,.08)}
.music-info{flex:1;min-width:0}
.music-info .m-title{font-size:.88rem;font-weight:800;color:#fff;margin-bottom:5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;letter-spacing:-.2px}
.music-info .m-status{font-size:.73rem;color:rgba(255,255,255,.45);font-weight:500;display:flex;align-items:center;gap:5px}
.music-status-dot{width:6px;height:6px;border-radius:50%;background:#a5b4fc;flex-shrink:0}
.music-status-dot.playing{animation:statusPulse 1s ease-in-out infinite}
@keyframes statusPulse{0%,100%{opacity:.4}50%{opacity:1}}
.music-controls{display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:16px;position:relative;z-index:1}
.m-ctrl{width:36px;height:36px;border-radius:50%;border:1.5px solid rgba(255,255,255,.15);background:rgba(255,255,255,.07);cursor:pointer;color:rgba(255,255,255,.6);font-size:.82rem;display:flex;align-items:center;justify-content:center;transition:.2s;flex-shrink:0;-webkit-tap-highlight-color:transparent}
.m-ctrl:hover{border-color:rgba(255,255,255,.4);color:#fff;background:rgba(255,255,255,.15);transform:scale(1.05)}
.m-play{width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none;cursor:pointer;color:#fff;font-size:1.05rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.2s;box-shadow:0 4px 20px rgba(139,92,246,.6),0 0 0 4px rgba(139,92,246,.2);-webkit-tap-highlight-color:transparent}
.m-play:hover{transform:scale(1.08);box-shadow:0 6px 28px rgba(139,92,246,.8),0 0 0 6px rgba(139,92,246,.25)}
.seek-bar{width:100%;height:4px;border-radius:99px;background:rgba(255,255,255,.1);outline:none;-webkit-appearance:none;cursor:pointer;accent-color:#818cf8;display:block;position:relative;z-index:1}
.seek-bar::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:#a5b4fc;cursor:pointer;box-shadow:0 0 6px rgba(165,180,252,.8)}
.seek-times{display:flex;justify-content:space-between;font-size:.65rem;color:rgba(255,255,255,.35);margin-top:6px;font-weight:700;letter-spacing:.3px;position:relative;z-index:1}
.music-vol-row{display:flex;align-items:center;gap:8px;margin-top:10px;position:relative;z-index:1}
.music-vol-icon{font-size:.75rem;color:rgba(255,255,255,.4);flex-shrink:0}
.music-vol-bar{flex:1;height:3px;border-radius:99px;background:rgba(255,255,255,.1);outline:none;-webkit-appearance:none;cursor:pointer;accent-color:#818cf8}

/* ── SOUNDCLOUD SEARCH ── */
.sc-search-card{background:#fff;border:1.5px solid var(--border);border-radius:16px;padding:18px;margin-bottom:14px}
.sc-search-hd{display:flex;align-items:center;gap:8px;margin-bottom:14px}
.sc-search-hd .hd-icon{width:34px;height:34px;background:#fff0f5;border-radius:9px;display:flex;align-items:center;justify-content:center;color:#ff5500;font-size:.88rem;flex-shrink:0}
.sc-search-hd .hd-title{font-weight:700;font-size:.9rem;color:var(--text)}
.sc-search-hd .hd-sub{font-size:.75rem;color:var(--muted);margin-top:1px}
.sc-input-row{display:flex;gap:8px;margin-bottom:0}
.sc-input{flex:1;padding:11px 14px;border:1.5px solid var(--border);border-radius:10px;font-size:.88rem;font-family:'Inter',sans-serif;outline:none;color:var(--text);transition:.15s;background:#fff}
.sc-input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(37,99,235,.1)}
.sc-btn{padding:11px 16px;background:var(--blue);color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.85rem;cursor:pointer;transition:.15s;font-family:'Inter',sans-serif;white-space:nowrap;display:flex;align-items:center;gap:6px}
.sc-btn:hover:not(:disabled){background:var(--blue-hover)}
.sc-btn:disabled{opacity:.5;cursor:not-allowed}
.sc-loading{display:none;align-items:center;gap:10px;padding:16px 0;color:var(--muted);font-size:.85rem;font-weight:600}
.sc-results{margin-top:12px;display:none;flex-direction:column;gap:7px}
.sc-results.show{display:flex}
/* SC result item with image */
.sc-result-item{display:flex;align-items:center;gap:11px;padding:10px 11px;border-radius:10px;border:1.5px solid var(--border);cursor:pointer;transition:.15s;background:#fff;-webkit-tap-highlight-color:transparent}
.sc-result-item:hover{border-color:#93c5fd;background:#f0f7ff;transform:translateX(2px)}
.sc-result-item.selected{border-color:var(--blue);background:var(--blue-light)}
.sc-cover-wrap{width:50px;height:50px;flex-shrink:0;position:relative}
.sc-cover{width:50px;height:50px;border-radius:8px;object-fit:cover;display:block}
.sc-cover-ph{width:50px;height:50px;border-radius:8px;background:linear-gradient(135deg,#ff5500,#ff8800);display:flex;align-items:center;justify-content:center;font-size:1.2rem;color:#fff}
.sc-track-info{flex:1;min-width:0}
.sc-track-title{font-size:.83rem;font-weight:700;color:var(--text);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;line-height:1.35}
.sc-track-meta{font-size:.72rem;color:var(--muted);margin-top:3px;display:flex;align-items:center;gap:6px}
.sc-play-hint{font-size:.7rem;color:var(--blue);font-weight:600;margin-top:4px;display:flex;align-items:center;gap:3px}
.sc-player-wrap{margin-top:12px;display:none}
.sc-player-wrap.show{display:block}
.sc-player-card{background:linear-gradient(135deg,#fff7ed,#fffbf0);border:1.5px solid #fed7aa;border-radius:12px;padding:14px}
.sc-player-title{font-size:.82rem;font-weight:700;color:var(--text);margin-bottom:10px;display:flex;align-items:center;gap:7px;overflow:hidden}
.sc-player-title span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sc-player-controls{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.sc-player-play{width:38px;height:38px;border-radius:50%;background:var(--blue);border:none;cursor:pointer;color:#fff;font-size:.9rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:.15s;-webkit-tap-highlight-color:transparent}
.sc-player-play:hover{background:var(--blue-hover);transform:scale(1.05)}
.sc-player-vol{width:70px;height:4px;border-radius:99px;background:#e2e8f0;outline:none;-webkit-appearance:none;cursor:pointer;accent-color:var(--blue)}
.sc-player-time{font-size:.72rem;color:var(--muted);font-weight:600;font-variant-numeric:tabular-nums;white-space:nowrap}
.sc-seek{flex:1;height:4px;border-radius:99px;background:#e2e8f0;outline:none;-webkit-appearance:none;cursor:pointer;accent-color:var(--blue)}

/* ── GETKEY ── */
.getkey-card{background:linear-gradient(135deg,#eff6ff,#f0fdf4);border:1.5px solid #bfdbfe;border-radius:16px;padding:20px;margin-bottom:14px}
.getkey-hd{text-align:center;margin-bottom:16px}
.getkey-hd .gh-icon{width:48px;height:48px;background:var(--blue);border-radius:13px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.1rem;margin:0 auto 10px}
.getkey-hd .gh-title{font-weight:800;font-size:1.05rem;color:var(--text)}
.getkey-hd .gh-sub{font-size:.78rem;color:var(--muted);margin-top:4px}
.getkey-info{display:flex;gap:10px;margin-bottom:16px}
.getkey-info-box{flex:1;background:#fff;border:1.5px solid var(--border);border-radius:10px;padding:12px;text-align:center}
.getkey-info-box .gi-label{font-size:.68rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.getkey-info-box .gi-val{font-size:1.3rem;font-weight:900;color:var(--blue)}
.getkey-info-box .gi-unit{font-size:.72rem;color:var(--muted);margin-top:2px;font-weight:500}
.getkey-limit{font-size:.76rem;color:var(--muted);text-align:center;margin-bottom:14px;display:flex;align-items:center;justify-content:center;gap:5px}
.getkey-result{margin-top:14px;display:none}
.getkey-result.show{display:block}
.getkey-result .link-box{background:#fff;border:1.5px solid var(--border);border-radius:10px;padding:12px 14px;font-size:.85rem;color:var(--blue);font-weight:600;word-break:break-all;margin-bottom:10px}

/* ── CHECK KEY ── */
.checkkey-result{margin-top:12px;display:none}
.checkkey-result.show{display:block}
.ckr-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}
.ckr-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:11px 12px}
.ckr-box .ck-label{font-size:.67rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px}
.ckr-box .ck-val{font-size:.88rem;font-weight:700;color:var(--text);word-break:break-all}
.ckr-box.full{grid-column:1/-1}

/* ── ADMIN TABS ── */
.admin-tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:16px;background:#f8fafc;border-radius:12px;padding:6px;border:1px solid var(--border)}
.admin-tab-btn{flex:1;min-width:0;padding:9px 10px;border-radius:8px;border:none;background:transparent;color:var(--muted);font-size:.76rem;font-weight:600;cursor:pointer;transition:.15s;font-family:'Inter',sans-serif;white-space:nowrap;text-align:center;display:flex;align-items:center;justify-content:center;gap:5px;-webkit-tap-highlight-color:transparent}
.admin-tab-btn:hover{color:var(--text);background:rgba(255,255,255,.7)}
.admin-tab-btn.active{background:#fff;color:var(--blue);font-weight:700;box-shadow:var(--shadow)}
.admin-tab-content{display:none}
.admin-tab-content.active{display:block;animation:tabIn .3s both}

/* ── TABLES ── */
.tbl-wrap{overflow-x:auto;border-radius:10px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:.8rem}
th{padding:10px 12px;background:#f8fafc;color:var(--muted);font-weight:700;text-transform:uppercase;font-size:.7rem;letter-spacing:.4px;white-space:nowrap;border-bottom:1px solid var(--border)}
td{padding:10px 12px;border-top:1px solid #f1f5f9;vertical-align:middle}
tr:hover td{background:#fafafa}
.td-actions{display:flex;gap:4px;flex-wrap:wrap}

/* ── INFO ROWS ── */
.info-row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--border);font-size:.85rem}
.info-row:last-child{border-bottom:none}
.info-label{color:var(--muted);font-weight:600}
.info-val{color:var(--text);font-weight:700;text-align:right}

/* ── DEVICE CARDS ── */
.dev-req-card{background:#fff;border:1.5px solid var(--border);border-radius:11px;padding:13px;margin-bottom:8px;transition:.15s}
.dev-req-card:hover{border-color:#93c5fd}
.dev-id{font-family:monospace;font-size:.78rem;font-weight:700;color:var(--text);word-break:break-all;margin-bottom:7px}
.dev-meta{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:9px}
.dev-meta span{background:#f1f5f9;color:var(--muted);padding:2px 8px;border-radius:5px;font-size:.72rem;font-weight:600}
.dev-actions{display:flex;gap:6px;flex-wrap:wrap;align-items:center}

/* ── LOG LINES ── */
.log-container{background:#0f172a;border-radius:10px;padding:14px;font-family:monospace;font-size:.75rem;color:#94a3b8;max-height:350px;overflow-y:auto;line-height:1.7}
.log-container .l-time{color:#64748b}
.log-container .l-ip{color:#38bdf8}
.log-container .l-method{color:#34d399}
.log-container .l-path{color:#e2e8f0}

/* ── STATS CARDS ── */
.stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat-box{background:#fff;border:1.5px solid var(--border);border-radius:12px;padding:14px;text-align:center}
.stat-box .s-num{font-size:1.8rem;font-weight:900;line-height:1;margin-bottom:5px}
.stat-box .s-label{font-size:.72rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.s-blue{color:var(--blue)}.s-green{color:var(--green)}.s-red{color:var(--red)}.s-amber{color:var(--amber)}.s-purple{color:var(--purple)}

/* ── RADIO ── */
.radio-row{display:flex;gap:9px}
.radio-opt{flex:1;padding:10px 12px;border:1.5px solid var(--border);border-radius:10px;cursor:pointer;display:flex;align-items:center;gap:8px;font-size:.84rem;font-weight:600;color:var(--muted);transition:.15s;background:#fff;-webkit-tap-highlight-color:transparent}
.radio-opt:has(input:checked){border-color:var(--blue);color:var(--blue);background:var(--blue-light)}
.radio-opt input{width:14px;height:14px;accent-color:var(--blue)}

/* ── IP INFO ── */
.ip-info-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.ip-cell{background:#f8fafc;border:1px solid var(--border);border-radius:9px;padding:10px 12px}
.ip-cell.full{grid-column:1/-1}
.ip-cell .ic-label{font-size:.67rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
.ip-cell .ic-val{font-size:.85rem;font-weight:700;color:var(--text);word-break:break-all}

/* ── LOGIN MODAL ── */
.modal-overlay{position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:300;display:flex;align-items:center;justify-content:center;padding:16px;backdrop-filter:blur(4px)}
.modal-overlay.hidden{display:none}
.modal-card{background:#fff;border-radius:20px;padding:32px 28px;width:min(380px,100%);box-shadow:0 25px 50px rgba(0,0,0,.2);animation:popIn .35s cubic-bezier(.34,1.56,.64,1) both}
.modal-title{font-weight:800;font-size:1.1rem;color:var(--text);text-align:center;margin-bottom:5px}
.modal-sub{font-size:.8rem;color:var(--muted);text-align:center;margin-bottom:22px}
.modal-icon{width:52px;height:52px;background:var(--blue-light);border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;font-size:1.3rem;color:var(--blue)}

/* ── RESPONSIVE ── */
@media(max-width:520px){
  .nav-links{display:none}
  .hamburger-btn{display:flex}
  .ckr-grid{grid-template-columns:1fr}
  .stats-grid{grid-template-columns:1fr 1fr}
  .admin-tabs{gap:2px}
  .admin-tab-btn{font-size:.68rem;padding:8px 5px}
}

/* ── MISC ── */
.divider{height:1px;background:var(--border);margin:14px 0}
.text-muted{color:var(--muted);font-size:.82rem}
.empty-state{text-align:center;padding:24px;color:var(--muted);font-size:.85rem}
.empty-state i{font-size:1.8rem;display:block;margin-bottom:8px;opacity:.4}
.free-link-box{background:var(--blue-light);border:1.5px solid #bfdbfe;border-radius:12px;padding:14px;margin-top:12px}
.free-link-label{font-size:.72rem;font-weight:700;color:var(--blue);margin-bottom:8px;text-transform:uppercase;letter-spacing:.4px}
.free-link-input{width:100%;padding:9px 12px;background:#fff;border:1px solid #bfdbfe;border-radius:8px;color:var(--blue);font-weight:700;font-size:.85rem;margin-bottom:8px;cursor:text;font-family:monospace}
</style>
</head>
<body>

<!-- ══ LOADING SCREEN ══ -->
<div id="pageLoader">
  <div class="loader-logo"><i class="fa-solid fa-shield-halved"></i></div>
  <div class="loader-title">Key Server</div>
  <div class="loader-sub">Đang khởi động hệ thống...</div>
  <div class="loader-bar-wrap"><div class="loader-bar"></div></div>
  <div class="loader-dots">
    <div class="loader-dot"></div>
    <div class="loader-dot"></div>
    <div class="loader-dot"></div>
  </div>
</div>

<!-- ══ TOP NAV ══ -->
<nav class="topnav">
  <div class="nav-logo">
    <div class="nav-logo-icon"><i class="fa-solid fa-shield-halved"></i></div>
    Key Server
  </div>

  <!-- Desktop nav -->
  <div class="nav-links" id="desktopNav">
    {% if not session.get('is_admin') %}
    <button class="nav-link active" id="nl-home" onclick="sw('home')"><i class="fa-solid fa-house"></i> Trang Chủ</button>
    <button class="nav-link" id="nl-getkey" onclick="sw('getkey')"><i class="fa-solid fa-key"></i> GetKey</button>
    <button class="nav-link nav-admin" onclick="openLoginModal()"><i class="fa-solid fa-lock"></i> Đăng Nhập Admin</button>
    {% else %}
    <button class="nav-link active" id="nl-home" onclick="sw('home')"><i class="fa-solid fa-house"></i> Trang Chủ</button>
    <button class="nav-link" id="nl-getkey" onclick="sw('getkey')"><i class="fa-solid fa-key"></i> GetKey</button>
    <button class="nav-link" id="nl-admin" onclick="sw('admin')"><i class="fa-solid fa-shield-halved"></i> Quản Trị</button>
    <a href="/logout" class="nav-link nav-logout"><i class="fa-solid fa-right-from-bracket"></i> Đăng Xuất</a>
    {% endif %}
  </div>

  <!-- Mobile hamburger -->
  <button class="hamburger-btn" id="hbgBtn" onclick="toggleMobileMenu()">
    <span></span><span></span><span></span>
  </button>
</nav>

<!-- Mobile overlay -->
<div class="mobile-overlay" id="mobileOverlay" onclick="closeMobileMenu()"></div>

<!-- Mobile menu (slides from RIGHT) -->
<div class="mobile-menu" id="mobileMenu">
  <div class="mobile-menu-title">Điều Hướng</div>
  {% if not session.get('is_admin') %}
  <button class="nav-link" onclick="sw('home');closeMobileMenu()"><i class="fa-solid fa-house"></i> Trang Chủ</button>
  <button class="nav-link" onclick="sw('getkey');closeMobileMenu()"><i class="fa-solid fa-key"></i> GetKey</button>
  <button class="nav-link nav-admin" onclick="openLoginModal();closeMobileMenu()"><i class="fa-solid fa-lock"></i> Đăng Nhập Admin</button>
  {% else %}
  <button class="nav-link" onclick="sw('home');closeMobileMenu()"><i class="fa-solid fa-house"></i> Trang Chủ</button>
  <button class="nav-link" onclick="sw('getkey');closeMobileMenu()"><i class="fa-solid fa-key"></i> GetKey</button>
  <div class="mobile-menu-divider"></div>
  <div class="mobile-menu-title">Quản Trị Admin</div>
  <button class="nav-link" onclick="sw('admin');sw_admin('home');closeMobileMenu()"><i class="fa-solid fa-circle-info"></i> Admin Home</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('taokhoa');closeMobileMenu()"><i class="fa-solid fa-plus"></i> Tạo Key</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('database');closeMobileMenu()"><i class="fa-solid fa-database"></i> Quản Lý Keys</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('checkkey');closeMobileMenu()"><i class="fa-solid fa-shield-halved"></i> Kiểm Tra Key</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('keyfree');closeMobileMenu()"><i class="fa-solid fa-gift"></i> Key Free</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('stats');closeMobileMenu()"><i class="fa-solid fa-chart-bar"></i> Thống Kê</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('security');closeMobileMenu()"><i class="fa-solid fa-lock"></i> Bảo Mật</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('devices');closeMobileMenu()"><i class="fa-solid fa-mobile-screen"></i> Thiết Bị</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('weblogs');closeMobileMenu()"><i class="fa-solid fa-list-ul"></i> Nhật Ký Web</button>
  <button class="nav-link" onclick="sw('admin');sw_admin('settings');closeMobileMenu()"><i class="fa-solid fa-gear"></i> Settings</button>
  <div class="mobile-menu-divider"></div>
  <a href="/logout" class="nav-link nav-logout"><i class="fa-solid fa-right-from-bracket"></i> Đăng Xuất</a>
  {% endif %}
</div>

<!-- Toast container -->
<div class="toast-container" id="toastContainer"></div>

<!-- ══ MAIN ══ -->
<div class="main">

<!-- ════ TAB: HOME ════ -->
<div id="tab-home" class="tab active">

  <!-- Social links -->
  <div class="card">
    <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-link"></i></div> <span>Mạng Xã Hội Admin</span></div>
    <a href="https://t.me/vkhanh3010" target="_blank" class="social-btn s-tg">
      <div class="s-icon"><i class="fa-brands fa-telegram"></i></div>
      <div class="s-text"><span class="s-label">Liên hệ</span><span class="s-name">Telegram Admin</span></div>
      <i class="fa-solid fa-chevron-right s-arrow"></i>
    </a>
    <a href="https://www.tiktok.com/@midu.c2?_r=1&_t=ZS-96dFFSbVHBE" target="_blank" class="social-btn s-tt">
      <div class="s-icon"><i class="fa-brands fa-tiktok"></i></div>
      <div class="s-text"><span class="s-label">Follow</span><span class="s-name">Kênh TikTok Chính Thức</span></div>
      <i class="fa-solid fa-chevron-right s-arrow"></i>
    </a>
    <a href="https://youtube.com/@dokimodsgame?si=hrkcwAeZD7UKgKTB" target="_blank" class="social-btn s-yt">
      <div class="s-icon"><i class="fa-brands fa-youtube"></i></div>
      <div class="s-text"><span class="s-label">Subscribe</span><span class="s-name">YouTube DokiMods</span></div>
      <i class="fa-solid fa-chevron-right s-arrow"></i>
    </a>
    <a href="https://www.facebook.com/share/1ERXsth7Zr/" target="_blank" class="social-btn s-fb">
      <div class="s-icon"><i class="fa-brands fa-facebook-f"></i></div>
      <div class="s-text"><span class="s-label">Theo dõi</span><span class="s-name">Facebook</span></div>
      <i class="fa-solid fa-chevron-right s-arrow"></i>
    </a>
  </div>

  <!-- VIP Music Player -->
  <div class="music-card">
    <div class="music-header">
      <span class="music-header-title"><i class="fa-solid fa-headphones-simple" style="margin-right:5px"></i>Nhạc Nền</span>
      <div class="music-header-icon">
        <div class="music-dot active"></div>
        <div class="music-dot"></div>
        <div class="music-dot"></div>
      </div>
    </div>
    <div class="music-tracks">
      <div class="track-btn playing" id="tr0" onclick="selectTrack(0)">
        <div class="t-num">Bài 1</div>
        <div class="t-name">Nhạc Nền 1</div>
      </div>
      <div class="track-btn" id="tr1" onclick="selectTrack(1)">
        <div class="t-num">Bài 2</div>
        <div class="t-name">Nhạc Nền 2</div>
      </div>
      <div class="track-btn" id="tr2" onclick="selectTrack(2)">
        <div class="t-num">Bài 3</div>
        <div class="t-name">Nhạc Nền 3</div>
      </div>
    </div>
    <div class="music-now-playing">
      <div class="vinyl-wrap">
        <div class="vinyl" id="vinylEl">
          <div class="vinyl-c"><i class="fa-solid fa-music" style="font-size:.45rem;color:#fff"></i></div>
        </div>
      </div>
      <div class="music-info">
        <div class="m-title" id="mTitle">Nhạc Nền 1</div>
        <div class="m-status">
          <div class="music-status-dot" id="statusDot"></div>
          <span id="mStatus">Đang dừng</span>
        </div>
      </div>
    </div>
    <div class="music-controls">
      <button class="m-ctrl" onclick="prevTrack()" title="Bài trước"><i class="fa-solid fa-backward-step"></i></button>
      <button class="m-ctrl" onclick="seekBack()" title="Lùi 10s"><i class="fa-solid fa-rotate-left" style="font-size:.75rem"></i></button>
      <button class="m-play" onclick="toggleMusic()" id="playBtn"><i class="fa-solid fa-play" id="playIcon"></i></button>
      <button class="m-ctrl" onclick="seekFwd()" title="Tiến 10s"><i class="fa-solid fa-rotate-right" style="font-size:.75rem"></i></button>
      <button class="m-ctrl" onclick="nextTrack()" title="Bài tiếp"><i class="fa-solid fa-forward-step"></i></button>
    </div>
    <input type="range" class="seek-bar" id="seekBar" value="0" min="0" max="100" step="0.1" oninput="onSeekInput(this.value)">
    <div class="seek-times"><span id="curTime">0:00</span><span id="durTime">0:00</span></div>
    <div class="music-vol-row">
      <i class="fa-solid fa-volume-low music-vol-icon"></i>
      <input type="range" class="music-vol-bar" id="volBar" value="80" min="0" max="100" step="1" oninput="setVol(this.value)">
      <i class="fa-solid fa-volume-high music-vol-icon"></i>
    </div>
    <audio id="bgAudio" src="/nhac.mp3"></audio>
  </div>

  <!-- SoundCloud Search -->
  <div class="sc-search-card">
    <div class="sc-search-hd">
      <div class="hd-icon"><i class="fa-brands fa-soundcloud"></i></div>
      <div>
        <div class="hd-title">Tìm Nhạc SoundCloud</div>
        <div class="hd-sub">Tìm kiếm và nghe bất kỳ bài hát nào</div>
      </div>
    </div>
    <div class="sc-input-row">
      <input type="text" class="sc-input" id="scQuery" placeholder="Nhập tên bài hát hoặc nghệ sĩ..." onkeydown="if(event.key==='Enter')doScSearch()">
      <button class="sc-btn" id="scBtn" onclick="doScSearch()"><i class="fa-solid fa-magnifying-glass"></i> Tìm</button>
    </div>
    <div class="sc-loading" id="scLoading">
      <div class="spinner spinner-sm"></div> Đang tìm kiếm...
    </div>
    <div id="scResults" class="sc-results"></div>
    <!-- SC Player -->
    <div class="sc-player-wrap" id="scPlayerWrap">
      <div class="sc-player-card">
        <div class="sc-player-title"><i class="fa-brands fa-soundcloud" style="color:#ff5500;flex-shrink:0"></i> <span id="scPlayerTitle">—</span></div>
        <div class="sc-player-controls">
          <button class="sc-player-play" onclick="toggleSCPlay()"><i class="fa-solid fa-play" id="scPlayIcon"></i></button>
          <input type="range" class="sc-seek" id="scSeekBar" value="0" min="0" max="100" step="0.1" oninput="onScSeek(this.value)">
          <span class="sc-player-time" id="scTime">0:00</span>
          <input type="range" class="sc-player-vol" id="scVol" value="80" min="0" max="100" step="1" oninput="setScVol(this.value)" title="Âm lượng">
        </div>
        <audio id="scAudio"></audio>
      </div>
    </div>
  </div>

  <!-- Check Key (public) -->
  <div class="card">
    <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-shield-halved"></i></div> <span>Kiểm Tra Key</span></div>
    <div class="fg">
      <label>Nhập mã key cần kiểm tra</label>
      <input type="text" id="ckInput" placeholder="VD: FREE-ABC123 hoặc 7DAY-XYZ..." onkeydown="if(event.key==='Enter')doCheckKey()">
    </div>
    <button class="btn btn-primary" onclick="doCheckKey()"><i class="fa-solid fa-magnifying-glass"></i> Kiểm Tra</button>
    <div id="ckLoading" style="display:none;margin-top:12px"><div style="display:flex;align-items:center;gap:9px;color:var(--muted);font-size:.85rem"><div class="spinner spinner-sm"></div> Đang kiểm tra...</div></div>
    <div id="ckResult" class="checkkey-result"></div>
  </div>

</div><!-- end tab-home -->

<!-- ════ TAB: GETKEY ════ -->
<div id="tab-getkey" class="tab">
  <div class="getkey-card">
    <div class="getkey-hd">
      <div class="gh-icon"><i class="fa-solid fa-key"></i></div>
      <div class="gh-title">Nhận Key Miễn Phí</div>
      <div class="gh-sub">Hoàn thành link rút gọn để nhận key tự động</div>
    </div>
    <div class="getkey-info" id="getkeyInfoRow">
      <div class="getkey-info-box">
        <div class="gi-label"><i class="fa-solid fa-clock" style="color:var(--blue)"></i> Hạn Sử Dụng</div>
        <div class="gi-val" id="gkDuration">12</div>
        <div class="gi-unit" id="gkDurationUnit">Giờ</div>
      </div>
      <div class="getkey-info-box">
        <div class="gi-label"><i class="fa-solid fa-mobile-screen" style="color:var(--blue)"></i> Thiết Bị</div>
        <div class="gi-val" id="gkDevices">1</div>
        <div class="gi-unit">Thiết bị</div>
      </div>
    </div>
    <div class="getkey-limit"><i class="fa-solid fa-circle-info"></i> Giới hạn <strong>3 key</strong> mỗi IP trong 24 giờ. Qua 24h sẽ reset.</div>
    <button class="btn btn-primary" id="gkBtn" onclick="doGetKey()"><i class="fa-solid fa-link"></i> Tạo Link GetKey</button>
    <div id="gkLoading" style="display:none;margin-top:12px"><div style="display:flex;align-items:center;gap:9px;color:var(--muted);font-size:.85rem"><div class="spinner spinner-sm"></div> Đang tạo link...</div></div>
    <div id="gkResult" class="getkey-result"></div>
  </div>

  <div class="card">
    <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-circle-question"></i></div> <span>Hướng Dẫn Lấy Key</span></div>
    <div style="font-size:.84rem;color:var(--text2);line-height:1.75">
      <div style="display:flex;gap:9px;margin-bottom:8px;align-items:flex-start"><div style="width:22px;height:22px;border-radius:50%;background:var(--blue);color:#fff;font-size:.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">1</div><div>Nhấn <strong>Tạo Link GetKey</strong> ở trên</div></div>
      <div style="display:flex;gap:9px;margin-bottom:8px;align-items:flex-start"><div style="width:22px;height:22px;border-radius:50%;background:var(--blue);color:#fff;font-size:.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">2</div><div>Mở link rút gọn (Link4m) và <strong>hoàn thành quảng cáo</strong></div></div>
      <div style="display:flex;gap:9px;margin-bottom:8px;align-items:flex-start"><div style="width:22px;height:22px;border-radius:50%;background:var(--blue);color:#fff;font-size:.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">3</div><div>Hệ thống tự động <strong>cấp key miễn phí</strong> cho bạn</div></div>
      <div style="display:flex;gap:9px;align-items:flex-start"><div style="width:22px;height:22px;border-radius:50%;background:var(--blue);color:#fff;font-size:.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px">4</div><div>Copy key và dán vào phần mềm để sử dụng</div></div>
      <div style="margin-top:12px;padding:10px 13px;background:var(--amber-light);border:1px solid #fcd34d;border-radius:8px;font-size:.8rem;color:var(--amber)">
        <i class="fa-solid fa-triangle-exclamation"></i> <strong>Lưu ý:</strong> Không được dùng VPN/Proxy khi lấy key. Mỗi IP chỉ lấy tối đa 3 key/ngày.
      </div>
    </div>
  </div>
</div><!-- end tab-getkey -->

<!-- ════ TAB: ADMIN ════ -->
{% if session.get('is_admin') %}
<div id="tab-admin" class="tab">

  <!-- Admin nav tabs -->
  <div class="admin-tabs" id="adminTabs">
    <button class="admin-tab-btn active" id="at-home" onclick="sw_admin('home')"><i class="fa-solid fa-house"></i> Home</button>
    <button class="admin-tab-btn" id="at-taokhoa" onclick="sw_admin('taokhoa')"><i class="fa-solid fa-plus"></i> Tạo Key</button>
    <button class="admin-tab-btn" id="at-database" onclick="sw_admin('database')"><i class="fa-solid fa-database"></i> Keys</button>
    <button class="admin-tab-btn" id="at-checkkey" onclick="sw_admin('checkkey')"><i class="fa-solid fa-shield-halved"></i> Check</button>
    <button class="admin-tab-btn" id="at-keyfree" onclick="sw_admin('keyfree')"><i class="fa-solid fa-gift"></i> Free Key</button>
    <button class="admin-tab-btn" id="at-stats" onclick="sw_admin('stats')"><i class="fa-solid fa-chart-bar"></i> Stats</button>
    <button class="admin-tab-btn" id="at-security" onclick="sw_admin('security')"><i class="fa-solid fa-lock"></i> Bảo Mật</button>
    <button class="admin-tab-btn" id="at-devices" onclick="sw_admin('devices')"><i class="fa-solid fa-mobile-screen"></i> Thiết Bị</button>
    <button class="admin-tab-btn" id="at-weblogs" onclick="sw_admin('weblogs')"><i class="fa-solid fa-list-ul"></i> Nhật Ký</button>
    <button class="admin-tab-btn" id="at-settings" onclick="sw_admin('settings')"><i class="fa-solid fa-gear"></i> Settings</button>
  </div>

  <!-- ADMIN HOME -->
  <div id="at-content-home" class="admin-tab-content active">
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-circle-info"></i></div> <span>Thông Tin Admin</span></div>
      <div class="info-row"><span class="info-label">Tài khoản</span><span class="info-val badge badge-blue">{{ session.get('admin_user','Admin') }}</span></div>
      <div class="info-row"><span class="info-label">Trạng thái</span><span class="info-val badge badge-green">Đang đăng nhập</span></div>
      <div class="info-row" id="adminIPRow"><span class="info-label">IP của bạn</span><span class="info-val" id="adminIP"><div class="spinner spinner-sm"></div></span></div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-link"></i></div> <span>Mạng Xã Hội Admin</span></div>
      <a href="https://t.me/vkhanh3010" target="_blank" class="social-btn s-tg"><div class="s-icon"><i class="fa-brands fa-telegram"></i></div><div class="s-text"><span class="s-label">Liên hệ</span><span class="s-name">Telegram Admin</span></div><i class="fa-solid fa-chevron-right s-arrow"></i></a>
      <a href="https://www.tiktok.com/@midu.c2" target="_blank" class="social-btn s-tt"><div class="s-icon"><i class="fa-brands fa-tiktok"></i></div><div class="s-text"><span class="s-label">Follow</span><span class="s-name">Kênh TikTok</span></div><i class="fa-solid fa-chevron-right s-arrow"></i></a>
      <a href="https://youtube.com/@dokimodsgame" target="_blank" class="social-btn s-yt"><div class="s-icon"><i class="fa-brands fa-youtube"></i></div><div class="s-text"><span class="s-label">Subscribe</span><span class="s-name">YouTube DokiMods</span></div><i class="fa-solid fa-chevron-right s-arrow"></i></a>
      <a href="https://www.facebook.com/share/1ERXsth7Zr/" target="_blank" class="social-btn s-fb"><div class="s-icon"><i class="fa-brands fa-facebook-f"></i></div><div class="s-text"><span class="s-label">Theo dõi</span><span class="s-name">Facebook</span></div><i class="fa-solid fa-chevron-right s-arrow"></i></a>
    </div>
  </div>

  <!-- ADMIN TẠO KEY -->
  <div id="at-content-taokhoa" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-wand-magic-sparkles"></i></div> <span>Tạo Khóa Mới</span></div>
      <form id="createKeyForm">
        <div class="fg">
          <label>Kiểu tạo</label>
          <div class="radio-row">
            <label class="radio-opt"><input type="radio" name="mode" value="random" checked> Ngẫu nhiên</label>
            <label class="radio-opt"><input type="radio" name="mode" value="custom"> Tùy chỉnh</label>
          </div>
        </div>
        <div class="fg" id="customKeyFg" style="display:none">
          <label>Tên key tùy chỉnh</label>
          <input type="text" id="customKeyName" placeholder="VD: VIP-ABC123">
        </div>
        <div class="fg">
          <label>Thời hạn sử dụng</label>
          <div class="row2">
            <input type="number" id="keyVal" value="7" min="1" placeholder="Số lượng">
            <select id="keyUnit">
              <option value="phút">Phút</option>
              <option value="tiếng">Tiếng</option>
              <option value="ngày" selected>Ngày</option>
              <option value="tháng">Tháng</option>
              <option value="năm">Năm</option>
              <option value="permanent">Vĩnh viễn</option>
            </select>
          </div>
        </div>
        <div class="fg">
          <label>Số thiết bị</label>
          <input type="number" id="keyDev" value="1" min="1">
        </div>
        <div id="createKeyAlert" style="display:none;margin-bottom:10px"></div>
        <button type="button" class="btn btn-primary" id="createKeyBtn" onclick="doCreateKey()"><i class="fa-solid fa-circle-plus"></i> Tạo Khóa</button>
      </form>
    </div>
  </div>

  <!-- ADMIN DATABASE -->
  <div id="at-content-database" class="admin-tab-content">
    <div class="card" style="padding-bottom:0">
      <div class="card-hd" style="margin-bottom:12px"><div class="ic-blue ic-card"><i class="fa-solid fa-database"></i></div> <span>Quản Lý Keys</span>
        <button class="btn-sm btn-sm-blue" style="margin-left:auto" onclick="loadKeys()"><i class="fa-solid fa-rotate"></i> Làm mới</button>
      </div>
      <div class="fg" style="padding:0 0 14px">
        <input type="text" id="keySearch" placeholder="Tìm key..." oninput="filterKeys(this.value)" style="font-size:.84rem">
      </div>
      <div id="keyList"><div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div></div>
    </div>
  </div>

  <!-- ADMIN CHECK KEY -->
  <div id="at-content-checkkey" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-shield-halved"></i></div> <span>Kiểm Tra Key</span></div>
      <div class="fg">
        <label>Mã Key</label>
        <input type="text" id="adminCkInput" placeholder="Nhập mã key..." onkeydown="if(event.key==='Enter')doAdminCheckKey()">
      </div>
      <button class="btn btn-primary" onclick="doAdminCheckKey()"><i class="fa-solid fa-magnifying-glass"></i> Kiểm Tra</button>
      <div id="adminCkResult" style="margin-top:12px"></div>
    </div>
  </div>

  <!-- ADMIN KEY FREE -->
  <div id="at-content-keyfree" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-green ic-card"><i class="fa-solid fa-gift"></i></div> <span>Cấu Hình Key Free</span></div>
      <div class="fg">
        <label>Thời hạn mỗi key free</label>
        <div class="row2">
          <input type="number" id="freeVal" value="12" min="1">
          <select id="freeUnit">
            <option value="phút">Phút</option>
            <option value="tiếng" selected>Tiếng</option>
            <option value="ngày">Ngày</option>
            <option value="tháng">Tháng</option>
            <option value="năm">Năm</option>
          </select>
        </div>
      </div>
      <div class="fg">
        <label>Số thiết bị tối đa</label>
        <input type="number" id="freeDev" value="1" min="1">
      </div>
      <div id="freeCfgAlert" style="display:none;margin-bottom:10px"></div>
      <button class="btn btn-primary" onclick="saveFreeConfig()"><i class="fa-solid fa-floppy-disk"></i> Lưu cấu hình</button>
    </div>
    <div class="card">
      <div class="card-hd"><div class="ic-green ic-card"><i class="fa-solid fa-link"></i></div> <span>Tạo Link GetKey (Admin)</span></div>
      <p style="font-size:.83rem;color:var(--muted);margin-bottom:14px">Tạo link Link4m Admin — không cần timing/VPN check, key cấp ngay sau khi vượt link.</p>
      <button class="btn btn-primary" id="adminGenLinkBtn" onclick="adminGenLink()"><i class="fa-solid fa-link"></i> Tạo Link Link4m</button>
      <div id="adminGenLinkResult"></div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-globe"></i></div> <span>Quản Lý IP Key</span></div>
      <div class="fg">
        <label>Tìm kiếm theo IP</label>
        <div style="display:flex;gap:8px">
          <input type="text" id="adminIPSearch" placeholder="Nhập IP cần tra cứu...">
          <button class="btn-sm btn-sm-blue" onclick="adminSearchIP()"><i class="fa-solid fa-magnifying-glass"></i></button>
        </div>
      </div>
      <div id="adminIPResult"></div>
    </div>
  </div>

  <!-- ADMIN STATS -->
  <div id="at-content-stats" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-chart-bar"></i></div> <span>Thống Kê Key</span>
        <button class="btn-sm btn-sm-blue" style="margin-left:auto" onclick="loadStats()"><i class="fa-solid fa-rotate"></i></button>
      </div>
      <div id="statsContent"><div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div></div>
    </div>
  </div>

  <!-- ADMIN BẢO MẬT -->
  <div id="at-content-security" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-red ic-card"><i class="fa-solid fa-lock"></i></div> <span>Đổi Mật Khẩu Admin</span></div>
      <div class="fg"><label>Tài khoản mới</label><input type="text" id="newUser" placeholder="Nhập tài khoản mới..."></div>
      <div class="fg"><label>Mật khẩu mới</label><input type="password" id="newPass" placeholder="Nhập mật khẩu mới..."></div>
      <div id="chgPassAlert" style="display:none;margin-bottom:10px"></div>
      <button class="btn btn-primary" onclick="doChangePass()"><i class="fa-solid fa-shield-check"></i> Cập Nhật</button>
    </div>
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-book-open"></i></div> <span>API Endpoints</span></div>
      <div style="font-size:.8rem;color:var(--muted);line-height:1.8">
        <div><code style="background:#f1f5f9;padding:2px 7px;border-radius:5px;font-size:.78rem">POST /api/verify</code> — Xác thực key + hwid</div>
        <div><code style="background:#f1f5f9;padding:2px 7px;border-radius:5px;font-size:.78rem">POST /api/check_expiry</code> — Kiểm tra hạn (read-only)</div>
        <div><code style="background:#f1f5f9;padding:2px 7px;border-radius:5px;font-size:.78rem">POST /api/check-device</code> — Kiểm tra Device ID</div>
        <div><code style="background:#f1f5f9;padding:2px 7px;border-radius:5px;font-size:.78rem">GET /api/getkey</code> — Lấy link Link4m</div>
      </div>
    </div>
  </div>

  <!-- ADMIN THIẾT BỊ -->
  <div id="at-content-devices" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-purple ic-card"><i class="fa-solid fa-mobile-screen"></i></div> <span>Duyệt Thiết Bị</span>
        <button class="btn-sm btn-sm-blue" style="margin-left:auto" onclick="loadDeviceRequests()"><i class="fa-solid fa-rotate"></i></button>
      </div>
      <div id="devReqList"><div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div></div>
    </div>
    <div class="card">
      <div class="card-hd"><div class="ic-green ic-card"><i class="fa-solid fa-circle-plus"></i></div> <span>Thêm Thiết Bị Trực Tiếp</span></div>
      <div class="fg"><label>Device ID</label><input type="text" id="adminDeviceId" placeholder="Dán Device ID vào đây..."></div>
      <div class="fg">
        <label>Thời gian</label>
        <div class="row2">
          <input type="number" id="adminDevVal" value="7" min="1">
          <select id="adminDevUnit">
            <option value="phút">Phút</option>
            <option value="tiếng">Tiếng</option>
            <option value="ngày" selected>Ngày</option>
            <option value="tháng">Tháng</option>
            <option value="năm">Năm</option>
            <option value="permanent">Vĩnh viễn</option>
          </select>
        </div>
      </div>
      <div id="adminAddIDAlert" style="display:none;margin-bottom:10px"></div>
      <button class="btn btn-primary" onclick="doAdminAddID()"><i class="fa-solid fa-circle-plus"></i> Duyệt & Kích Hoạt Ngay</button>
    </div>
    <div class="card">
      <div class="card-hd"><div class="ic-green ic-card"><i class="fa-solid fa-check-double"></i></div> <span>Thiết Bị Đã Duyệt</span>
        <button class="btn-sm btn-sm-blue" style="margin-left:auto" onclick="loadApprovedDevices()"><i class="fa-solid fa-rotate"></i></button>
      </div>
      <div id="approvedDevList"><div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div></div>
    </div>
  </div>

  <!-- ADMIN WEB LOGS -->
  <div id="at-content-weblogs" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-amber ic-card"><i class="fa-solid fa-list-ul"></i></div> <span>Nhật Ký Truy Cập Web</span>
        <div style="margin-left:auto;display:flex;gap:6px">
          <button class="btn-sm btn-sm-blue" onclick="loadWebLogs()"><i class="fa-solid fa-rotate"></i> Làm mới</button>
          <button class="btn-sm btn-sm-red" onclick="clearWebLogs()"><i class="fa-solid fa-trash"></i> Xóa</button>
        </div>
      </div>
      <div style="margin-bottom:10px;font-size:.78rem;color:var(--muted)">Hiển thị 200 dòng mới nhất • Tổng: <span id="logTotal">—</span> dòng</div>
      <div class="log-container" id="logContainer">
        <div class="empty-state" style="color:#475569"><div class="spinner" style="margin:0 auto 10px;border-top-color:#60a5fa"></div>Đang tải nhật ký...</div>
      </div>
    </div>
  </div>

  <!-- ADMIN SETTINGS -->
  <div id="at-content-settings" class="admin-tab-content">
    <div class="card">
      <div class="card-hd"><div class="ic-blue ic-card"><i class="fa-solid fa-gear"></i></div> <span>Settings API</span></div>
      <div style="font-size:.84rem;color:var(--text2);line-height:1.8">
        <p style="margin-bottom:12px">Các endpoint để tích hợp với tool/game:</p>
        <div style="background:#0f172a;border-radius:10px;padding:14px;font-family:monospace;font-size:.76rem;color:#94a3b8;line-height:1.8">
          <div><span style="color:#60a5fa">POST</span> <span style="color:#34d399">/api/verify</span></div>
          <div style="color:#475569;margin-left:12px">body: key=... &amp; hwid=...</div>
          <br>
          <div><span style="color:#60a5fa">POST</span> <span style="color:#34d399">/api/check_expiry</span></div>
          <div style="color:#475569;margin-left:12px">body: key=... &amp; hwid=...</div>
          <br>
          <div><span style="color:#60a5fa">POST</span> <span style="color:#34d399">/api/check-device</span></div>
          <div style="color:#475569;margin-left:12px">body: device_id=...</div>
          <br>
          <div><span style="color:#60a5fa">GET</span> <span style="color:#34d399">/api/getkey</span></div>
          <div style="color:#475569;margin-left:12px">returns: link (Link4m)</div>
        </div>
      </div>
    </div>
  </div>

</div><!-- end tab-admin -->
{% endif %}

</div><!-- end main -->

<!-- ════ LOGIN MODAL ════ -->
<div class="modal-overlay hidden" id="loginModal" onclick="if(event.target===this)closeLoginModal()">
  <div class="modal-card">
    <div class="modal-icon"><i class="fa-solid fa-shield-halved"></i></div>
    <div class="modal-title">Đăng Nhập Admin</div>
    <div class="modal-sub">Nhập thông tin quản trị để tiếp tục</div>
    <div id="loginErr" style="display:none;margin-bottom:12px;padding:10px 13px;background:var(--red-light);border:1px solid #fca5a5;color:var(--red);border-radius:9px;font-size:.84rem;font-weight:600"></div>
    <div id="loginSpinner" style="display:none;text-align:center;padding:12px"><div class="spinner" style="margin:auto"></div></div>
    <form id="loginForm">
      <div class="fg"><label>Tài khoản</label><input type="text" id="lu" required placeholder="Nhập tài khoản" autocomplete="username"></div>
      <div class="fg"><label>Mật khẩu</label><input type="password" id="lp" required placeholder="Nhập mật khẩu" autocomplete="current-password"></div>
      <button type="submit" class="btn btn-primary"><i class="fa-solid fa-right-to-bracket"></i> Đăng Nhập</button>
      <button type="button" class="btn btn-outline" style="margin-top:8px" onclick="closeLoginModal()">Hủy</button>
    </form>
  </div>
</div>

<script>
// ══ PAGE LOADER ══
window.addEventListener('load', function() {
  setTimeout(function() {
    var loader = document.getElementById('pageLoader');
    if (loader) loader.classList.add('hidden');
  }, 1800);
});

// ══ NAVIGATION ══
function sw(tab) {
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l=>l.classList.remove('active'));
  var el = document.getElementById('tab-'+tab);
  if(el) el.classList.add('active');
  var nl = document.getElementById('nl-'+tab);
  if(nl) nl.classList.add('active');
  if(tab==='admin' && document.getElementById('at-content-database')?.classList.contains('active')) loadKeys();
  if(tab==='admin' && document.getElementById('at-content-stats')?.classList.contains('active')) loadStats();
}

function sw_admin(sub) {
  document.querySelectorAll('.admin-tab-content').forEach(c=>c.classList.remove('active'));
  document.querySelectorAll('.admin-tab-btn').forEach(b=>b.classList.remove('active'));
  var c = document.getElementById('at-content-'+sub);
  var b = document.getElementById('at-'+sub);
  if(c) c.classList.add('active');
  if(b) b.classList.add('active');
  if(sub==='database') loadKeys();
  if(sub==='stats') loadStats();
  if(sub==='devices') { loadDeviceRequests(); loadApprovedDevices(); }
  if(sub==='weblogs') loadWebLogs();
  if(sub==='keyfree') loadFreeConfig();
  if(sub==='home') scanAdminIP();
}

// ══ MOBILE MENU (RIGHT SIDE) ══
function toggleMobileMenu() {
  var btn = document.getElementById('hbgBtn');
  var menu = document.getElementById('mobileMenu');
  var overlay = document.getElementById('mobileOverlay');
  btn.classList.toggle('open');
  menu.classList.toggle('open');
  overlay.classList.toggle('open');
  document.body.style.overflow = menu.classList.contains('open') ? 'hidden' : '';
}
function closeMobileMenu() {
  document.getElementById('hbgBtn').classList.remove('open');
  document.getElementById('mobileMenu').classList.remove('open');
  document.getElementById('mobileOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

// ══ ADMIN IP SCAN ══
function scanAdminIP() {
  var el = document.getElementById('adminIP');
  if(!el) return;
  el.innerHTML = '<div class="spinner spinner-sm" style="display:inline-block"></div>';
  fetch('https://get.geojs.io/v1/ip/geo.json')
  .then(r=>r.json()).then(d=>{
    el.innerHTML = '<span style="color:var(--blue);font-family:monospace">'+(d.ip||'—')+'</span> <span style="color:var(--muted);font-size:.78rem">('+translateCountry(d.country)+')</span>';
  }).catch(()=>{ el.textContent='Không thể quét'; });
}
function translateCountry(c) {
  var m={'Vietnam':'Việt Nam','United States':'Hoa Kỳ','China':'Trung Quốc','Japan':'Nhật Bản','South Korea':'Hàn Quốc','Singapore':'Singapore'};
  return m[c]||c||'—';
}

// ══ TOAST ══
function showToast(msg, type, dur) {
  type = type||'info'; dur = dur||3500;
  var c = document.getElementById('toastContainer');
  var d = document.createElement('div');
  var icons = {success:'fa-circle-check',error:'fa-circle-xmark',info:'fa-circle-info',warn:'fa-triangle-exclamation'};
  d.className = 'toast t-'+type;
  d.innerHTML = '<i class="fa-solid '+icons[type]+'"></i><span>'+msg+'</span>';
  c.appendChild(d);
  setTimeout(function(){ d.style.animation='toastOut .3s ease forwards'; setTimeout(function(){d.remove();},300); },dur);
}

// ══ COPY ══
function copyText(txt, btn) {
  navigator.clipboard.writeText(txt).then(function(){
    var orig = btn ? btn.innerHTML : '';
    if(btn){ btn.innerHTML='<i class="fa-solid fa-check"></i> Đã copy'; setTimeout(function(){btn.innerHTML=orig;},1500); }
    showToast('Đã sao chép!','success',1800);
  }).catch(function(){ prompt('Sao chép thủ công:',txt); });
}

// ══ FORMAT HELPERS ══
function fmtTime(s) {
  if(isNaN(s)||s<0) return '0:00';
  var m = Math.floor(s/60), sec=Math.floor(s%60);
  return m+':'+(sec<10?'0':'')+sec;
}
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

// ══ VIP MUSIC PLAYER ══
var tracks = ['/nhac.mp3','/nhac2.mp3','/nhac3.mp3'];
var trackNames = ['Nhạc Nền 1','Nhạc Nền 2','Nhạc Nền 3'];
var curTrack = 0, musicPlaying = false;
var audio = document.getElementById('bgAudio');
var seekBar = document.getElementById('seekBar');

function selectTrack(n) {
  curTrack = n;
  document.querySelectorAll('.track-btn').forEach(function(b,i){b.classList.toggle('playing',i===n);});
  audio.src = tracks[n];
  document.getElementById('mTitle').textContent = trackNames[n];
  audio.load();
  if(musicPlaying) { audio.play().catch(function(){}); }
}

function toggleMusic() {
  if(musicPlaying) {
    audio.pause(); musicPlaying=false;
    document.getElementById('playIcon').className='fa-solid fa-play';
    document.getElementById('vinylEl').classList.remove('spin');
    document.getElementById('mStatus').textContent='Đang dừng';
    document.getElementById('statusDot').classList.remove('playing');
  } else {
    audio.play().then(function(){
      musicPlaying=true;
      document.getElementById('playIcon').className='fa-solid fa-pause';
      document.getElementById('vinylEl').classList.add('spin');
      document.getElementById('mStatus').textContent='Đang phát...';
      document.getElementById('statusDot').classList.add('playing');
    }).catch(function(){showToast('Không thể phát nhạc','error');});
  }
}

function prevTrack() { selectTrack((curTrack-1+3)%3); if(musicPlaying) audio.play().catch(function(){}); }
function nextTrack() { selectTrack((curTrack+1)%3); if(musicPlaying) audio.play().catch(function(){}); }
function seekBack() { audio.currentTime = Math.max(0, audio.currentTime-10); }
function seekFwd() { audio.currentTime = Math.min(audio.duration||0, audio.currentTime+10); }
function onSeekInput(v) { audio.currentTime = (v/100)*(audio.duration||0); }
function setVol(v) { audio.volume = v/100; }

audio.addEventListener('timeupdate', function(){
  if(!audio.duration) return;
  seekBar.value = (audio.currentTime/audio.duration)*100;
  document.getElementById('curTime').textContent = fmtTime(audio.currentTime);
  document.getElementById('durTime').textContent = fmtTime(audio.duration);
});
audio.addEventListener('ended', function(){
  // Auto play next track
  selectTrack((curTrack+1)%3);
  audio.play().catch(function(){});
});

// ══ SOUNDCLOUD SEARCH ══
var scAudio = document.getElementById('scAudio');
var scPlaying = false;

function doScSearch() {
  var q = document.getElementById('scQuery').value.trim();
  if(!q) { showToast('Vui lòng nhập từ khóa','warn'); return; }
  var btn = document.getElementById('scBtn');
  btn.disabled = true;
  document.getElementById('scLoading').style.display='flex';
  var resultsEl = document.getElementById('scResults');
  resultsEl.innerHTML='';
  resultsEl.classList.remove('show');
  document.getElementById('scPlayerWrap').classList.remove('show');
  fetch('/api/search_music?q='+encodeURIComponent(q))
  .then(function(r){return r.json();})
  .then(function(d){
    btn.disabled=false;
    document.getElementById('scLoading').style.display='none';
    var results = d.results||[];
    if(!results.length) {
      resultsEl.innerHTML='<div style="text-align:center;padding:16px;color:var(--muted);font-size:.85rem"><i class="fa-solid fa-music" style="font-size:1.5rem;display:block;margin-bottom:8px;opacity:.3"></i>Không tìm thấy kết quả. Thử từ khóa khác!</div>';
      resultsEl.classList.add('show');
      return;
    }
    var html = '';
    results.forEach(function(r, i) {
      var coverHtml = '';
      if(r.cover && r.cover.length > 0 && !r.cover.startsWith('data:')) {
        coverHtml = '<div class="sc-cover-wrap"><img class="sc-cover" src="'+escHtml(r.cover)+'" alt="" loading="lazy" onerror="this.parentNode.innerHTML=\'<div class=\\\"sc-cover-ph\\\"><i class=\\\"fa-solid fa-music\\\"></i></div>\'"></div>';
      } else {
        coverHtml = '<div class="sc-cover-wrap"><div class="sc-cover-ph"><i class="fa-solid fa-music"></i></div></div>';
      }
      var dur = r.duration ? ' • '+fmtTime(r.duration/1000) : '';
      var user = r.user ? escHtml(r.user)+dur : dur;
      html += '<div class="sc-result-item" id="scr'+i+'" onclick="loadScTrack('+i+','+JSON.stringify(r.title)+','+JSON.stringify(r.url)+','+JSON.stringify(r.cover||'')+')">'+
        coverHtml+
        '<div class="sc-track-info">'+
          '<div class="sc-track-title">'+escHtml(r.title)+'</div>'+
          (user?'<div class="sc-track-meta"><i class="fa-solid fa-user" style="font-size:.65rem"></i>'+user+'</div>':'')+
          '<div class="sc-play-hint"><i class="fa-solid fa-play" style="font-size:.6rem"></i> Nhấn để phát</div>'+
        '</div>'+
      '</div>';
    });
    resultsEl.innerHTML = html;
    resultsEl.classList.add('show');
  })
  .catch(function(){
    btn.disabled=false;
    document.getElementById('scLoading').style.display='none';
    showToast('Lỗi tìm kiếm nhạc','error');
  });
}

function loadScTrack(i, title, url, cover) {
  document.querySelectorAll('.sc-result-item').forEach(function(el){el.classList.remove('selected');});
  var el = document.getElementById('scr'+i);
  if(el) el.classList.add('selected');
  document.getElementById('scPlayerTitle').textContent = title||'—';
  document.getElementById('scPlayerWrap').classList.add('show');
  document.getElementById('scPlayIcon').className='fa-solid fa-spinner fa-spin';
  scAudio.pause(); scPlaying=false;
  fetch('/api/get_stream?url='+encodeURIComponent(url))
  .then(function(r){return r.json();})
  .then(function(d){
    document.getElementById('scPlayIcon').className='fa-solid fa-play';
    if(d.stream_url) {
      scAudio.src = d.stream_url;
      scAudio.volume = (document.getElementById('scVol').value||80)/100;
      scAudio.play().then(function(){
        scPlaying=true;
        document.getElementById('scPlayIcon').className='fa-solid fa-pause';
      }).catch(function(){ showToast('Không thể phát bài này','error'); });
    } else {
      showToast(d.error||'Không lấy được link stream','error');
    }
  })
  .catch(function(){ document.getElementById('scPlayIcon').className='fa-solid fa-play'; showToast('Lỗi kết nối server','error'); });
}

function toggleSCPlay() {
  if(scPlaying) { scAudio.pause(); scPlaying=false; document.getElementById('scPlayIcon').className='fa-solid fa-play'; }
  else { scAudio.play().then(function(){ scPlaying=true; document.getElementById('scPlayIcon').className='fa-solid fa-pause'; }).catch(function(){}); }
}
function setScVol(v) { scAudio.volume=v/100; }
function onScSeek(v) { scAudio.currentTime=(v/100)*(scAudio.duration||0); }
scAudio.addEventListener('timeupdate', function(){
  if(!scAudio.duration) return;
  document.getElementById('scSeekBar').value=(scAudio.currentTime/scAudio.duration)*100;
  document.getElementById('scTime').textContent=fmtTime(scAudio.currentTime);
});
scAudio.addEventListener('ended', function(){ scPlaying=false; document.getElementById('scPlayIcon').className='fa-solid fa-play'; });

// ══ CHECK KEY PUBLIC ══
function doCheckKey() {
  var k = document.getElementById('ckInput').value.trim();
  if(!k) { showToast('Vui lòng nhập mã key','warn'); return; }
  document.getElementById('ckLoading').style.display='block';
  document.getElementById('ckResult').className='checkkey-result';
  document.getElementById('ckResult').innerHTML='';
  fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'key='+encodeURIComponent(k)})
  .then(function(r){return r.json();})
  .then(function(d){
    document.getElementById('ckLoading').style.display='none';
    var r = document.getElementById('ckResult');
    r.className='checkkey-result show';
    if(!d.exists) {
      r.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>'+(d.msg||'Key không tồn tại!')+'</div>';
      return;
    }
    var stColor = d.key_status==='Đã kích hoạt'?'badge-green':(d.key_status==='Hết hạn'?'badge-red':'badge-amber');
    r.innerHTML='<div style="margin-top:4px"><div class="ckr-grid">'+
      '<div class="ckr-box full"><div class="ck-label">Mã Key</div><div class="ck-val" style="font-family:monospace;font-size:.85rem">'+escHtml(d.key)+'</div></div>'+
      '<div class="ckr-box"><div class="ck-label">Trạng Thái</div><div class="ck-val"><span class="badge '+stColor+'">'+d.key_status+'</span></div></div>'+
      '<div class="ckr-box"><div class="ck-label">Hạn Sử Dụng</div><div class="ck-val">'+escHtml(d.duration)+'</div></div>'+
      '<div class="ckr-box"><div class="ck-label">Thiết Bị</div><div class="ck-val">'+d.used_devices+'/'+d.max_devices+'</div></div>'+
      '<div class="ckr-box"><div class="ck-label">Ngày Tạo</div><div class="ck-val" style="font-size:.78rem">'+escHtml(d.created_at)+'</div></div>'+
      '<div class="ckr-box full"><div class="ck-label">Kích Hoạt</div><div class="ck-val" style="font-size:.78rem">'+escHtml(d.activated_time)+'</div></div>'+
    '</div></div>';
  })
  .catch(function(){ document.getElementById('ckLoading').style.display='none'; showToast('Lỗi kết nối server','error'); });
}

// ══ GETKEY ══
(function loadGetKeyConfig() {
  fetch('/api/getkey_public_config').then(function(r){return r.json();}).then(function(d){
    document.getElementById('gkDuration').textContent = d.val||'12';
    var unitMap = {'phút':'Phút','tiếng':'Giờ','ngày':'Ngày','tháng':'Tháng','năm':'Năm'};
    document.getElementById('gkDurationUnit').textContent = unitMap[d.unit]||d.unit||'Giờ';
    document.getElementById('gkDevices').textContent = d.dev||'1';
  }).catch(function(){});
})();

function doGetKey() {
  var btn = document.getElementById('gkBtn');
  btn.disabled=true;
  document.getElementById('gkLoading').style.display='block';
  document.getElementById('gkResult').className='getkey-result';
  document.getElementById('gkResult').innerHTML='';
  fetch('/api/getkey')
  .then(function(r){return r.json();})
  .then(function(d){
    btn.disabled=false;
    document.getElementById('gkLoading').style.display='none';
    var r = document.getElementById('gkResult');
    if(d.status==='success') {
      r.className='getkey-result show';
      r.innerHTML='<div style="background:var(--green-light);border:1.5px solid #86efac;border-radius:12px;padding:16px;text-align:center">'+
        '<div style="display:flex;justify-content:center;margin-bottom:10px"><div class="anim-success"><svg width="28" height="28" viewBox="0 0 24 24"><polyline points="20,6 9,17 4,12" class="check-circle"/></svg></div></div>'+
        '<div style="font-weight:700;color:var(--green);margin-bottom:6px">Link đã tạo thành công!</div>'+
        '<div style="font-size:.78rem;color:var(--muted);margin-bottom:12px">Mở link bên dưới, hoàn thành quảng cáo để nhận key</div>'+
        '<div style="background:#fff;border:1px solid #86efac;border-radius:8px;padding:10px 12px;font-family:monospace;font-size:.82rem;color:var(--blue);word-break:break-all;margin-bottom:10px">'+escHtml(d.link)+'</div>'+
        '<div style="display:flex;gap:8px;justify-content:center">'+
          '<button class="btn-sm btn-sm-green" onclick="copyText('+JSON.stringify(d.link)+',this)"><i class="fa-solid fa-copy"></i> Sao chép</button>'+
          '<a href="'+escHtml(d.link)+'" target="_blank" class="btn-sm btn-sm-blue"><i class="fa-solid fa-external-link"></i> Mở link</a>'+
        '</div></div>';
    } else {
      r.className='getkey-result show';
      r.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>'+escHtml(d.message||'Không tạo được link. Thử lại!')+'</div>';
    }
  })
  .catch(function(){
    btn.disabled=false;
    document.getElementById('gkLoading').style.display='none';
    showToast('Lỗi kết nối server','error');
  });
}

// ══ LOGIN MODAL ══
function openLoginModal() {
  document.getElementById('loginModal').classList.remove('hidden');
  setTimeout(function(){ document.getElementById('lu').focus(); }, 100);
}
function closeLoginModal() {
  document.getElementById('loginModal').classList.add('hidden');
}
document.getElementById('loginForm').addEventListener('submit', function(e) {
  e.preventDefault();
  var u=document.getElementById('lu').value.trim();
  var p=document.getElementById('lp').value.trim();
  if(!u||!p) return;
  var err=document.getElementById('loginErr');
  var spin=document.getElementById('loginSpinner');
  err.style.display='none';
  spin.style.display='block';
  this.querySelector('button[type=submit]').disabled=true;
  fetch('/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'user='+encodeURIComponent(u)+'&pass='+encodeURIComponent(p)})
  .then(function(r){return r.json();})
  .then(function(d){
    spin.style.display='none';
    if(d.status==='success') { window.location.reload(); }
    else {
      err.style.display='block';
      err.textContent = d.message||'Sai tài khoản hoặc mật khẩu!';
      document.getElementById('loginForm').querySelector('button[type=submit]').disabled=false;
    }
  })
  .catch(function(){ spin.style.display='none'; err.style.display='block'; err.textContent='Lỗi kết nối server!'; document.getElementById('loginForm').querySelector('button[type=submit]').disabled=false; });
});

// ══ ADMIN: CREATE KEY ══
function doCreateKey() {
  var mode = document.querySelector('input[name="mode"]:checked')?.value||'random';
  var v = document.getElementById('keyVal').value.trim();
  var u = document.getElementById('keyUnit').value;
  var d = document.getElementById('keyDev').value.trim();
  var c = document.getElementById('customKeyName')?.value?.trim()||'';
  if(u!=='permanent' && (!v||isNaN(parseInt(v))||parseInt(v)<1)) { showToast('Nhập thời gian hợp lệ','warn'); return; }
  var btn=document.getElementById('createKeyBtn');
  btn.disabled=true; btn.innerHTML='<div class="spinner spinner-sm spinner-white"></div> Đang tạo...';
  var alert2=document.getElementById('createKeyAlert'); alert2.style.display='none';
  var body='mode='+mode+'&v='+encodeURIComponent(v)+'&u='+encodeURIComponent(u)+'&d='+encodeURIComponent(d)+'&c_key='+encodeURIComponent(c);
  fetch('/admin',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body})
  .then(function(r){return r.json();})
  .then(function(d2){
    btn.disabled=false; btn.innerHTML='<i class="fa-solid fa-circle-plus"></i> Tạo Khóa';
    if(d2.status==='success') {
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-success show"><i class="fa-solid fa-circle-check"></i> Tạo thành công! Key: <strong style="font-family:monospace">'+escHtml(d2.key)+'</strong> <button class="btn-sm btn-sm-green" onclick="copyText(\''+d2.key.replace(/\'/g,"\\'")+'\'  ,this)" style="margin-left:6px"><i class="fa-solid fa-copy"></i></button></div>';
    } else {
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>'+(d2.message||'Lỗi hệ thống')+'</div>';
    }
  })
  .catch(function(){ btn.disabled=false; btn.innerHTML='<i class="fa-solid fa-circle-plus"></i> Tạo Khóa'; showToast('Lỗi kết nối','error'); });
}

// ══ ADMIN: LOAD KEYS ══
var allKeys = [];
function loadKeys() {
  var el=document.getElementById('keyList');
  if(!el) return;
  el.innerHTML='<div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div>';
  fetch('/api/list_keys').then(function(r){return r.json();}).then(function(data){
    allKeys=data; renderKeys(data);
  }).catch(function(){ el.innerHTML='<div class="empty-state" style="color:var(--red)"><i class="fa-solid fa-triangle-exclamation"></i>Lỗi tải dữ liệu</div>'; });
}
function filterKeys(q) {
  renderKeys(allKeys.filter(function(k){return k.key.toLowerCase().includes(q.toLowerCase());}));
}
function renderKeys(data) {
  var el=document.getElementById('keyList');
  if(!data.length) { el.innerHTML='<div class="empty-state"><i class="fa-solid fa-inbox"></i>Chưa có key nào</div>'; return; }
  var h='<div style="display:flex;flex-direction:column;gap:8px">';
  data.forEach(function(k){
    var stClass=k.status==='Đã kích hoạt'?'badge-green':(k.status==='Hết hạn'?'badge-red':'badge-amber');
    var typeClass=k.is_free?'badge-purple':'badge-blue';
    h+='<div style="background:#fff;border:1.5px solid var(--border);border-radius:12px;padding:13px">'+
      '<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:9px">'+
        '<div style="flex:1;min-width:0"><div style="font-family:monospace;font-weight:800;font-size:.82rem;color:var(--text);word-break:break-all">'+escHtml(k.key)+'</div><div style="font-size:.72rem;color:var(--muted);margin-top:3px">'+escHtml(k.created_at_str)+'</div></div>'+
        '<div style="display:flex;gap:4px;flex-shrink:0;flex-wrap:wrap"><span class="badge '+stClass+'">'+k.status+'</span><span class="badge '+typeClass+'">'+(k.is_free?'Free':'VIP')+'</span></div>'+
      '</div>'+
      '<div style="display:flex;gap:10px;font-size:.78rem;color:var(--muted);margin-bottom:9px;flex-wrap:wrap">'+
        '<span><i class="fa-solid fa-clock" style="color:var(--blue)"></i> '+escHtml(k.han_dung)+'</span>'+
        '<span><i class="fa-solid fa-mobile-screen" style="color:var(--purple)"></i> '+escHtml(k.thiet_bi)+'</span>'+
        '<span><i class="fa-solid fa-calendar" style="color:var(--muted)"></i> '+k.age_hours+'h</span>'+
      '</div>'+
      '<div class="td-actions">'+
        '<button class="btn-sm btn-sm-blue" onclick="copyText(\''+k.key.replace(/\'/g,"\\'")+'\',this)"><i class="fa-solid fa-copy"></i> Copy</button>'+
        '<button class="btn-sm btn-sm-amber" onclick="doResetKey(\''+k.key.replace(/\'/g,"\\'")+'\')"><i class="fa-solid fa-rotate"></i> Reset</button>'+
        '<button class="btn-sm btn-sm-red" onclick="doDeleteKey(\''+k.key.replace(/\'/g,"\\'")+'\')"><i class="fa-solid fa-trash"></i> Xóa</button>'+
      '</div>'+
    '</div>';
  });
  h+='</div>';
  el.innerHTML=h;
}
function doDeleteKey(k) {
  if(!confirm('Xóa key: '+k+'?')) return;
  fetch('/delete/'+encodeURIComponent(k)).then(function(r){return r.json();}).then(function(){ loadKeys(); showToast('Đã xóa key','success'); });
}
function doResetKey(k) {
  if(!confirm('Reset key: '+k+'?')) return;
  fetch('/reset/'+encodeURIComponent(k)).then(function(r){return r.json();}).then(function(){ loadKeys(); showToast('Đã reset key','success'); });
}

// ══ ADMIN: STATS ══
function loadStats() {
  var el=document.getElementById('statsContent');
  if(!el) return;
  el.innerHTML='<div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div>';
  fetch('/api/key_stats').then(function(r){return r.json();}).then(function(d){
    el.innerHTML='<div class="stats-grid">'+
      '<div class="stat-box"><div class="s-num s-blue">'+d.total+'</div><div class="s-label">Tổng Keys</div></div>'+
      '<div class="stat-box"><div class="s-num s-green">'+d.activated+'</div><div class="s-label">Đã Kích Hoạt</div></div>'+
      '<div class="stat-box"><div class="s-num s-red">'+d.expired+'</div><div class="s-label">Hết Hạn</div></div>'+
      '<div class="stat-box"><div class="s-num s-amber">'+d.not_activated+'</div><div class="s-label">Chưa Kích Hoạt</div></div>'+
      '<div class="stat-box"><div class="s-num s-purple">'+d.free_total+'</div><div class="s-label">Keys Free</div></div>'+
      '<div class="stat-box"><div class="s-num s-blue">'+d.total_bypasses+'</div><div class="s-label">Lượt Tạo Link</div></div>'+
    '</div>';
  }).catch(function(){ el.innerHTML='<div class="empty-state" style="color:var(--red)">Lỗi tải stats</div>'; });
}

// ══ ADMIN: CHECK KEY ══
function doAdminCheckKey() {
  var k=document.getElementById('adminCkInput').value.trim();
  if(!k) return;
  var el=document.getElementById('adminCkResult');
  el.innerHTML='<div class="spinner spinner-sm" style="display:inline-block"></div>';
  fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'key='+encodeURIComponent(k)})
  .then(function(r){return r.json();})
  .then(function(d){
    if(!d.exists){ el.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>'+(d.msg||'Key không tồn tại!')+'</div>'; return; }
    var stClass=d.key_status==='Đã kích hoạt'?'badge-green':(d.key_status==='Hết hạn'?'badge-red':'badge-amber');
    el.innerHTML='<div class="ckr-grid" style="margin-top:8px">'+
      '<div class="ckr-box full"><div class="ck-label">Mã Key</div><div class="ck-val" style="font-family:monospace">'+escHtml(d.key)+'</div></div>'+
      '<div class="ckr-box"><div class="ck-label">Trạng Thái</div><div class="ck-val"><span class="badge '+stClass+'">'+d.key_status+'</span></div></div>'+
      '<div class="ckr-box"><div class="ck-label">Hạn Sử Dụng</div><div class="ck-val">'+escHtml(d.duration)+'</div></div>'+
      '<div class="ckr-box"><div class="ck-label">Thiết Bị</div><div class="ck-val">'+d.used_devices+'/'+d.max_devices+'</div></div>'+
      '<div class="ckr-box full"><div class="ck-label">Kích Hoạt</div><div class="ck-val" style="font-size:.78rem">'+escHtml(d.activated_time)+'</div></div>'+
    '</div>';
  })
  .catch(function(){ el.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>Lỗi kết nối</div>'; });
}

// ══ ADMIN: FREE CONFIG ══
function loadFreeConfig() {
  fetch('/admin/get_free_config').then(function(r){return r.json();}).then(function(d){
    if(d.status==='success') {
      document.getElementById('freeVal').value=d.val||'12';
      document.getElementById('freeUnit').value=d.unit||'tiếng';
      document.getElementById('freeDev').value=d.dev||'1';
    }
  }).catch(function(){});
}
function saveFreeConfig() {
  var v=document.getElementById('freeVal').value;
  var u=document.getElementById('freeUnit').value;
  var d=document.getElementById('freeDev').value;
  var alert2=document.getElementById('freeCfgAlert'); alert2.style.display='none';
  fetch('/admin/free_setup',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'v='+v+'&u='+encodeURIComponent(u)+'&d='+d})
  .then(function(r){return r.json();}).then(function(d2){
    if(d2.status==='success'){
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-success show"><i class="fa-solid fa-circle-check"></i> Đã lưu cấu hình thành công!</div>';
      setTimeout(function(){alert2.style.display='none';},3000);
    }
  }).catch(function(){ showToast('Lỗi lưu cấu hình','error'); });
}

// ══ ADMIN: GEN LINK ══
function adminGenLink() {
  var btn=document.getElementById('adminGenLinkBtn');
  btn.disabled=true; btn.innerHTML='<div class="spinner spinner-sm spinner-white"></div> Đang tạo...';
  var res=document.getElementById('adminGenLinkResult'); res.innerHTML='';
  fetch('/admin/gen_key_link',{method:'POST'})
  .then(function(r){return r.json();}).then(function(d){
    btn.disabled=false; btn.innerHTML='<i class="fa-solid fa-link"></i> Tạo Link Link4m';
    if(d.status==='success') {
      res.innerHTML='<div class="free-link-box"><div class="free-link-label"><i class="fa-solid fa-link"></i> Link Link4m Admin</div>'+
        '<input class="free-link-input" readonly value="'+escHtml(d.link)+'">'+
        '<div style="display:flex;gap:7px">'+
          '<button class="btn-sm btn-sm-blue" onclick="copyText(\''+d.link.replace(/\'/g,"\\'")+'\',this)"><i class="fa-solid fa-copy"></i> Sao chép</button>'+
          '<a href="'+escHtml(d.link)+'" target="_blank" class="btn-sm btn-sm-green"><i class="fa-solid fa-external-link"></i> Mở link</a>'+
        '</div></div>';
    } else {
      res.innerHTML='<div class="alert alert-error show" style="margin-top:10px"><i class="fa-solid fa-circle-xmark"></i>'+escHtml(d.message||'Lỗi tạo link')+'</div>';
    }
  }).catch(function(){ btn.disabled=false; btn.innerHTML='<i class="fa-solid fa-link"></i> Tạo Link Link4m'; showToast('Lỗi kết nối','error'); });
}

// ══ ADMIN: IP SEARCH ══
function adminSearchIP() {
  var ip=document.getElementById('adminIPSearch').value.trim();
  if(!ip) return;
  var el=document.getElementById('adminIPResult');
  el.innerHTML='<div style="display:flex;align-items:center;gap:8px;padding:10px;color:var(--muted);font-size:.83rem"><div class="spinner spinner-sm"></div>Đang tra cứu...</div>';
  fetch('https://get.geojs.io/v1/ip/geo/'+encodeURIComponent(ip)+'.json')
  .then(function(r){return r.json();}).then(function(geo){
    var country=translateCountry(geo.country);
    var lat=geo.latitude||''; var lng=geo.longitude||'';
    var mapLink=lat&&lng?'<a href="https://www.google.com/maps?q='+lat+','+lng+'" target="_blank" class="btn-sm btn-sm-blue" style="margin-top:8px;display:inline-flex"><i class="fa-solid fa-map-location-dot"></i> Xem bản đồ</a>':'';
    el.innerHTML='<div class="ip-info-grid" style="margin-top:10px">'+
      '<div class="ip-cell full"><div class="ic-label">Địa Chỉ IP</div><div class="ic-val" style="color:var(--blue);font-family:monospace">'+(geo.ip||ip)+'</div></div>'+
      '<div class="ip-cell"><div class="ic-label">Quốc Gia</div><div class="ic-val">'+country+'</div></div>'+
      '<div class="ip-cell"><div class="ic-label">Thành Phố</div><div class="ic-val">'+(geo.city||'—')+'</div></div>'+
      '<div class="ip-cell full"><div class="ic-label">Nhà Mạng</div><div class="ic-val" style="color:var(--blue)">'+(geo.organization_name||geo.org||'—')+'</div></div>'+
      (lat&&lng?'<div class="ip-cell"><div class="ic-label">Vĩ Độ</div><div class="ic-val">'+lat+'</div></div><div class="ip-cell"><div class="ic-label">Kinh Độ</div><div class="ic-val">'+lng+'</div></div>':'')+
    '</div>'+mapLink;
  }).catch(function(){ el.innerHTML='<div class="alert alert-error show" style="margin-top:8px"><i class="fa-solid fa-circle-xmark"></i>Không tra cứu được IP này</div>'; });
}

// ══ ADMIN: CHANGE PASSWORD ══
function doChangePass() {
  var u=document.getElementById('newUser').value.trim();
  var p=document.getElementById('newPass').value.trim();
  var alert2=document.getElementById('chgPassAlert');
  if(!u||!p){ showToast('Vui lòng nhập đầy đủ','warn'); return; }
  alert2.style.display='none';
  fetch('/api/change_admin',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'u='+encodeURIComponent(u)+'&p='+encodeURIComponent(p)})
  .then(function(r){return r.json();}).then(function(d){
    if(d.status==='success'){
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-success show"><i class="fa-solid fa-circle-check"></i> Đã cập nhật thành công!</div>';
    } else {
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>'+escHtml(d.message||'Lỗi cập nhật')+'</div>';
    }
  }).catch(function(){showToast('Lỗi kết nối','error');});
}

// ══ ADMIN: DEVICE REQUESTS ══
function loadDeviceRequests() {
  var el=document.getElementById('devReqList');
  if(!el) return;
  el.innerHTML='<div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div>';
  fetch('/api/list_device_requests').then(function(r){return r.json();}).then(function(data){
    if(!data.length){ el.innerHTML='<div class="empty-state"><i class="fa-solid fa-inbox"></i>Không có yêu cầu nào</div>'; return; }
    var frag = document.createDocumentFragment();
    data.forEach(function(r){
      var did=r.device_id||'—'; var short=did.length>24?did.substring(0,24)+'…':did;
      var card = document.createElement('div'); card.className='dev-req-card';
      var meta = document.createElement('div'); meta.className='dev-meta';
      var sp1=document.createElement('span'); sp1.innerHTML='<i class="fa-solid fa-clock"></i> '+escHtml(r.submitted_at_str||'');
      var sp2=document.createElement('span'); sp2.innerHTML='<i class="fa-solid fa-hourglass-half"></i> '+(r.val||'')+' '+(r.unit||'');
      var sp3=document.createElement('span'); sp3.innerHTML='<i class="fa-solid fa-globe"></i> '+escHtml(r.ip||'');
      meta.append(sp1,sp2,sp3);
      var idDiv=document.createElement('div'); idDiv.className='dev-id'; idDiv.textContent=short;
      var acts=document.createElement('div'); acts.className='dev-actions';
      var badge=document.createElement('span'); badge.className='badge badge-amber'; badge.innerHTML='<i class="fa-solid fa-clock"></i> Chờ duyệt';
      var approveBtn=document.createElement('button'); approveBtn.className='btn-sm btn-sm-green'; approveBtn.innerHTML='<i class="fa-solid fa-check"></i> Duyệt';
      approveBtn.addEventListener('click',function(){approveDevReq(r.req_id,did,r.val,r.unit);});
      var rejectBtn=document.createElement('button'); rejectBtn.className='btn-sm btn-sm-red'; rejectBtn.innerHTML='<i class="fa-solid fa-xmark"></i> Từ chối';
      rejectBtn.addEventListener('click',function(){rejectDevReq(r.req_id);});
      var copyBtn=document.createElement('button'); copyBtn.className='btn-sm btn-sm-blue'; copyBtn.innerHTML='<i class="fa-solid fa-copy"></i>';
      copyBtn.addEventListener('click',function(){copyText(did,copyBtn);});
      acts.append(badge,approveBtn,rejectBtn,copyBtn);
      card.append(idDiv,meta,acts);
      frag.appendChild(card);
    });
    el.innerHTML=''; el.appendChild(frag);
  }).catch(function(){ el.innerHTML='<div class="empty-state" style="color:var(--red)"><i class="fa-solid fa-triangle-exclamation"></i>Lỗi tải</div>'; });
}
function approveDevReq(reqId,deviceId,defVal,defUnit) {
  var val=prompt('Thời gian duyệt (số lượng):',defVal);
  if(val===null) return;
  var unit=prompt('Đơn vị (phút/tiếng/ngày/tháng/năm/permanent):',defUnit);
  if(unit===null) return;
  fetch('/api/approve_device_request',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'req_id='+encodeURIComponent(reqId)+'&val='+encodeURIComponent(val)+'&unit='+encodeURIComponent(unit)})
  .then(function(r){return r.json();}).then(function(d){ if(d.status==='success'){ loadDeviceRequests(); loadApprovedDevices(); showToast('Đã duyệt thiết bị','success'); } else showToast(d.msg||'Lỗi','error'); });
}
function rejectDevReq(reqId) {
  if(!confirm('Từ chối yêu cầu này?')) return;
  fetch('/api/reject_device_request',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'req_id='+encodeURIComponent(reqId)})
  .then(function(r){return r.json();}).then(function(){ loadDeviceRequests(); showToast('Đã từ chối','info'); });
}
function loadApprovedDevices() {
  var el=document.getElementById('approvedDevList');
  if(!el) return;
  el.innerHTML='<div class="empty-state"><div class="spinner" style="margin:0 auto 10px"></div>Đang tải...</div>';
  fetch('/api/list_approved_devices').then(function(r){return r.json();}).then(function(data){
    if(!data.length){ el.innerHTML='<div class="empty-state"><i class="fa-solid fa-check-double"></i>Chưa có thiết bị nào được duyệt</div>'; return; }
    var h='';
    data.forEach(function(d){
      var did=d.device_id||'—'; var short=did.length>24?did.substring(0,24)+'...':did;
      var stBadge=d.is_expired?'<span class="badge badge-red"><i class="fa-solid fa-xmark"></i> Hết hạn</span>':'<span class="badge badge-green"><i class="fa-solid fa-check"></i> Hợp lệ</span>';
      h+='<div class="dev-req-card">'+
        '<div class="dev-id" title="'+escHtml(did)+'">'+escHtml(short)+'</div>'+
        '<div class="dev-meta">'+
          '<span><i class="fa-solid fa-clock"></i> '+escHtml(d.time_left)+'</span>'+
          '<span><i class="fa-solid fa-calendar"></i> '+escHtml(d.approved_at)+'</span>'+
          '<span><i class="fa-solid fa-globe"></i> '+escHtml(d.ip)+'</span>'+
        '</div>'+
        '<div class="dev-actions">'+stBadge+
          '<button class="btn-sm btn-sm-amber" onclick="extendDevice(\''+escHtml(did)+'\')"><i class="fa-solid fa-calendar-plus"></i> Gia hạn</button>'+
          '<button class="btn-sm btn-sm-red" onclick="deleteDevice(\''+escHtml(did)+'\')"><i class="fa-solid fa-trash"></i> Xóa</button>'+
        '</div>'+
      '</div>';
    });
    el.innerHTML=h;
  }).catch(function(){ el.innerHTML='<div class="empty-state" style="color:var(--red)">Lỗi tải</div>'; });
}
function extendDevice(did) {
  var val=prompt('Thêm bao nhiêu?','7');
  if(!val) return;
  var unit=prompt('Đơn vị:','ngày');
  if(!unit) return;
  fetch('/api/extend_approved_device',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'device_id='+encodeURIComponent(did)+'&val='+encodeURIComponent(val)+'&unit='+encodeURIComponent(unit)})
  .then(function(r){return r.json();}).then(function(d){ if(d.status==='success'){ loadApprovedDevices(); showToast('Đã gia hạn','success'); } else showToast(d.msg||'Lỗi','error'); });
}
function deleteDevice(did) {
  if(!confirm('Xóa thiết bị: '+did+'?')) return;
  fetch('/api/delete_approved_device',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'device_id='+encodeURIComponent(did)})
  .then(function(r){return r.json();}).then(function(){ loadApprovedDevices(); showToast('Đã xóa thiết bị','success'); });
}
function doAdminAddID() {
  var did=document.getElementById('adminDeviceId').value.trim();
  var val=document.getElementById('adminDevVal').value.trim();
  var unit=document.getElementById('adminDevUnit').value;
  var alert2=document.getElementById('adminAddIDAlert');
  if(!did){ showToast('Vui lòng nhập Device ID!','warn'); return; }
  alert2.style.display='none';
  fetch('/api/add_device_id',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'device_id='+encodeURIComponent(did)+'&val='+encodeURIComponent(val)+'&unit='+encodeURIComponent(unit)})
  .then(function(r){return r.json();}).then(function(d){
    if(d.status==='success'){
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-success show"><i class="fa-solid fa-circle-check"></i> Đã duyệt & kích hoạt thành công!</div>';
      document.getElementById('adminDeviceId').value='';
      loadApprovedDevices();
      setTimeout(function(){alert2.style.display='none';},3000);
    } else {
      alert2.style.display='block';
      alert2.innerHTML='<div class="alert alert-error show"><i class="fa-solid fa-circle-xmark"></i>'+escHtml(d.msg||'Lỗi')+'</div>';
    }
  }).catch(function(){showToast('Lỗi kết nối','error');});
}

// ══ ADMIN: WEB LOGS ══
function loadWebLogs() {
  var el=document.getElementById('logContainer');
  var tot=document.getElementById('logTotal');
  if(!el) return;
  el.innerHTML='<div class="empty-state" style="color:#475569"><div class="spinner" style="margin:0 auto 10px;border-top-color:#60a5fa"></div>Đang tải nhật ký...</div>';
  fetch('/api/web_logs?limit=200').then(function(r){return r.json();}).then(function(d){
    if(tot) tot.textContent=d.total||0;
    if(!d.lines||!d.lines.length){ el.innerHTML='<span style="color:#475569">Chưa có nhật ký nào</span>'; return; }
    el.innerHTML=d.lines.map(function(l){
      var re=/^\[([^\]]+)\]\s+(\S+)\s+(\S+)\s+(.+)$/,parts=l.match(re);
      if(parts) return '<div><span class="l-time">['+parts[1]+']</span> <span class="l-ip">'+parts[2]+'</span> <span class="l-method">'+parts[3]+'</span> <span class="l-path">'+escHtml(parts[4])+'</span></div>';
      return '<div>'+escHtml(l)+'</div>';
    }).join('');
  }).catch(function(){ el.innerHTML='<span style="color:#ef4444">Lỗi tải nhật ký</span>'; });
}
function clearWebLogs() {
  if(!confirm('Xóa toàn bộ nhật ký web?')) return;
  fetch('/api/clear_web_logs',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
    if(d.status==='success'){ loadWebLogs(); showToast('Đã xóa nhật ký','success'); }
    else showToast('Lỗi xóa nhật ký','error');
  }).catch(function(){showToast('Lỗi kết nối','error');});
}

// ══ TOGGLE CUSTOM KEY FORM ══
document.querySelectorAll('input[name="mode"]').forEach(function(r){
  r.addEventListener('change',function(){
    var show = document.querySelector('input[name="mode"]:checked')?.value==='custom';
    var el = document.getElementById('customKeyFg');
    if(el) el.style.display = show?'block':'none';
  });
});

// ══ INIT ══
{% if session.get('is_admin') %}
(function() {
  var url = new URL(window.location.href);
  if(url.hash==='#admin') { sw('admin'); sw_admin('home'); }
})();
{% endif %}
</script>
</body>
</html>
"""

CHECK_IP_KEY_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Check IP Key</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
*:focus{outline:none!important}
:root{--bg:#f1f5f9;--panel:#fff;--border:#e2e8f0;--blue:#2563eb;--blue-light:#eff6ff;--green:#16a34a;--red:#dc2626;--amber:#d97706;--text:#0f172a;--muted:#64748b;--shadow:0 1px 3px rgba(0,0,0,.1)}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;padding-bottom:40px}
.topbar{position:fixed;top:0;left:0;right:0;height:54px;background:#fff;border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 16px;gap:12px;z-index:50;box-shadow:var(--shadow)}
.bk{display:inline-flex;align-items:center;gap:6px;color:var(--blue);font-weight:700;font-size:.82rem;text-decoration:none;padding:7px 12px;border:1.5px solid var(--border);border-radius:8px;background:#fff;transition:.15s}
.bk:hover{background:var(--blue-light);border-color:#bfdbfe}
.ttl{font-weight:800;font-size:.9rem;color:var(--text)}
.wrap{max-width:560px;margin:0 auto;padding:66px 14px 0}
.card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:18px;margin-bottom:12px;box-shadow:var(--shadow)}
.card-hd{font-weight:700;font-size:.88rem;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.card-hd i{width:32px;height:32px;background:var(--blue-light);color:var(--blue);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.82rem}
.hero{text-align:center;padding:18px 0}
.hero-icon{width:58px;height:58px;background:var(--blue);border-radius:15px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:1.25rem;color:#fff;box-shadow:0 4px 12px rgba(37,99,235,.3)}
.hero-title{font-weight:900;font-size:1.3rem;color:var(--text);margin-bottom:5px}
.hero-sub{font-size:.8rem;color:var(--muted)}
.fg{margin-bottom:12px}
.fg label{display:block;font-size:.74rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.srow{display:flex;gap:8px}
.sinp{flex:1;padding:11px 14px;background:#fff;border:1.5px solid var(--border);border-radius:10px;color:var(--text);font-size:.88rem;font-family:'Inter',sans-serif;outline:none;transition:.15s}
.sinp:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(37,99,235,.1)}
.sbtn{padding:11px 18px;background:var(--blue);border:none;border-radius:10px;color:#fff;font-weight:700;font-size:.88rem;cursor:pointer;transition:.15s;font-family:'Inter',sans-serif;white-space:nowrap;display:flex;align-items:center;gap:6px}
.sbtn:hover:not(:disabled){background:#1d4ed8}
.sbtn:disabled{opacity:.5;cursor:not-allowed}
@keyframes spin{to{transform:rotate(360deg)}}
.spinner{width:20px;height:20px;border:2.5px solid #e2e8f0;border-top-color:var(--blue);border-radius:50%;animation:spin .75s linear infinite;margin:0 auto 8px}
.radar-wrap{display:none;text-align:center;padding:24px;background:#fff;border:1px solid var(--border);border-radius:14px;margin-bottom:12px}
.ebox{background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;padding:18px;display:none;margin-bottom:12px;text-align:center}
.eico{font-size:1.6rem;color:var(--red);margin-bottom:8px}
.emsg{font-size:.85rem;font-weight:700;color:var(--red)}
.results{display:none}
.kcard{background:#fff;border:1px solid var(--border);border-radius:12px;padding:15px;margin-bottom:10px;box-shadow:var(--shadow)}
.kcard-hd{display:flex;align-items:center;gap:7px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--border)}
.drow{display:flex;align-items:flex-start;gap:11px;padding:9px 0;border-bottom:1px solid #f1f5f9}
.drow:last-child{border-bottom:none;padding-bottom:0}
.dic{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.8rem;flex-shrink:0;margin-top:1px}
.ib{background:var(--blue-light);color:var(--blue)}
.ig{background:#f0fdf4;color:var(--green)}
.ip{background:#f5f3ff;color:#7c3aed}
.db{flex:1;min-width:0}
.dlbl{font-size:.65rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
.dval{font-size:.85rem;font-weight:700;color:var(--text);word-break:break-all}
.dsub{font-size:.72rem;color:var(--muted);margin-top:2px}
.cpb{flex-shrink:0;background:var(--blue-light);border:1px solid #bfdbfe;color:var(--blue);padding:5px 9px;border-radius:7px;font-size:.69rem;font-weight:700;cursor:pointer;transition:.2s;font-family:'Inter',sans-serif}
.cpb:hover{background:#dbeafe}
.cpb.ok{background:#f0fdf4;border-color:#86efac;color:var(--green)}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:.71rem;font-weight:700;margin-top:4px}
.b-act{background:#f0fdf4;color:var(--green);border:1px solid #86efac}
.b-inact{background:#fffbeb;color:var(--amber);border:1px solid #fcd34d}
.b-exp{background:#fef2f2;color:var(--red);border:1px solid #fca5a5}
.geo-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.gcell{background:#f8fafc;border-radius:9px;padding:10px 12px;border:1px solid var(--border)}
.gcell.full{grid-column:1/-1}
.glbl{font-size:.63rem;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
.gval{font-size:.83rem;font-weight:800;color:var(--text);word-break:break-all}
.mlink{display:inline-flex;align-items:center;gap:6px;color:var(--blue);text-decoration:none;font-weight:700;font-size:.78rem;border:1px solid #bfdbfe;padding:7px 13px;border-radius:9px;margin-top:10px;transition:.15s}
.mlink:hover{background:var(--blue-light)}
.devitem{background:#f8fafc;border:1px solid var(--border);border-radius:10px;padding:11px 13px;margin-bottom:7px}
.devnum{font-size:.69rem;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.devrow{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;font-size:.8rem;padding:3px 0;border-bottom:1px solid var(--border)}
.devrow:last-child{border-bottom:none}
.dkey{color:var(--muted);flex-shrink:0}
.dval2{color:var(--text);font-weight:700;text-align:right;word-break:break-all;max-width:65%}
</style>
</head>
<body>
<div class="topbar">
  <a href="/" class="bk"><i class="fa-solid fa-arrow-left"></i> Quay Lại</a>
  <div class="ttl">Check IP Key</div>
</div>
<div class="wrap">
  <div class="hero">
    <div class="hero-icon"><i class="fa-solid fa-network-wired"></i></div>
    <div class="hero-title">Tra Cứu Thông Tin Key</div>
    <div class="hero-sub">Kiểm tra chi tiết key, thiết bị và vị trí địa lý IP</div>
  </div>
  <div class="card">
    <div class="fg">
      <label><i class="fa-solid fa-key" style="color:var(--blue)"></i> Nhập mã key cần tra cứu</label>
      <div class="srow">
        <input class="sinp" id="inp" placeholder="VD: FREE-ABC12 hoặc 7DAY-XYZ..." onkeydown="if(event.key==='Enter')doCheck()">
        <button class="sbtn" id="sbtn" onclick="doCheck()"><i class="fa-solid fa-magnifying-glass"></i> TRA CỨU</button>
      </div>
    </div>
  </div>
  <div class="radar-wrap" id="rdrWrap"><div class="spinner"></div><div style="font-size:.82rem;color:var(--muted);font-weight:600">Đang tra cứu thông tin...</div></div>
  <div class="ebox" id="ebox"><div class="eico"><i class="fa-solid fa-triangle-exclamation"></i></div><div class="emsg" id="emsg">Key không tồn tại!</div></div>
  <div class="results" id="results">
    <div class="kcard">
      <div class="kcard-hd"><div class="dic ib"><i class="fa-solid fa-key"></i></div><span style="font-weight:700;font-size:.82rem;color:var(--blue);text-transform:uppercase;letter-spacing:.5px">Thông Tin Key</span></div>
      <div class="drow"><div class="dic ib"><i class="fa-solid fa-key"></i></div><div class="db"><div class="dlbl">Mã Key</div><div class="dval" id="r-key" style="font-family:monospace;font-size:.82rem"></div><div id="r-status-wrap"></div></div><button class="cpb" onclick="cp('r-key',this)"><i class="fa-solid fa-copy"></i> Copy</button></div>
      <div class="drow"><div class="dic ib"><i class="fa-solid fa-hourglass-half"></i></div><div class="db"><div class="dlbl">Thời Hạn Key</div><div class="dval" id="r-dur" style="color:var(--blue)"></div></div></div>
      <div class="drow"><div class="dic ig"><i class="fa-solid fa-desktop"></i></div><div class="db"><div class="dlbl">Địa Chỉ IP Kích Hoạt</div><div class="dval" id="r-ip" style="color:var(--green);font-family:monospace;font-size:.8rem"></div><div class="dsub">IP ghi nhận lúc kích hoạt</div></div><button class="cpb" onclick="cp('r-ip',this)"><i class="fa-solid fa-copy"></i></button></div>
      <div class="drow"><div class="dic ib"><i class="fa-solid fa-bolt"></i></div><div class="db"><div class="dlbl">Thời Gian Kích Hoạt</div><div class="dval" id="r-act"></div></div></div>
      <div class="drow"><div class="dic ib"><i class="fa-solid fa-calendar-plus"></i></div><div class="db"><div class="dlbl">Ngày Tạo Key</div><div class="dval" id="r-created"></div></div></div>
    </div>
    <div class="kcard" id="geoCard" style="display:none">
      <div class="kcard-hd"><div class="dic ip"><i class="fa-solid fa-earth-asia"></i></div><span style="font-weight:700;font-size:.82rem;color:#7c3aed;text-transform:uppercase;letter-spacing:.5px">Vị Trí Địa Lý IP</span></div>
      <div class="geo-grid" id="geoGrid"></div>
      <div id="geoMapWrap"></div>
    </div>
    <div class="kcard" id="devCard" style="display:none">
      <div class="kcard-hd"><div class="dic ip"><i class="fa-solid fa-mobile-screen-button"></i></div><span style="font-weight:700;font-size:.82rem;color:#7c3aed;text-transform:uppercase;letter-spacing:.5px">Thiết Bị Đã Đăng Ký</span></div>
      <div id="devList"></div>
    </div>
  </div>
</div>
<script>
function cp(id,btn){var val=document.getElementById(id).innerText.trim();if(!val||val==='—')return;navigator.clipboard.writeText(val).then(function(){var o=btn.innerHTML;btn.innerHTML='<i class="fa-solid fa-check"></i> OK';btn.classList.add('ok');setTimeout(function(){btn.innerHTML=o;btn.classList.remove('ok');},1500);}).catch(function(){prompt('Copy:',val);});}
function cpTxt(txt,btn){navigator.clipboard.writeText(txt).then(function(){var o=btn.innerHTML;btn.innerHTML='<i class="fa-solid fa-check"></i>';btn.classList.add('ok');setTimeout(function(){btn.innerHTML=o;btn.classList.remove('ok');},1500);}).catch(function(){prompt('Copy:',txt);});}
function escH(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function translateCountry(c){var m={'Vietnam':'Việt Nam','United States':'Hoa Kỳ','China':'Trung Quốc','Japan':'Nhật Bản','South Korea':'Hàn Quốc','Singapore':'Singapore','Thailand':'Thái Lan','Germany':'Đức','France':'Pháp','United Kingdom':'Anh','Australia':'Úc','Canada':'Canada','Russia':'Nga'};return m[c]||c||'—';}
function renderGeo(ip,geo){var uk='Không rõ';var country=translateCountry(geo.country||'');var region=geo.region||uk;var city=geo.city||uk;var org=geo.organization_name||geo.org||uk;var tz=geo.timezone||uk;var lat=geo.latitude||'';var lng=geo.longitude||'';var h='<div class="gcell full"><div class="glbl">Địa Chỉ Cụ Thể</div><div class="gval" style="color:var(--green)">'+(city!==uk?city+(region!==uk?', '+region:''):uk)+'</div></div>';h+='<div class="gcell"><div class="glbl">Quốc Gia</div><div class="gval">'+country+'</div></div>';h+='<div class="gcell"><div class="glbl">Thành Phố</div><div class="gval">'+city+'</div></div>';h+='<div class="gcell"><div class="glbl">Múi Giờ</div><div class="gval">'+tz+'</div></div>';h+='<div class="gcell full"><div class="glbl">Nhà Mạng</div><div class="gval" style="color:var(--blue)">'+org+'</div></div>';if(lat&&lng){h+='<div class="gcell"><div class="glbl">Vĩ Độ</div><div class="gval">'+lat+'</div></div><div class="gcell"><div class="glbl">Kinh Độ</div><div class="gval">'+lng+'</div></div>';}document.getElementById('geoGrid').innerHTML=h;document.getElementById('geoMapWrap').innerHTML=lat&&lng?'<a class="mlink" href="https://www.google.com/maps?q='+lat+','+lng+'" target="_blank"><i class="fa-solid fa-map-location-dot"></i> Xem trên Google Maps</a>':'';}
function doCheck(){var key=document.getElementById('inp').value.trim();if(!key){alert('Vui lòng nhập mã key!');return;}var btn=document.getElementById('sbtn');btn.disabled=true;document.getElementById('rdrWrap').style.display='block';document.getElementById('results').style.display='none';document.getElementById('ebox').style.display='none';setTimeout(function(){fetch('/api/get_key_ip_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'key='+encodeURIComponent(key)}).then(function(r){return r.json();}).then(function(d){document.getElementById('rdrWrap').style.display='none';if(!d.exists){document.getElementById('emsg').innerHTML='<i class="fa-solid fa-triangle-exclamation"></i> '+(d.msg||'Key không tồn tại!');document.getElementById('ebox').style.display='block';btn.disabled=false;return;}document.getElementById('r-key').innerText=d.key||'—';document.getElementById('r-dur').innerText=d.duration||'—';var st=d.status||'';var scls=st==='Đã kích hoạt'?'b-act':(st==='Chưa kích hoạt'?'b-inact':'b-exp');document.getElementById('r-status-wrap').innerHTML='<span class="badge '+scls+'">'+st+'</span>';document.getElementById('r-ip').innerText=d.client_ip||'— Chưa có thông tin —';document.getElementById('r-act').innerText=d.activated_time||'—';document.getElementById('r-created').innerText=d.created_at||'—';document.getElementById('results').style.display='block';var devs=d.devices||[];if(devs.length>0){var dh='';devs.forEach(function(dev,idx){var did=dev.device_id||'—';var exp=dev.expiry_str||'—';var short=did.length>22?did.substring(0,22)+'...':did;dh+='<div class="devitem"><div class="devnum"><i class="fa-solid fa-mobile-screen-button"></i> Thiết Bị #'+(idx+1)+'</div><div class="devrow"><span class="dkey">Machine ID</span><span class="dval2" title="'+escH(did)+'">'+escH(short)+'</span></div><div class="devrow"><span class="dkey">Hạn sử dụng</span><span class="dval2">'+escH(exp)+'</span></div></div>';});document.getElementById('devList').innerHTML=dh;document.getElementById('devCard').style.display='block';}var ip=d.client_ip;if(ip&&ip.length>0){document.getElementById('geoCard').style.display='block';document.getElementById('geoGrid').innerHTML='<div class="gcell full" style="text-align:center;color:var(--muted);font-size:.8rem;padding:14px"><div style="width:22px;height:22px;border:2px solid #e2e8f0;border-top-color:var(--blue);border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 8px"></div>Đang tra cứu vị trí...</div>';fetch('https://get.geojs.io/v1/ip/geo/'+encodeURIComponent(ip)+'.json').then(function(r){return r.json();}).then(function(geo){renderGeo(ip,geo);}).catch(function(){document.getElementById('geoGrid').innerHTML='<div class="gcell full" style="color:var(--red);font-size:.8rem;text-align:center;padding:12px"><i class="fa-solid fa-shield-halved"></i> Không tra cứu được vị trí IP</div>';});}btn.disabled=false;}).catch(function(){document.getElementById('rdrWrap').style.display='none';document.getElementById('emsg').innerHTML='<i class="fa-solid fa-plug-circle-xmark"></i> Lỗi kết nối máy chủ!';document.getElementById('ebox').style.display='block';btn.disabled=false;});},1200);}
(function(){var params=new URLSearchParams(window.location.search);var k=params.get('key');if(k){document.getElementById('inp').value=k;setTimeout(doCheck,300);}})();
</script>
</body>
</html>
"""

FREE_KEY_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Nhận Key Free</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
*:focus{outline:none!important}
:root{--blue:#2563eb;--green:#16a34a;--red:#dc2626;--amber:#d97706;--text:#0f172a;--muted:#64748b;--border:#e2e8f0}
body{background:linear-gradient(135deg,#eff6ff 0%,#f0fdf4 100%);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.wrap{width:min(440px,100%)}
.card{background:#fff;border:1px solid var(--border);border-radius:20px;padding:28px 24px;box-shadow:0 10px 40px rgba(0,0,0,.08)}
.hd{text-align:center;margin-bottom:24px}
.hd-icon{width:58px;height:58px;background:var(--blue);border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;font-size:1.3rem;color:#fff;box-shadow:0 4px 15px rgba(37,99,235,.3)}
.hd-title{font-weight:900;font-size:1.2rem;color:var(--text);margin-bottom:5px}
.hd-sub{font-size:.8rem;color:var(--muted)}
.prog-wrap{margin-bottom:16px}
.prog-track{width:100%;height:8px;background:#f1f5f9;border-radius:99px;overflow:hidden;border:1px solid var(--border)}
.prog-fill{height:100%;width:0%;background:linear-gradient(90deg,var(--blue),#7c3aed);border-radius:99px;transition:width .15s linear}
.prog-pct{text-align:center;font-size:.78rem;font-weight:800;color:var(--blue);margin-top:5px}
.chk-list{display:flex;flex-direction:column;gap:8px}
.chk-row{display:flex;align-items:center;gap:11px;padding:10px 13px;background:#f8fafc;border:1px solid var(--border);border-radius:10px;transition:.3s}
.chk-row.ok-row{background:#f0fdf4;border-color:#86efac}
.chk-row.fail-row{background:#fef2f2;border-color:#fca5a5}
.chk-ico{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:.8rem;flex-shrink:0;background:#e2e8f0;color:var(--muted);transition:.3s}
.chk-ico.run{background:#dbeafe;color:var(--blue);animation:p .8s ease infinite}
.chk-ico.ok{background:#dcfce7;color:var(--green)}
.chk-ico.fail{background:#fee2e2;color:var(--red)}
@keyframes p{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}
.chk-desc{font-size:.82rem;font-weight:600;color:var(--muted);flex:1}
.chk-row.ok-row .chk-desc{color:var(--green)}
.chk-row.fail-row .chk-desc{color:var(--red)}
#resBox{text-align:center}
.res-icon{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;background:#dcfce7;border:2px solid #86efac}
.res-icon svg{stroke:var(--green)}
@keyframes drawCheck{to{stroke-dashoffset:0}}
@keyframes popIn{from{transform:scale(0)}50%{transform:scale(1.2)}to{transform:scale(1)}}
.animated-check{stroke-dasharray:100;stroke-dashoffset:100;animation:drawCheck .5s .2s ease forwards;stroke-linecap:round;stroke-linejoin:round;stroke-width:2.5;fill:none}
.res-icon.success-icon{animation:popIn .4s cubic-bezier(.34,1.56,.64,1) both}
.res-label{font-weight:800;font-size:1rem;color:var(--green);margin-bottom:5px}
.res-sub{font-size:.78rem;color:var(--muted);margin-bottom:16px}
.key-display{background:#f8fafc;border:1.5px solid var(--border);border-radius:12px;padding:14px;margin-bottom:14px}
.key-display .kd-label{font-size:.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:7px}
.key-val{font-family:monospace;font-size:1.05rem;font-weight:900;color:var(--blue);word-break:break-all;letter-spacing:.5px}
.key-meta{display:flex;justify-content:center;gap:12px;margin-top:8px;font-size:.76rem;color:var(--muted);font-weight:600;flex-wrap:wrap}
.btn{display:flex;align-items:center;justify-content:center;gap:7px;width:100%;padding:12px;border-radius:11px;font-weight:700;font-size:.9rem;cursor:pointer;border:none;transition:.15s;font-family:'Inter',sans-serif;margin-bottom:8px}
.btn-blue{background:var(--blue);color:#fff}
.btn-blue:hover{background:#1d4ed8}
.btn-outline{background:#fff;color:var(--text);border:1.5px solid var(--border)}
.btn-outline:hover{background:#f8fafc}
#errBox{text-align:center}
.err-icon{width:58px;height:58px;border-radius:50%;background:#fef2f2;border:2px solid #fca5a5;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;font-size:1.3rem;color:var(--red)}
.err-label{font-weight:800;color:var(--red);margin-bottom:8px;font-size:.95rem}
.err-msg{font-size:.82rem;color:var(--muted);line-height:1.65;margin-bottom:14px}
@keyframes spin{to{transform:rotate(360deg)}}
.spin-anim{animation:spin .75s linear infinite}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="hd">
      <div class="hd-icon"><i class="fa-solid fa-key"></i></div>
      <div class="hd-title">Nhận Key Miễn Phí</div>
      <div class="hd-sub">Hệ thống đang xác thực và cấp key...</div>
    </div>
    <div id="scanBox">
      <div class="prog-wrap">
        <div class="prog-track"><div class="prog-fill" id="progBar"></div></div>
        <div class="prog-pct" id="progPct">0%</div>
        <div style="text-align:center;font-size:.75rem;color:var(--muted);margin-top:4px" id="progLabel">Đang khởi động...</div>
      </div>
      <div class="chk-list">
        <div class="chk-row" id="chk1"><div class="chk-ico wait" id="chk1ico"><i class="fa-solid fa-circle-dot"></i></div><div class="chk-desc" id="chk1desc">Quét IP thiết bị</div></div>
        <div class="chk-row" id="chk2"><div class="chk-ico wait" id="chk2ico"><i class="fa-solid fa-circle-dot"></i></div><div class="chk-desc" id="chk2desc">Kiểm tra VPN/Proxy</div></div>
        <div class="chk-row" id="chk3"><div class="chk-ico wait" id="chk3ico"><i class="fa-solid fa-circle-dot"></i></div><div class="chk-desc" id="chk3desc">Xác thực & cấp key</div></div>
      </div>
    </div>
    <div id="resBox" style="display:none">
      <div class="res-icon success-icon"><svg width="30" height="30" viewBox="0 0 24 24"><polyline points="20,6 9,17 4,12" class="animated-check"/></svg></div>
      <div class="res-label">Nhận Key Thành Công!</div>
      <div class="res-sub">Key đã được cấp. Dán vào phần mềm để sử dụng.</div>
      <div class="key-display">
        <div class="kd-label"><i class="fa-solid fa-key" style="color:var(--blue)"></i> Mã Key của bạn</div>
        <div class="key-val" id="keyVal">—</div>
        <div class="key-meta" id="keyMeta"></div>
      </div>
      <button class="btn btn-blue" onclick="cpKey()"><i class="fa-solid fa-copy"></i> Sao Chép Key</button>
      <button class="btn btn-outline" onclick="window.location.href='/'"><i class="fa-solid fa-house"></i> Về Trang Chủ</button>
    </div>
    <div id="errBox" style="display:none">
      <div class="err-icon"><i class="fa-solid fa-circle-xmark"></i></div>
      <div class="err-label">Không thể nhận Key</div>
      <div class="err-msg" id="errMsg">Xảy ra lỗi không xác định.</div>
      <button class="btn btn-outline" onclick="window.location.href='/'"><i class="fa-solid fa-house"></i> Về Trang Chủ</button>
    </div>
  </div>
</div>
<script>
function setProgress(pct, label) {
  document.getElementById('progBar').style.width = pct + '%';
  document.getElementById('progPct').textContent = pct + '%';
  if(label) document.getElementById('progLabel').textContent = label;
}
function setCheck(n, state, desc) {
  var ico = document.getElementById('chk'+n+'ico');
  var dsc = document.getElementById('chk'+n+'desc');
  var row = document.getElementById('chk'+n);
  ico.className = 'chk-ico ' + state;
  row.className = 'chk-row' + (state==='ok'?' ok-row':state==='fail'?' fail-row':'');
  if(state==='wait') ico.innerHTML='<i class="fa-solid fa-circle-dot"></i>';
  else if(state==='run') ico.innerHTML='<i class="fa-solid fa-circle-notch spin-anim"></i>';
  else if(state==='ok') ico.innerHTML='<i class="fa-solid fa-circle-check"></i>';
  else if(state==='fail') ico.innerHTML='<i class="fa-solid fa-circle-xmark"></i>';
  if(desc) dsc.textContent = desc;
}
var generatedKey = null;
function showSuccess(key, han, dev) {
  document.getElementById('scanBox').style.display='none';
  document.getElementById('errBox').style.display='none';
  document.getElementById('resBox').style.display='block';
  document.getElementById('keyVal').innerText = key;
  generatedKey = key;
  if(han||dev) {
    document.getElementById('keyMeta').innerHTML =
      (han?'<span><i class="fa-solid fa-clock" style="color:var(--blue)"></i> '+han+'</span>':'<span><i class="fa-solid fa-clock" style="color:var(--blue)"></i> 12 giờ</span>')
      +(dev?'<span><i class="fa-solid fa-mobile-screen" style="color:#7c3aed"></i> '+dev+' thiết bị</span>':'')
      +'<span><i class="fa-solid fa-shield-check" style="color:var(--green)"></i> Đã xác thực</span>';
  }
}
function showFail(msg) {
  setProgress(100,'Kiểm tra hoàn tất');
  setTimeout(function(){
    document.getElementById('scanBox').style.display='none';
    document.getElementById('resBox').style.display='none';
    document.getElementById('errBox').style.display='block';
    document.getElementById('errMsg').innerHTML = msg;
  }, 700);
}
function cpKey() {
  if(!generatedKey) return;
  navigator.clipboard.writeText(generatedKey)
  .then(function(){ alert('✅ Đã sao chép key! Dán vào phần mềm để sử dụng.'); })
  .catch(function(){ prompt('Sao chép thủ công:', generatedKey); });
}
(function(){
  var params = new URLSearchParams(window.location.search);
  var token = params.get('token');
  if(!token) {
    showFail('Bạn cần vượt link rút gọn (Link4m) trước!<br>Liên hệ Admin: <strong style="color:var(--blue);">@vkhanh3010</strong>');
    return;
  }
  setProgress(8,'Đang quét IP thiết bị...');
  setCheck(1,'run','Đang quét IP...');
  var ipDataStr = '';
  fetch('https://get.geojs.io/v1/ip/geo.json')
  .then(function(r){return r.json();})
  .then(function(d){
    if(d&&d.ip){
      ipDataStr='Client IP: '+d.ip+' | '+(d.city||'')+', '+(d.country||'')+' | Org: '+(d.organization_name||d.org||'N/A');
      setCheck(1,'ok','IP: '+d.ip+' — '+(d.country||'Unknown'));
    } else setCheck(1,'ok','IP đã ghi nhận');
    setProgress(38,'Đang phát hiện VPN/Proxy...');
    setCheck(2,'run','Đang phân tích lưu lượng...');
    setTimeout(function(){
      setProgress(65,'Đang xác thực bypass link...');
      setCheck(2,'ok','Lưu lượng bình thường');
      setCheck(3,'run','Đang gửi yêu cầu máy chủ...');
      setProgress(82,'Đang tạo key từ máy chủ...');
      fetch('/api/confirm_bypass',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'token='+encodeURIComponent(token)+'&ip_info='+encodeURIComponent(ipDataStr)})
      .then(function(r){return r.json();})
      .then(function(d){
        if(d.status==='success'){
          setProgress(100,'Xác thực thành công!');
          setCheck(3,'ok','Bypass hợp lệ — key đã tạo');
          setTimeout(function(){showSuccess(d.key,d.han_dung||null,d.thiet_bi||null);},700);
        } else {
          var msg=d.message||'';
          var fc=3;
          if(msg.includes('VPN')||msg.includes('proxy')||msg.includes('Proxy')) fc=2;
          else if(msg.includes('IP')||msg.includes('giới hạn')) fc=1;
          if(fc===1){setCheck(1,'fail','');setCheck(2,'ok','OK');setCheck(3,'ok','OK');}
          else if(fc===2){setCheck(2,'fail','');setCheck(3,'ok','OK');}
          else setCheck(3,'fail','');
          showFail(msg||'Xảy ra lỗi không xác định.');
        }
      })
      .catch(function(){setCheck(3,'fail','Đứt kết nối');showFail('Lỗi kết nối máy chủ. Thử tải lại trang!');});
    },900);
  })
  .catch(function(){
    setCheck(1,'ok','IP ghi nhận (offline mode)');
    setProgress(65,'Đang xác thực bypass link...');
    setCheck(2,'ok','Bỏ qua kiểm tra mạng ngoài');
    setCheck(3,'run','Đang kiểm tra server...');
    fetch('/api/confirm_bypass',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'token='+encodeURIComponent(token)+'&ip_info='})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.status==='success'){setProgress(100,'Xác thực thành công!');setCheck(3,'ok','OK');setTimeout(function(){showSuccess(d.key,d.han_dung||null,d.thiet_bi||null);},700);}
      else{setCheck(3,'fail','');showFail(d.message||'Lỗi xác thực.');}
    })
    .catch(function(){setCheck(3,'fail','');showFail('Lỗi kết nối máy chủ.');});
  });
})();
</script>
</body>
</html>
"""

DEVICE_REG_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>Đăng Ký Thiết Bị</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
*:focus{outline:none!important}
:root{--blue:#2563eb;--green:#16a34a;--red:#dc2626;--amber:#d97706;--text:#0f172a;--muted:#64748b;--border:#e2e8f0}
body{background:#f1f5f9;color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;display:flex;align-items:flex-start;justify-content:center;padding:20px 16px 40px}
.wrap{width:min(420px,100%);margin:0 auto;padding-top:8px}
.header{text-align:center;margin-bottom:22px}
.hd-icon{width:58px;height:58px;background:var(--blue);border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:1.3rem;color:#fff;box-shadow:0 4px 15px rgba(37,99,235,.3)}
.hd-title{font-weight:900;font-size:1.2rem;color:var(--text);margin-bottom:5px}
.hd-sub{font-size:.78rem;color:var(--muted)}
.card{background:#fff;border:1px solid var(--border);border-radius:16px;padding:22px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.fg{margin-bottom:12px}
.fg label{display:block;font-size:.74rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px}
.fg input,.fg select,.fg textarea{width:100%;padding:11px 14px;background:#fff;border:1.5px solid var(--border);border-radius:10px;color:var(--text);font-size:.9rem;font-family:'Inter',sans-serif;outline:none;transition:.15s}
.fg input:focus,.fg select:focus,.fg textarea:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(37,99,235,.1)}
.fg textarea{resize:none;min-height:70px}
.row2{display:flex;gap:10px}.row2>*{flex:1}
.btn-sub{width:100%;padding:13px;background:var(--blue);border:none;border-radius:11px;color:#fff;font-weight:700;font-size:.9rem;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;transition:.15s;font-family:'Inter',sans-serif}
.btn-sub:hover:not(:disabled){background:#1d4ed8;transform:translateY(-1px)}
.btn-sub:disabled{opacity:.5;cursor:not-allowed;transform:none}
@keyframes spin{to{transform:rotate(360deg)}}
.spinner{width:18px;height:18px;border:2.5px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .75s linear infinite;display:inline-block;vertical-align:middle}
.alert{border-radius:10px;padding:12px 14px;font-size:.84rem;font-weight:600;display:none;margin-top:10px}
.alert-success{background:#f0fdf4;border:1px solid #86efac;color:var(--green)}
.alert-error{background:#fef2f2;border:1px solid #fca5a5;color:var(--red)}
.info-box{background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:14px 16px;font-size:.8rem;color:var(--muted);line-height:1.75}
.info-box strong{color:var(--text)}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="hd-icon"><i class="fa-solid fa-mobile-screen-button"></i></div>
    <div class="hd-title">Đăng Ký Thiết Bị</div>
    <div class="hd-sub">Gửi yêu cầu duyệt Device ID tới Admin</div>
  </div>
  <div class="card">
    <div class="fg"><label><i class="fa-solid fa-fingerprint" style="color:var(--blue)"></i> Device ID / Machine ID</label><input type="text" id="devId" required placeholder="Dán Device ID của thiết bị vào đây..."></div>
    <div class="fg"><label><i class="fa-solid fa-hourglass-half" style="color:var(--amber)"></i> Thời gian sử dụng mong muốn</label><div class="row2"><input type="number" id="devVal" value="7" min="1" placeholder="Số lượng"><select id="devUnit"><option value="phút">Phút</option><option value="tiếng">Tiếng</option><option value="ngày" selected>Ngày</option><option value="tháng">Tháng</option><option value="năm">Năm</option></select></div></div>
    <div class="fg"><label><i class="fa-solid fa-note-sticky" style="color:var(--amber)"></i> Ghi chú (tuỳ chọn)</label><textarea id="devNote" placeholder="Lý do xin duyệt, tên thiết bị,..."></textarea></div>
    <div class="alert alert-success" id="alertOk"></div>
    <div class="alert alert-error" id="alertErr"></div>
    <button type="button" class="btn-sub" id="subBtn" onclick="submitDeviceReq()"><i class="fa-solid fa-paper-plane"></i> Gửi Yêu Cầu</button>
  </div>
  <div class="info-box">
    <div style="font-weight:800;color:var(--blue);margin-bottom:8px"><i class="fa-solid fa-circle-info"></i> Hướng dẫn</div>
    <div>1. Nhập <strong>Device ID</strong> chính xác của thiết bị bạn muốn duyệt.</div>
    <div>2. Chọn thời gian sử dụng mong muốn.</div>
    <div>3. Nhấn <strong>Gửi Yêu Cầu</strong> và chờ Admin duyệt.</div>
    <div style="margin-top:8px">Liên hệ Admin: <strong style="color:var(--blue)">@vkhanh3010</strong></div>
  </div>
</div>
<script>
function submitDeviceReq() {
  var did=document.getElementById('devId').value.trim();
  var val=document.getElementById('devVal').value.trim();
  var unit=document.getElementById('devUnit').value;
  var note=document.getElementById('devNote').value.trim();
  var btn=document.getElementById('subBtn');
  var alertOk=document.getElementById('alertOk');
  var alertErr=document.getElementById('alertErr');
  if(!did){alertErr.style.display='block';alertErr.innerHTML='<i class="fa-solid fa-triangle-exclamation"></i> Vui lòng nhập Device ID!';return;}
  alertOk.style.display='none';alertErr.style.display='none';
  btn.disabled=true;btn.innerHTML='<div class="spinner"></div> Đang gửi...';
  fetch('/api/submit_device_request',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'device_id='+encodeURIComponent(did)+'&val='+encodeURIComponent(val)+'&unit='+encodeURIComponent(unit)+'&note='+encodeURIComponent(note)})
  .then(function(r){return r.json();}).then(function(d){
    btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-paper-plane"></i> Gửi Yêu Cầu';
    if(d.status==='success'||d.status==='exists'||d.status==='already_approved'){
      alertOk.style.display='block';
      if(d.status==='success') alertOk.innerHTML='<i class="fa-solid fa-circle-check"></i> Gửi yêu cầu thành công! Admin sẽ duyệt sớm.';
      else if(d.status==='exists') alertOk.innerHTML='<i class="fa-solid fa-circle-check"></i> Device ID này đã được gửi rồi, đang chờ Admin duyệt.';
      else alertOk.innerHTML='<i class="fa-solid fa-circle-check"></i> Device ID này đã được duyệt và còn hạn!';
    } else {
      alertErr.style.display='block';alertErr.innerHTML='<i class="fa-solid fa-triangle-exclamation"></i> '+(d.msg||'Lỗi hệ thống!');
    }
  }).catch(function(){btn.disabled=false;btn.innerHTML='<i class="fa-solid fa-paper-plane"></i> Gửi Yêu Cầu';alertErr.style.display='block';alertErr.innerHTML='<i class="fa-solid fa-triangle-exclamation"></i> Lỗi kết nối máy chủ!';});
}
</script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(port=port, host='0.0.0.0', debug=False)
