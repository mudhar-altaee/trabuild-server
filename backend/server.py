import os
import json
import uuid
import datetime
import hashlib
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="../admin", static_url_path="/admin")
CORS(app)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Trabuild@2018@Trabuild@2026")

def get_admin_token():
    salt = "TRABUILD_SECURE_ADMIN_HASH_SALT_2026"
    return hashlib.sha256(f"{ADMIN_PASSWORD}_{salt}".encode("utf-8")).hexdigest()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        elif request.headers.get("X-Admin-Token"):
            token = request.headers.get("X-Admin-Token").strip()
        
        expected = get_admin_token()
        if not token or token != expected:
            return jsonify({"success": False, "message": "غير مصرح - مطلوب تسجيل دخول الإدارة."}), 401
        return f(*args, **kwargs)
    return decorated_function

DB_PATH = os.path.join(os.path.dirname(__file__), "database.json")

# Default database seed if file doesn't exist
DEFAULT_DB = {
    "courses": [
        {
            "description": "دورة احترافية شاملة لكافة برامج التصميم الهندسي وتطبيقات Revit والتصميم الإنشائي",
            "id": 1,
            "instructor": "مهندس ترابلد المعتمد",
            "lessons": [
                {
                    "bunny_id": "3e10d737-098d-459d-ac34-2501590ddd36",
                    "duration": "00:45:00 خمسة واربعين دقيقة",
                    "id": 103,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/3e10d737-098d-459d-ac34-2501590ddd36/playlist.m3u8",
                    "title": "المحاضرة 01 : استخدام الحاسوب"
                },
                {
                    "bunny_id": "ad1acda7-7f3d-48f0-a826-0687c21962fe",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 101,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/ad1acda7-7f3d-48f0-a826-0687c21962fe/playlist.m3u8",
                    "title": "المحاضرة 02 : مقدمة عن البرنامج"
                },
                {
                    "bunny_id": "3c4b4cd2-6654-46c0-9517-d7f8e201f10e",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 102,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/3c4b4cd2-6654-46c0-9517-d7f8e201f10e/playlist.m3u8",
                    "title": "المحاضرة 03 : شرح (views)"
                },
                {
                    "bunny_id": "4cf8eede-ee78-48ba-be8b-ca282f3cc06f",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 104,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/4cf8eede-ee78-48ba-be8b-ca282f3cc06f/playlist.m3u8",
                    "title": "المحاضرة 04 : شرح (walls)"
                },
                {
                    "bunny_id": "5979bc80-60d4-4fbc-a5d5-46fa13978929",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 105,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/5979bc80-60d4-4fbc-a5d5-46fa13978929/playlist.m3u8",
                    "title": "المحاضرة 05 : شرح (Floors & Curtain walls)"
                },
                {
                    "bunny_id": "bcbdba58-e5cc-4532-a8d2-68a787794028",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 106,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/bcbdba58-e5cc-4532-a8d2-68a787794028/playlist.m3u8",
                    "title": "المحاضرة 06 : (Ai Render & Curtain walls)"
                },
                {
                    "bunny_id": "57548971-22f9-4c56-8b8f-fc21697fff40",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 107,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/57548971-22f9-4c56-8b8f-fc21697fff40/playlist.m3u8",
                    "title": "المحاضرة 07 : تطبيق عملي"
                },
                {
                    "bunny_id": "bdce8bb4-c845-4524-949f-e4210e95165c",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 108,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/bdce8bb4-c845-4524-949f-e4210e95165c/playlist.m3u8",
                    "title": "المحاضرة 08 : شرح ( Roof & Dimensions )"
                },
                {
                    "bunny_id": "398a542b-dc7e-4139-85ba-d1b7cd86f8e8",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 109,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/398a542b-dc7e-4139-85ba-d1b7cd86f8e8/playlist.m3u8",
                    "title": "المحاضرة 09 : شرح (Modification Tools)"
                },
                {
                    "bunny_id": "ee8109a9-b0f8-4b85-9ed1-92db25f254a9",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 110,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/ee8109a9-b0f8-4b85-9ed1-92db25f254a9/playlist.m3u8",
                    "title": "المحاضرة 10 : شرح (stairs)"
                },
                {
                    "bunny_id": "65a81b01-ccc2-49b0-8039-13aca216fb3c",
                    "duration": "1:30:00 ساعة ونصف",
                    "id": 111,
                    "stream_url": "https://vz-6e61c2b5-302.b-cdn.net/65a81b01-ccc2-49b0-8039-13aca216fb3c/playlist.m3u8",
                    "title": "المحاضرة 11 : شرح (visibility & graphics)"
                }
            ],
            "title": "Revit Architecture 2027 - رفت معماري 2027"
        }
    ],
    "licenses": [
        {
            "allowed_hwids": [
                "HWID-WIN-2B5850029A5C"
            ],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "HWID-WIN-2B5850029A5C",
            "id": "1",
            "key": "TRABUILD-2026-6843-A60A",
            "last_active": "2026-08-24 06:00:00 PM",
            "phone": "07706843000",
            "status": "active",
            "student_name": "يونس نبيل حميد"
        },
        {
            "allowed_hwids": [
                "HWID-WIN-3CE5C44614B8",
                "HWID-WIN-7B5954D83D51"
            ],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "HWID-WIN-3CE5C44614B8",
            "id": "2",
            "key": "TRABUILD-2026-1859-B75B",
            "last_active": "2026-09-19 04:34:16 PM",
            "phone": "07722501859",
            "status": "active",
            "student_name": "زينب عبد الرزاق حسين"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "3",
            "key": "TRABUILD-2026-3663-0BCB",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07703663000",
            "status": "waiting",
            "student_name": "سجى نبيل شريف"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "4",
            "key": "TRABUILD-2026-9745-56A0",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07709745000",
            "status": "waiting",
            "student_name": "دانية محمد خليل"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "5",
            "key": "TRABUILD-2026-6667-C6AD",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07706667000",
            "status": "waiting",
            "student_name": "كوثر حسن موسى"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "6",
            "key": "TRABUILD-2026-1196-A126",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07701196000",
            "status": "waiting",
            "student_name": "ايات احمد عباس"
        },
        {
            "allowed_hwids": [
                "HWID-WIN-8C668D6B9ED7"
            ],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "HWID-WIN-8C668D6B9ED7",
            "id": "7",
            "key": "TRABUILD-2026-4452-9A1A",
            "last_active": "2026-09-19 03:32:28 PM",
            "phone": "07704452000",
            "status": "active",
            "student_name": "مضر المعمار"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "8",
            "key": "TRABUILD-2026-0050-B5F2",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07700050000",
            "status": "waiting",
            "student_name": "ليليان ليث خالص"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "9",
            "key": "TRABUILD-2026-8899-284C",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07708899000",
            "status": "waiting",
            "student_name": "قمر احمد جابر"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "10",
            "key": "TRABUILD-2026-7130-F1CE",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07707130000",
            "status": "waiting",
            "student_name": "محمد ناظم داود"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "11",
            "key": "TRABUILD-2026-8663-A825",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07708663000",
            "status": "waiting",
            "student_name": "ديما عمر يوسف"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "12",
            "key": "TRABUILD-2026-5317-FABC",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07705317000",
            "status": "waiting",
            "student_name": "رتاج منتصر هاشم"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "13",
            "key": "TRABUILD-2026-2431-580A",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07702431000",
            "status": "waiting",
            "student_name": "احمد رفعت محمد"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "14",
            "key": "TRABUILD-2026-1710-0A31",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07701710000",
            "status": "waiting",
            "student_name": "حوراء حسين رسه"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "15",
            "key": "TRABUILD-2026-6289-B0B1",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07706289000",
            "status": "waiting",
            "student_name": "ياسر حيدر محمد"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "16",
            "key": "TRABUILD-2026-3624-657A",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07703624000",
            "status": "waiting",
            "student_name": "عبد الله احمد عبد الله"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "17",
            "key": "TRABUILD-2026-1686-D285",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07701686000",
            "status": "waiting",
            "student_name": "الحسن باسم محمد"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "18",
            "key": "TRABUILD-2026-8888-90C7",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07708888000",
            "status": "waiting",
            "student_name": "هشام ال"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "19",
            "key": "TRABUILD-2026-3950-F618",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07703950000",
            "status": "waiting",
            "student_name": "قمر نورس كاظم"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "20",
            "key": "TRABUILD-2026-4376-04BA",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07704376000",
            "status": "waiting",
            "student_name": "مريم حميد مزيعل"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "21",
            "key": "TRABUILD-2026-2568-C690",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07702568000",
            "status": "waiting",
            "student_name": "علي خضير عباس"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "22",
            "key": "TRABUILD-2026-8533-1A0D",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07708533000",
            "status": "banned",
            "student_name": "مصطفى ثائر علي"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "23",
            "key": "TRABUILD-2026-6366-9DBF",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07706366000",
            "status": "waiting",
            "student_name": "محمد احمد صالح"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "24",
            "key": "TRABUILD-2026-2887-59FE",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07702887000",
            "status": "waiting",
            "student_name": "رقية حافظ صاحب"
        },
        {
            "allowed_hwids": [],
            "course_ids": [
                1
            ],
            "created_at": "2026-08-18 12:00:00 PM",
            "hwid": "",
            "id": "25",
            "key": "TRABUILD-2026-0000-2C0E",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07700000000",
            "status": "waiting",
            "student_name": "رقية حسين محمد"
        },
        {
            "course_ids": [
                1
            ],
            "created_at": "2026-09-19 03:25:09 PM",
            "hwid": "",
            "id": "26",
            "key": "TRABUILD-2026-8563-0626",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07712438563",
            "status": "waiting",
            "student_name": "قمر احمد ابراهيم"
        },
        {
            "course_ids": [
                1
            ],
            "created_at": "2026-09-19 03:25:58 PM",
            "hwid": "",
            "id": "27",
            "key": "TRABUILD-2026-6150-B494",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07783346150",
            "status": "waiting",
            "student_name": "شهد هيثم مانع"
        },
        {
            "course_ids": [
                1
            ],
            "created_at": "2026-09-19 03:26:52 PM",
            "hwid": "",
            "id": "28",
            "key": "TRABUILD-2026-5068-59CD",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07711485068",
            "status": "waiting",
            "student_name": "ميسم قاسم عبدالرضا"
        },
        {
            "course_ids": [
                1
            ],
            "created_at": "2026-09-19 03:27:52 PM",
            "hwid": "",
            "id": "29",
            "key": "TRABUILD-2026-4452-57BB",
            "last_active": "لم يسجل دخول بعد",
            "phone": "07854814949",
            "status": "waiting",
            "student_name": "العراب الاصلي"
        }
    ]
}

DATABASE_URL = os.environ.get("DATABASE_URL")
LAST_DB_ERROR = ""

def ensure_seed_consistency(data):
    """
    Ensure all default seed courses and student licenses exist in the data
    without ever overwriting newly registered HWIDs, last_active dates, or new courses/lessons.
    """
    if not isinstance(data, dict):
        return DEFAULT_DB, True
    
    # 1. Merge licenses
    existing_lics = data.setdefault("licenses", [])
    existing_keys = {l.get("key"): l for l in existing_lics if isinstance(l, dict) and l.get("key")}
    
    modified = False
    for def_lic in DEFAULT_DB.get("licenses", []):
        k = def_lic.get("key")
        if not k:
            continue
        if k not in existing_keys:
            existing_lics.append(def_lic)
            existing_keys[k] = def_lic
            modified = True
        else:
            cur_lic = existing_keys[k]
            if not cur_lic.get("hwid") and def_lic.get("hwid"):
                cur_lic["hwid"] = def_lic["hwid"]
                cur_lic["status"] = def_lic.get("status", "active")
                cur_lic["allowed_hwids"] = def_lic.get("allowed_hwids", [def_lic["hwid"]])
                modified = True
    
    # 2. Merge courses & lessons
    existing_courses = data.setdefault("courses", [])
    existing_course_map = {c.get("id"): c for c in existing_courses if isinstance(c, dict) and c.get("id")}
    
    for def_c in DEFAULT_DB.get("courses", []):
        cid = def_c.get("id")
        if cid not in existing_course_map:
            existing_courses.append(def_c)
            existing_course_map[cid] = def_c
            modified = True
        else:
            cur_c = existing_course_map[cid]
            cur_lessons = cur_c.setdefault("lessons", [])
            cur_lesson_ids = {l.get("id") for l in cur_lessons if isinstance(l, dict)}
            for def_l in def_c.get("lessons", []):
                if def_l.get("id") not in cur_lesson_ids:
                    cur_lessons.append(def_l)
                    cur_lesson_ids.add(def_l.get("id"))
                    modified = True
                    
    return data, modified

def get_pg_conn():
    global LAST_DB_ERROR
    if not DATABASE_URL:
        return None
    try:
        import psycopg2
        url = DATABASE_URL.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        # Try direct connection first (works for Neon, Supabase, Render internal URLs, standard Postgres)
        try:
            return psycopg2.connect(url, connect_timeout=5)
        except Exception as err_direct:
            # If it's an unexpanded Render hostname connecting from an external network
            if "@dpg-" in url and ".render.com" not in url:
                import re
                url_ext = re.sub(r"@(dpg-[^:/]+)([:/])", r"@\1.frankfurt-postgres.render.com\2", url)
                if "sslmode=" not in url_ext:
                    url_ext += ("&" if "?" in url_ext else "?") + "sslmode=require"
                return psycopg2.connect(url_ext, connect_timeout=5)
            raise err_direct
    except Exception as e:
        LAST_DB_ERROR = str(e)
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
            else:
                existing = row[0]
                if isinstance(existing, str):
                    existing = json.loads(existing)
                merged, modified = ensure_seed_consistency(existing)
                if modified:
                    cur.execute(
                        "UPDATE trabuild_store SET data = %s, updated_at = CURRENT_TIMESTAMP WHERE id = 'main';",
                        [json.dumps(merged)]
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
                    data, modified = ensure_seed_consistency(data)
                    if modified:
                        save_db(data)
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
            data = json.load(f)
            data, modified = ensure_seed_consistency(data)
            if modified:
                save_db(data)
            return data
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
    db_status = "local"
    conn = None
    err_msg = ""
    try:
        conn = get_pg_conn()
        if conn:
            db_status = "postgres"
            conn.close()
        elif DATABASE_URL:
            db_status = "postgres_failed"
    except Exception as e:
        err_msg = str(e)

    db_host = ""
    if DATABASE_URL:
        try:
            import urllib.parse
            db_host = urllib.parse.urlparse(DATABASE_URL).hostname or ""
        except Exception:
            pass

    return jsonify({
        "status": "ok",
        "service": "trabuild",
        "db": db_status,
        "db_host": db_host,
        "error": LAST_DB_ERROR
    }), 200
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

    # 2. Strict 1-Device Machine Lock with Multi-Adapter Stability
    bound_hwid = license_item.get("hwid", "").strip()
    allowed_hwids = license_item.setdefault("allowed_hwids", [])
    if bound_hwid and bound_hwid not in allowed_hwids:
        allowed_hwids.append(bound_hwid)

    if not bound_hwid or len(allowed_hwids) == 0:
        # First-time activation -> Lock permanently to this student's computer!
        license_item["hwid"] = client_hwid
        license_item["allowed_hwids"] = [client_hwid]
        license_item["status"] = "active"
        license_item["last_active"] = get_baghdad_time()
        save_db(db)
    elif client_hwid == bound_hwid or client_hwid in allowed_hwids:
        # Authorized original computer -> allow smooth login
        license_item["status"] = "active"
        license_item["last_active"] = get_baghdad_time()
        save_db(db)
    elif len(allowed_hwids) < 4:
        # Same single physical laptop adapter variations across reboots/sleep/Wi-Fi states
        allowed_hwids.append(client_hwid)
        license_item["status"] = "active"
        license_item["last_active"] = get_baghdad_time()
        save_db(db)
    else:
        # A completely DIFFERENT / SECOND laptop attempting to use the license -> STRICT BLOCK!
        return jsonify({
            "success": False,
            "hwid_mismatch": True,
            "message": f"عذراً! هذا الترخيص مقفل على جهاز الطالب الأصلي فقط ولا يمكن تشغيله على حاسبة أخرى.\nإذا قمت بتغيير حاسبتك يرجى مراجعة إدارة الكورس لتصفير الترخيص."
        }), 403

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

    allowed_hwids = license_item.get("allowed_hwids", [])
    bound_hwid = license_item.get("hwid", "")
    if bound_hwid and (client_hwid != bound_hwid and client_hwid not in allowed_hwids):
        return jsonify({"valid": False, "reason": "hwid_mismatch", "message": "عدم تطابق في بصمة الجهاز المصرح به."}), 403

    # Update last active timestamp
    license_item["last_active"] = get_baghdad_time()
    save_db(db)

    return jsonify({"valid": True, "status": license_item["status"]})

@app.route("/api/courses", methods=["GET"])
def get_courses():
    # Require either admin token or active student license
    auth_header = request.headers.get("Authorization", "")
    admin_token = ""
    if auth_header.startswith("Bearer "):
        admin_token = auth_header.split(" ", 1)[1].strip()
    elif request.headers.get("X-Admin-Token"):
        admin_token = request.headers.get("X-Admin-Token").strip()

    is_admin = (admin_token and admin_token == get_admin_token())

    student_key = (
        request.headers.get("X-License-Key") or 
        request.args.get("license_key") or 
        request.args.get("key")
    )
    db = load_db()

    is_student_valid = False
    if student_key:
        lic = next((l for l in db.get("licenses", []) if l["key"].upper() == student_key.strip().upper()), None)
        if lic and lic.get("status") == "active":
            is_student_valid = True

    if not is_admin and not is_student_valid:
        return jsonify({
            "success": False, 
            "message": "غير مصرح - يتطلب ترخيص طالب نشط أو تسجيل دخول الإدارة."
        }), 401

    return jsonify({"success": True, "courses": db.get("courses", [])})

# ----------------------------------------------------
# Admin Dashboard API Endpoints (Secured with @admin_required)
# ----------------------------------------------------

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.json or {}
    pwd = data.get("password", "").strip()
    if pwd == ADMIN_PASSWORD:
        return jsonify({
            "success": True,
            "token": get_admin_token(),
            "message": "تم تسجيل دخول الإدارة بنجاح."
        })
    return jsonify({
        "success": False,
        "message": "كلمة المرور غير صحيحة! يرجى المحاولة مرة أخرى."
    }), 401

@app.route("/api/admin/verify", methods=["GET", "POST"])
@admin_required
def admin_verify():
    return jsonify({"success": True, "valid": True})

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
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
@admin_required
def get_admin_licenses():
    db = load_db()
    return jsonify({"success": True, "licenses": db.get("licenses", [])})

@app.route("/api/admin/licenses", methods=["POST"])
@admin_required
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
@admin_required
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
@admin_required
def reset_hwid(key):
    db = load_db()
    license_item = next((l for l in db["licenses"] if l["key"].upper() == key.upper()), None)
    if not license_item:
        return jsonify({"success": False, "message": "الترخيص غير موجود."}), 404

    license_item["hwid"] = ""
    license_item["allowed_hwids"] = []
    if license_item.get("status") != "banned":
        license_item["status"] = "waiting"

    save_db(db)
    return jsonify({
        "success": True, 
        "message": f"تم تصفير جهاز الطالب ({license_item['student_name']}). يمكنه الآن التفعيل على حاسبة جديدة."
    })

@app.route("/api/admin/licenses/<key>/delete", methods=["POST", "DELETE"])
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def add_lesson():
    data = request.json or {}
    course_id = int(data.get("course_id", 1))
    title = data.get("title", "").strip()
    duration = data.get("duration", "45:00 دقيقة").strip()
    stream_url = data.get("stream_url", "").strip()
    bunny_id = data.get("bunny_id", "").strip()
    position = data.get("position", "bottom").strip() # "top" or "bottom"

    if not title or not stream_url:
        return jsonify({"success": False, "message": "يرجى كتابة عنوان المحاضرة ورابط الفيديو أو معرف Bunny."}), 400

    db = load_db()
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    if not course:
        return jsonify({"success": False, "message": "الكورس غير موجود."}), 404

    # Calculate safe unique lesson ID
    all_existing_ids = [l["id"] for c in db["courses"] for l in c.get("lessons", [])]
    next_id = max(all_existing_ids, default=100) + 1

    new_lesson = {
        "id": next_id,
        "title": title,
        "duration": duration,
        "bunny_id": bunny_id or f"bunny_{uuid.uuid4().hex[:6]}",
        "stream_url": stream_url
    }
    
    lessons = course.setdefault("lessons", [])
    if position == "top":
        lessons.insert(0, new_lesson)
    else:
        lessons.append(new_lesson)

    save_db(db)
    return jsonify({"success": True, "message": "تمت إضافة المحاضرة بنجاح.", "lesson": new_lesson})

@app.route("/api/admin/courses/<int:course_id>/lessons/<int:lesson_id>/move", methods=["POST"])
@admin_required
def move_lesson(course_id, lesson_id):
    data = request.json or {}
    direction = data.get("direction", "up").strip() # "up" or "down"

    db = load_db()
    course = next((c for c in db["courses"] if c["id"] == course_id), None)
    if not course:
        return jsonify({"success": False, "message": "الكورس غير موجود."}), 404

    lessons = course.get("lessons", [])
    index = next((i for i, l in enumerate(lessons) if l["id"] == lesson_id), -1)
    if index == -1:
        return jsonify({"success": False, "message": "المحاضرة غير موجودة."}), 404

    if direction == "up" and index > 0:
        lessons[index], lessons[index - 1] = lessons[index - 1], lessons[index]
    elif direction == "down" and index < len(lessons) - 1:
        lessons[index], lessons[index + 1] = lessons[index + 1], lessons[index]
    else:
        return jsonify({"success": False, "message": "لا يمكن تحريك المحاضرة أكثر في هذا الاتجاه."}), 400

    save_db(db)
    return jsonify({"success": True, "message": "تم تغيير ترتيب المحاضرة بنجاح."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[TRABUILD] Starting Trabuild Cloud API Server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)


