import os
import json
import uuid
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="../admin", static_url_path="/admin")
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")

# Default database seed if file doesn't exist
DEFAULT_DB = {
    "courses": [
        {
            "id": 1,
            "title": "كورس هندسة وتصميم TRABUILD المتقدم",
            "description": "دورة احترافية شاملة لكافة برامج التصميم الهندسي وتطبيقات Revit والتصميم الإنشائي",
            "instructor": "مهندس ترابلد المعتمد",
            "lessons": [
                {
                    "id": 101,
                    "title": "المحاضرة 01: مقدمة في نظام TRABUILD وبيئة العمل",
                    "duration": "45:20 دقيقة",
                    "bunny_id": "sample_video_101",
                    "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
                },
                {
                    "id": 102,
                    "title": "المحاضرة 02: أدوات النمذجة المتقدمة وإدارة العناصر",
                    "duration": "58:45 دقيقة",
                    "bunny_id": "sample_video_102",
                    "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
                },
                {
                    "id": 103,
                    "title": "المحاضرة 03: إخراج المخططات النهائية وتصدير المشروع",
                    "duration": "50:15 دقيقة",
                    "bunny_id": "sample_video_103",
                    "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
                }
            ]
        }
    ],
    "licenses": [
        {
            "id": "1",
            "key": "TRABUILD-2026-IRAQ-7777",
            "student_name": "احمد علي حسين",
            "phone": "07701234567",
            "hwid": "",
            "status": "active",  # active, banned, waiting
            "course_ids": [1],
            "created_at": "2026-08-15 10:00:00",
            "last_active": "2026-08-15 12:00:00"
        },
        {
            "id": "2",
            "key": "TRABUILD-2026-IRAQ-8888",
            "student_name": "حسين قاسم عبد",
            "phone": "07809876543",
            "hwid": "",
            "status": "active",
            "course_ids": [1],
            "created_at": "2026-08-15 11:30:00",
            "last_active": "2026-08-15 11:30:00"
        }
    ]
}

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_pg_conn():
    if not DATABASE_URL:
        return None
    try:
        import psycopg2
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        print(f"[DB] PostgreSQL connection warning: {e}")
        return None

def init_pg_tables():
    conn = get_pg_conn()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trabuild_store (
                    id VARCHAR(50) PRIMARY KEY,
                    data JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("SELECT data FROM trabuild_store WHERE id = 'main';")
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "INSERT INTO trabuild_store (id, data) VALUES ('main', %s);",
                    [json.dumps(DEFAULT_DB)]
                )
            conn.commit()
            print("[DB] PostgreSQL initialized successfully!")
    except Exception as e:
        print(f"[DB] Error initializing PostgreSQL tables: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if DATABASE_URL:
    try:
        init_pg_tables()
    except Exception:
        pass

def load_db():
    conn = get_pg_conn()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM trabuild_store WHERE id = 'main';")
                row = cur.fetchone()
                if row and row[0]:
                    data = row[0]
                    if isinstance(data, str):
                        data = json.loads(data)
                    return data
        except Exception as e:
            print(f"[DB] Error loading from PostgreSQL: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # Fallback to local json file
    if not os.path.exists(DB_PATH):
        save_db(DEFAULT_DB)
        return DEFAULT_DB
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DB

def save_db(data):
    conn = get_pg_conn()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trabuild_store (id, data, updated_at) 
                    VALUES ('main', %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) 
                    DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP;
                """, [json.dumps(data)])
                conn.commit()
        except Exception as e:
            print(f"[DB] Error saving to PostgreSQL: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ----------------------------------------------------
# Static Admin Dashboard & Health Check Routes
# ----------------------------------------------------
@app.route("/healthz")
@app.route("/ping")
def health_check():
    return jsonify({"status": "ok", "service": "trabuild"}), 200
@app.route("/")
@app.route("/admin")
@app.route("/admin/")
def serve_admin():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/styles.css")
@app.route("/admin/styles.css")
def serve_styles():
    return send_from_directory(app.static_folder, "styles.css")

@app.route("/admin.js")
@app.route("/admin/admin.js")
def serve_js():
    return send_from_directory(app.static_folder, "admin.js")

@app.route("/admin/<path:path>")
def serve_admin_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/assets/<path:path>")
def serve_assets(path):
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    return send_from_directory(assets_dir, path)

def get_baghdad_time():
    """Returns formatted time strictly in Baghdad / Iraq local time (UTC+3)."""
    now_baghdad = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    return now_baghdad.strftime("%Y-%m-%d %I:%M:%S %p")

# ----------------------------------------------------
# Student Player API Endpoints
# ----------------------------------------------------

@app.route("/api/auth/activate", methods=["POST"])
def activate_license():
    data = request.json or {}
    license_key = data.get("license_key", "").strip()
    client_hwid = data.get("hwid", "").strip()

    if not license_key or not client_hwid:
        return jsonify({"success": False, "message": "بيانات التفعيل غير مكتملة (مطلوب الكود وبصمة الجهاز)."}), 400

    db = load_db()
    license_item = next((l for l in db["licenses"] if l["key"].upper() == license_key.upper()), None)

    if not license_item:
        return jsonify({"success": False, "message": "مفتاح الترخيص غير صالح أو غير موجود في النظام."}), 404

    # 1. Check if banned
    if license_item.get("status") == "banned":
        return jsonify({
            "success": False,
            "banned": True,
            "message": "تم حظر هذا الحساب من قبل الإدارة. يرجى التواصل مع الدعم الفني."
        }), 403

    # 2. Check Device Binding (HWID)
    bound_hwid = license_item.get("hwid", "")
    if not bound_hwid:
        # First time activation on this hardware -> bind it!
        license_item["hwid"] = client_hwid
        license_item["status"] = "active"
        license_item["last_active"] = get_baghdad_time()
        save_db(db)
    elif bound_hwid != client_hwid:
        return jsonify({
            "success": False,
            "hwid_mismatch": True,
            "message": f"عذراً! هذا الترخيص مفعل مسبقاً على جهاز آخر.\nالجهاز المسجل: ({bound_hwid[:8]}...)\nجهازك الحالي: ({client_hwid[:8]}...)\nلا يمكن مشاركة الترخيص."
        }), 403

    # Update last active
    license_item["last_active"] = get_baghdad_time()
    save_db(db)

    # Return student profile and courses
    allowed_course_ids = license_item.get("course_ids", [1])
    courses = [c for c in db["courses"] if c["id"] in allowed_course_ids]

    return jsonify({
        "success": True,
        "student": {
            "name": license_item["student_name"],
            "phone": license_item["phone"],
            "key": license_item["key"],
            "hwid": client_hwid,
            "status": license_item["status"]
        },
        "courses": courses
    })

@app.route("/api/auth/heartbeat", methods=["POST"])
def check_heartbeat():
    data = request.json or {}
    license_key = data.get("license_key", "").strip()
    client_hwid = data.get("hwid", "").strip()

    db = load_db()
    license_item = next((l for l in db["licenses"] if l["key"].upper() == license_key.upper()), None)

    if not license_item:
        return jsonify({"valid": False, "reason": "not_found", "message": "الترخيص غير موجود."}), 404

    if license_item.get("status") == "banned":
        return jsonify({"valid": False, "reason": "banned", "message": "تم حظر هذا الحساب فوراً من قبل الإدارة!"}), 403

    if license_item.get("hwid") and license_item.get("hwid") != client_hwid:
        return jsonify({"valid": False, "reason": "hwid_mismatch", "message": "عدم تطابق في بصمة الجهاز المصرح به."}), 403

    # Update last active timestamp
    license_item["last_active"] = get_baghdad_time()
    save_db(db)

    return jsonify({"valid": True, "status": license_item["status"]})

@app.route("/api/courses", methods=["GET"])
def get_courses():
    db = load_db()
    return jsonify({"success": True, "courses": db.get("courses", [])})

# ----------------------------------------------------
# Admin Dashboard API Endpoints
# ----------------------------------------------------

@app.route("/api/admin/stats", methods=["GET"])
def get_admin_stats():
    db = load_db()
    licenses = db.get("licenses", [])
    courses = db.get("courses", [])
    total_lessons = sum(len(c.get("lessons", [])) for c in courses)

    active_count = sum(1 for l in licenses if l.get("status") == "active")
    banned_count = sum(1 for l in licenses if l.get("status") == "banned")
    waiting_count = sum(1 for l in licenses if not l.get("hwid"))

    return jsonify({
        "success": True,
        "stats": {
            "total_students": len(licenses),
            "active_students": active_count,
            "banned_students": banned_count,
            "waiting_students": waiting_count,
            "total_courses": len(courses),
            "total_lessons": total_lessons
        }
    })

@app.route("/api/admin/licenses", methods=["GET"])
def get_admin_licenses():
    db = load_db()
    return jsonify({"success": True, "licenses": db.get("licenses", [])})

@app.route("/api/admin/licenses", methods=["POST"])
def create_license():
    data = request.json or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    course_id = int(data.get("course_id", 1))
    custom_key = data.get("custom_key", "").strip()

    if not name:
        return jsonify({"success": False, "message": "اسم الطالب مطلوب."}), 400

    if custom_key:
        generated_key = custom_key.upper()
    else:
        phone_clean = phone[-4:] if len(phone) >= 4 else "8888"
        rand_code = uuid.uuid4().hex[:4].upper()
        generated_key = f"TRABUILD-2026-{phone_clean}-{rand_code}"

    db = load_db()
    # Check if key already exists, if so update it
    existing = next((l for l in db.get("licenses", []) if l["key"].upper() == generated_key.upper()), None)
    if existing:
        existing["student_name"] = name
        existing["phone"] = phone or existing.get("phone", "")
        existing["course_ids"] = [course_id]
        save_db(db)
        return jsonify({"success": True, "message": "تم تحديث الترخيص وإعادة تفعيله بنجاح.", "license": existing})

    new_license = {
        "id": str(len(db.get("licenses", [])) + 1),
        "key": generated_key,
        "student_name": name,
        "phone": phone or "07700000000",
        "hwid": "",
        "status": "waiting",
        "course_ids": [course_id],
        "created_at": get_baghdad_time(),
        "last_active": "لم يسجل دخول بعد"
    }
    db.setdefault("licenses", []).append(new_license)
    save_db(db)

    return jsonify({"success": True, "license": new_license})

@app.route("/api/admin/licenses/<key>/toggle-ban", methods=["POST"])
def toggle_ban(key):
    db = load_db()
    license_item = next((l for l in db["licenses"] if l["key"].upper() == key.upper()), None)
    if not license_item:
        return jsonify({"success": False, "message": "الترخيص غير موجود."}), 404

    if license_item.get("status") == "banned":
        license_item["status"] = "active" if license_item.get("hwid") else "waiting"
        action = "unbanned"
    else:
        license_item["status"] = "banned"
        action = "banned"

    save_db(db)
    return jsonify({
        "success": True, 
        "action": action, 
        "new_status": license_item["status"],
        "message": f"تم {'حظر' if action == 'banned' else 'إلغاء حظر'} الطالب ({license_item['student_name']}) بنجاح."
    })

@app.route("/api/admin/licenses/<key>/reset-hwid", methods=["POST"])
def reset_hwid(key):
    db = load_db()
    license_item = next((l for l in db["licenses"] if l["key"].upper() == key.upper()), None)
    if not license_item:
        return jsonify({"success": False, "message": "الترخيص غير موجود."}), 404

    license_item["hwid"] = ""
    if license_item.get("status") != "banned":
        license_item["status"] = "waiting"

    save_db(db)
    return jsonify({
        "success": True, 
        "message": f"تم تصفير جهاز الطالب ({license_item['student_name']}). يمكنه الآن التفعيل على حاسبة جديدة."
    })

@app.route("/api/admin/licenses/<key>/delete", methods=["POST", "DELETE"])
def delete_license(key):
    db = load_db()
    initial_count = len(db["licenses"])
    target_name = ""
    for l in db["licenses"]:
        if l["key"].upper() == key.upper():
            target_name = l["student_name"]
            break
            
    db["licenses"] = [l for l in db["licenses"] if l["key"].upper() != key.upper()]
    if len(db["licenses"]) == initial_count:
        return jsonify({"success": False, "message": "الترخيص غير موجود."}), 404

    save_db(db)
    return jsonify({"success": True, "message": f"تم مسح حساب الطالب ({target_name}) نهائياً بنجاح."})

@app.route("/api/admin/courses/<int:course_id>/rename", methods=["POST"])
def rename_course(course_id):
    data = request.json or {}
    new_title = data.get("title", "").strip()
    if not new_title:
        return jsonify({"success": False, "message": "اسم الكورس مطلوب."}), 400

    db = load_db()
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    if not course:
        return jsonify({"success": False, "message": "الكورس غير موجود."}), 404

    course["title"] = new_title
    save_db(db)
    return jsonify({"success": True, "message": "تم تعديل اسم الكورس بنجاح.", "title": new_title})

@app.route("/api/admin/courses/<int:course_id>/lessons/<int:lesson_id>/delete", methods=["POST", "DELETE"])
def delete_lesson(course_id, lesson_id):
    db = load_db()
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    if not course:
        return jsonify({"success": False, "message": "الكورس غير موجود."}), 404

    initial_count = len(course.get("lessons", []))
    course["lessons"] = [l for l in course.get("lessons", []) if l["id"] != lesson_id]
    if len(course["lessons"]) == initial_count:
        return jsonify({"success": False, "message": "المحاضرة غير موجودة."}), 404

    save_db(db)
    return jsonify({"success": True, "message": "تم حذف المحاضرة بنجاح."})

@app.route("/api/admin/courses/<int:course_id>/lessons/<int:lesson_id>/update", methods=["POST", "PUT"])
def update_lesson(course_id, lesson_id):
    data = request.json or {}
    title = data.get("title", "").strip()
    duration = data.get("duration", "").strip()
    stream_url = data.get("stream_url", "").strip()
    bunny_id = data.get("bunny_id", "").strip()

    if not title or not stream_url:
        return jsonify({"success": False, "message": "عنوان المحاضرة ورابط الفيديو مطلوبان."}), 400

    db = load_db()
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    if not course:
        return jsonify({"success": False, "message": "الكورس غير موجود."}), 404

    lesson = next((l for l in course.get("lessons", []) if l["id"] == lesson_id), None)
    if not lesson:
        return jsonify({"success": False, "message": "المحاضرة غير موجودة."}), 404

    lesson["title"] = title
    if duration:
        lesson["duration"] = duration
    lesson["stream_url"] = stream_url
    if bunny_id:
        lesson["bunny_id"] = bunny_id

    save_db(db)
    return jsonify({"success": True, "message": "تم تعديل بيانات المحاضرة بنجاح.", "lesson": lesson})

@app.route("/api/admin/courses", methods=["POST"])
def add_lesson():
    data = request.json or {}
    course_id = int(data.get("course_id", 1))
    title = data.get("title", "").strip()
    duration = data.get("duration", "45:00 دقيقة").strip()
    stream_url = data.get("stream_url", "").strip()
    bunny_id = data.get("bunny_id", "").strip()

    if not title or not stream_url:
        return jsonify({"success": False, "message": "يرجى كتابة عنوان المحاضرة ورابط الفيديو أو معرف Bunny."}), 400

    db = load_db()
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    if not course:
        return jsonify({"success": False, "message": "الكورس غير موجود."}), 404

    new_lesson = {
        "id": int(f"{course_id}{len(course.get('lessons', [])) + 1:02d}"),
        "title": title,
        "duration": duration,
        "bunny_id": bunny_id or f"bunny_{uuid.uuid4().hex[:6]}",
        "stream_url": stream_url
    }
    course.setdefault("lessons", []).append(new_lesson)
    save_db(db)

    return jsonify({"success": True, "lesson": new_lesson})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[TRABUILD] Starting Trabuild Cloud API Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)


