from flask import Flask, request, render_template, session,redirect,url_for,jsonify,send_from_directory
import pymysql
import bcrypt
import os,certifi
from datetime import timedelta
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import time
load_dotenv()


app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
app.permanent_session_lifetime = timedelta(days=int(os.getenv("SESSION_DAYS", "7")))


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "4000"))  # TiDB Cloud 默认 4000
DB_USER = os.getenv("DB_USER") or os.getenv("DB_USERNAME", "demo")
DB_PASS = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD", "demo")
DB_NAME = os.getenv("DB_NAME") or os.getenv("DB_DATABASE", "ai_learning_coach")

DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")
SEMESTER_CODE = os.getenv("SEMESTER_CODE", "2025T1")

WEEK_LABELS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

ALLOWED_EXTS = {"pdf"}
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "16")) * 1024 * 1024  # 16MB
# 上传根目录（可用 .env 配置 UPLOAD_ROOT；Docker 下建议挂载为卷）
# UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", "/app/uploads") # 会上传到C盘，测试时
# Path(UPLOAD_ROOT).mkdir(parents=True, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = str((BASE_DIR / "uploads").resolve())
Path(UPLOAD_ROOT).mkdir(parents=True, exist_ok=True)

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS

@app.get("/upload_material")
def upload_material_page():
    if "student_id" not in session:
        return redirect(url_for("index"))
    return render_template("upload_material.html")

@app.post("/materials/upload")
def upload_material():
    # 1) 校验登录
    uid = session.get("student_id")
    if not uid:
        return jsonify({"ok": False, "msg": "Not logged in"}), 401

    # 2) 取文件
    if "file" not in request.files:
        return jsonify({"ok": False, "msg": "No file part"}), 400
    f = request.files["file"]
    if not f or f.filename == "":
        return jsonify({"ok": False, "msg": "No selected file"}), 400
    if not _allowed_file(f.filename):
        return jsonify({"ok": False, "msg": "Only PDF is allowed"}), 400

    # 3) 保存到磁盘：uploads/<uid>/<毫秒时间戳>_原文件名.pdf
    user_dir = Path(UPLOAD_ROOT) / str(uid)
    user_dir.mkdir(parents=True, exist_ok=True)

    original = secure_filename(f.filename)
    saved_name = f"{int(time.time() * 1000)}_{original}"
    save_path = user_dir / saved_name

    try:
        f.save(save_path)
    except Exception as e:
        print("[UPLOAD SAVE ERROR]", repr(e))
        return jsonify({"ok": False, "msg": "Save failed"}), 500

    # 4) 写入数据库
    desc = (request.form.get("description") or "").strip() or None
    try:
        conn = get_conn()  # 复用你现有的连接函数
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_materials
                  (owner_id, filename_original, filename_saved, description)
                VALUES (%s, %s, %s, %s)
                """,
                (uid, original, saved_name, desc)
            )
        # 如果你的 get_conn() 没开 autocommit，这里确保提交：
        try:
            conn.commit()
        except Exception:
            pass
        conn.close()
    except Exception as e:
        print("[UPLOAD DB ERROR]", repr(e))
        # DB 失败时，删除刚保存的文件，避免磁盘留下脏文件
        try:
            if save_path.exists():
                save_path.unlink()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": "DB error"}), 500

    # 5) 表单来源：从页面提交则回跳，否则返回 JSON
    ref = request.headers.get("Referer")
    return redirect(ref) if ref else jsonify({"ok": True, "msg": "Uploaded", "filename": original})

@app.get("/materials/list")
def list_materials():
    uid = session.get("student_id")
    if not uid:
        return jsonify({"ok": False, "msg": "Not logged in"}), 401

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, filename_original, filename_saved, description, uploaded_at
            FROM user_materials
            WHERE owner_id=%s
            ORDER BY uploaded_at DESC, id DESC
            """,
            (uid,)
        )
        rows = cur.fetchall() or []
    conn.close()

    data = [{
        "id": r["id"],
        "filename": r["filename_original"],
        "url": url_for("download_material_by_id", material_id=r["id"]),
        "description": r.get("description"),
        "uploaded_at": str(r.get("uploaded_at")),
    } for r in rows]

    return jsonify({"ok": True, "data": data})

@app.get("/materials/file/id/<int:material_id>")
def download_material_by_id(material_id: int):
    uid = session.get("student_id")
    if not uid:
        return redirect(url_for("index"))

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT filename_original, filename_saved FROM user_materials WHERE id=%s AND owner_id=%s",
            (material_id, uid)
        )
        row = cur.fetchone()
    conn.close()

    if not row:
        return "File not found", 404

    user_dir = Path(UPLOAD_ROOT) / str(uid)
    file_path = user_dir / row["filename_saved"]
    if not file_path.exists():
        return "File missing on disk", 404

    return send_from_directory(
        directory=str(user_dir),
        path=row["filename_saved"],
        as_attachment=True,
        download_name=row["filename_original"],
        mimetype="application/pdf"
    )





def days_to_bitmask(selected_days):  # ['Mon','Sun'] -> int
    bit = 0
    for i, name in enumerate(WEEK_LABELS):
        if name in selected_days:
            bit |= (1 << i)
    return bit

def bitmask_to_days(bit):            # int -> ['Mon','Sun']
    return [WEEK_LABELS[i] for i in range(7) if (bit & (1 << i))]



def get_conn():
    
    return pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT) if DB_PORT else 4000,  # ⭐ TiDB 默认端口 4000
        user=DB_USER or os.getenv("DB_USERNAME"),
        password=DB_PASS or os.getenv("DB_PASSWORD"),
        database=DB_NAME or os.getenv("DB_DATABASE"),
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ca": certifi.where()},  # ⭐ 必须加，启用 TLS 连接
        connect_timeout=5,
    )


@app.route("/welcome")
def welcome():
    if "student_id" not in session:
        return redirect(url_for("index"))
    sid = session["student_id"]

    # 取该学生已选课程；LEFT JOIN 是为了即便 courses 表没名字也能展示 code
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT sc.course_code, COALESCE(c.course_name, '') AS course_name
            FROM student_courses sc
            LEFT JOIN courses c ON c.course_code = sc.course_code
            WHERE sc.student_id = %s
            ORDER BY sc.course_code
        """, (sid,))
        courses = cur.fetchall()
        cur.execute("""
                SELECT week_no, daily_hours, weekly_study_days, avoid_days_bitmask, mode, derived_from_week_no
                FROM student_weekly_preferences
                WHERE student_id=%s AND semester_code=%s
                ORDER BY week_no DESC
                LIMIT 1
            """, (sid, SEMESTER_CODE))
        pref = cur.fetchone()
        cur.execute("""
            SELECT MAX(week_no) AS maxw
            FROM student_weekly_preferences
            WHERE student_id=%s AND semester_code=%s
        """, (sid, SEMESTER_CODE))
        r = cur.fetchone()

    conn.close()

    current_week = 1 if not r or not r["maxw"] else min(10, int(r["maxw"]) + 1)
    if pref:
        pref["avoid_days_list"] = bitmask_to_days(pref["avoid_days_bitmask"])

    return render_template(
        "welcome.html",
        identifier=sid,
        courses=courses,
        pref=pref,
        semester=SEMESTER_CODE,
        current_week=current_week
    )
@app.route("/api/prefs/prev")
def api_prefs_prev():
    if "student_id" not in session:
        return {"ok": False, "error": "unauthorized"}, 401

    try:
        week_no = int(request.args.get("week_no", "2"))
    except Exception:
        week_no = 2
    if week_no <= 1:
        return {"ok": False, "error": "no previous week"}, 400

    sid = session["student_id"]
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT daily_hours, weekly_study_days, avoid_days_bitmask
            FROM student_weekly_preferences
            WHERE student_id=%s AND semester_code=%s AND week_no=%s
        """, (sid, SEMESTER_CODE, week_no - 1))
        row = cur.fetchone()
    conn.close()

    if not row:
        return {"ok": False, "error": "prev not found"}, 404
    return {"ok": True, "data": row}

# ========= 偏好：保存（Confirm） =========
@app.route("/api/prefs/save", methods=["POST"])
def save_prefs():
    if "student_id" not in session:
        return redirect(url_for("index"))
    sid = session["student_id"]

    # 读表单
    try:
        week_no = int(request.form.get("week_no", "1"))
    except Exception:
        week_no = 1
    mode = (request.form.get("mode") or "manual").lower()
    if week_no <= 1:
        mode = "manual"  # 第1周强制手动

    try:
        conn = get_conn()
        with conn.cursor() as cur:
            if mode == "default":
                # 后端直接用上一周的值，确保可信
                cur.execute("""
                    SELECT daily_hours, weekly_study_days, avoid_days_bitmask
                    FROM student_weekly_preferences
                    WHERE student_id=%s AND semester_code=%s AND week_no=%s
                """, (sid, SEMESTER_CODE, week_no - 1))
                prev = cur.fetchone()
                if not prev:
                    conn.close()
                    return redirect(url_for("welcome"))

                cur.execute("""
                    INSERT INTO student_weekly_preferences
                    (student_id, semester_code, week_no, daily_hours, weekly_study_days, avoid_days_bitmask, mode, derived_from_week_no)
                    VALUES (%s,%s,%s,%s,%s,%s,'default',%s)
                    ON DUPLICATE KEY UPDATE
                      daily_hours=VALUES(daily_hours),
                      weekly_study_days=VALUES(weekly_study_days),
                      avoid_days_bitmask=VALUES(avoid_days_bitmask),
                      mode='default',
                      derived_from_week_no=VALUES(derived_from_week_no)
                """, (sid, SEMESTER_CODE, week_no,
                      prev["daily_hours"], prev["weekly_study_days"], prev["avoid_days_bitmask"], week_no - 1))
            else:
                # manual：使用表单值
                try:
                    dh = float(request.form.get("daily_hours", "0"))
                    wsd = int(request.form.get("weekly_study_days", "0"))
                except Exception:
                    dh, wsd = 0.0, 0
                days_selected = request.form.getlist("avoid_days")
                mask = days_to_bitmask(days_selected)

                cur.execute("""
                    INSERT INTO student_weekly_preferences
                    (student_id, semester_code, week_no, daily_hours, weekly_study_days, avoid_days_bitmask, mode, derived_from_week_no)
                    VALUES (%s,%s,%s,%s,%s,%s,'manual',NULL)
                    ON DUPLICATE KEY UPDATE
                      daily_hours=VALUES(daily_hours),
                      weekly_study_days=VALUES(weekly_study_days),
                      avoid_days_bitmask=VALUES(avoid_days_bitmask),
                      mode='manual',
                      derived_from_week_no=NULL
                """, (sid, SEMESTER_CODE, week_no, dh, wsd, mask))
        conn.close()
        return redirect(url_for("welcome"))
    except Exception as e:
        print("[SAVE_PREFS ERROR]", repr(e))
        try:
            conn.close()
        except:
            pass
        return redirect(url_for("welcome"))   
@app.route("/logout")
def logout():
    session.clear()                 # clear the status 
    return redirect(url_for("index"))  # back to first page(login/register)

@app.route("/")
def index():
    #  templates/index.html
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    student_id = (request.form.get("student_id") or "").strip()
    email      = (request.form.get("email") or "").strip()
    password   = (request.form.get("password") or "")

    if not student_id or not email or not password:
        return render_template("index.html", message="Please enter your zid, email and password")

    try:
        # bcrypt 哈希
        password_bytes = password.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        conn = get_conn()
        with conn.cursor() as cur:
            sql = """
                INSERT INTO student_accounts (student_id, email, password_hash)
                VALUES (%s, %s, %s)
            """
            cur.execute(sql, (student_id, email, hashed))
        conn.close()

        return render_template("index.html", message="注册成功！")

    except pymysql.err.IntegrityError as e:
        # 唯一键冲突（学号/邮箱重复）
        return render_template("index.html", message="学号或邮箱已存在，请更换后再试。")

    except UnicodeEncodeError as e:
        # 典型：数据库登录密码含非 ASCII 字符导致握手失败
        return render_template(
            "index.html",
            message="数据库连接失败：请将 MySQL 登录密码改为仅包含 ASCII 的字符（英⽂/数字/常见符号）。"
        )

    except Exception as e:
        # 其他错误打印在控制台，页面返回通用提示
        print("[REGISTER ERROR]", repr(e))
        return render_template("index.html", message="注册失败：服务器内部错误，请检查后端日志。")
    

@app.route("/choose-courses", methods=["GET", "POST"])
def choose_courses():
    # 登录保护
    if "student_id" not in session:
        return redirect(url_for("index"))
    sid = session["student_id"]

    if request.method == "GET":
        return render_template("choose_courses.html")

    # POST: 单课程增量添加（必须存在于 courses 表中）
    code = (request.form.get("course_code") or "").strip().upper()
    if not code:
        return render_template("choose_courses.html", message="请输入课程代码。")

    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # 检查 courses 表中是否存在该课程
            cur.execute("SELECT 1 FROM courses WHERE course_code=%s LIMIT 1", (code,))
            if not cur.fetchone():
                conn.close()
                return render_template(
                    "choose_courses.html",
                    message=f"没有查询到该课程：{code}"
                )

            # ② 检查该学生是否已经选过这门课
            cur.execute(
                "SELECT 1 FROM student_courses WHERE student_id=%s AND course_code=%s LIMIT 1",
                (sid, code)
            )
            if cur.fetchone():
                conn.close()
                return redirect(url_for("materials_of_course", course_code=code))
                # return render_template(
                #     "choose_courses.html",
                #     message=f"已存在：{code}（无需重复添加）"
                # )

            # 插入新选课记录
            cur.execute(
                "INSERT INTO student_courses (student_id, course_code) VALUES (%s, %s)",
                (sid, code)
            )
        conn.close()
        
        return redirect(url_for("materials_of_course", course_code=code))
        #return render_template("choose_courses.html", message=f"已添加：{code}")

    except Exception as e:
        print("[CHOOSE COURSE ERROR]", repr(e))
        return render_template(
            "choose_courses.html",
            message="fail! Server Error!"
        )

@app.route("/materials/<course_code>")
def materials_of_course(course_code):

    if "student_id" not in session:
        return redirect(url_for("index"))
    code = (course_code or "").upper()
    # 这里现在不查资料，先显示空页面
    return render_template("materials.html", code=code)

@app.route("/show_my_material/<course_code>")
def show_my_material(course_code):
    if "student_id" not in session:
        return redirect(url_for("index"))
    code = (course_code or "").upper()
    return render_template("show_my_material.html", code=code)

@app.route("/login", methods=["POST"])
def login():
    identifier = (request.form.get("identifier") or "").strip()
    password   = request.form.get("password") or ""

    if not identifier or not password:
        return render_template("index.html", message="请填写账号和密码。")

    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT student_id, email, password_hash FROM student_accounts "
                "WHERE student_id=%s OR email=%s LIMIT 1",
                (identifier, identifier)
            )
            row = cur.fetchone()
        conn.close()

        if not row:
            return render_template("index.html", message="账号不存在。")

        ok = bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8"))
        if ok:
            #  关键：写入 session，后续受保护页面才能识别已登录
            session.permanent = True
            session["student_id"] = row["student_id"]

            # 两种选一：
            # 1) 若已在 welcome.html 放了“请选择课程”按钮，就跳到 welcome：
            return redirect(url_for("welcome"))           
            #return render_template("welcome.html", identifier=row["student_id"] or row["email"])
            # 2) 或者直接去选课页：
            # return redirect(url_for("choose_courses"))
        else:
            return render_template("index.html", message="Wrong Password!")

    except UnicodeEncodeError:
        return render_template(
            "index.html",
            message="Fail to make connection to Database!"
        )
    except Exception as e:
        print("[LOGIN ERROR]", repr(e))
        return render_template("index.html", message="Fail to log in! Please check the log!")

if __name__ == "__main__":
    # 生产环境不要用 debug=True；本地开发可以开
    # port = int(os.getenv("BACKEND_PORT", "9900"))
    # app.run(host="0.0.0.0", port=port, debug=True)
    app.run(host="0.0.0.0", port=80)