from flask import Flask, request, render_template, session,redirect,url_for
import pymysql
import bcrypt
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "dev-secret"   
app.permanent_session_lifetime = timedelta(days=7)
# === 修改成你的数据库信息（注意：密码务必只用 ASCII 字符，避免中文/表情）===
DB_HOST = "localhost"
DB_USER = "root"            # 或你新建的 demo 用户
DB_PASS = "928109"       # 👈 例子：只含英文字母/数字/符号
DB_NAME = "ai_learning_coach"

def get_conn():
    """
    建立到 MySQL 的连接：
    - autocommit=True 省去手动 commit
    - charset='utf8mb4' 确保中文学号/邮箱可写
    """
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def index():
    # 确保有 templates/index.html
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    student_id = (request.form.get("student_id") or "").strip()
    email      = (request.form.get("email") or "").strip()
    password   = (request.form.get("password") or "")

    if not student_id or not email or not password:
        return render_template("index.html", message="请填写学号、邮箱和密码。")

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

    # --- POST: 单课程增量添加（必须存在于 courses 表中） ---
    code = (request.form.get("course_code") or "").strip().upper()
    if not code:
        return render_template("choose_courses.html", message="请输入课程代码。")

    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # ① 检查 courses 表中是否存在该课程
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

            # ③ 插入新选课记录
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
            message="保存失败：服务器内部错误。"
        )

@app.route("/materials/<course_code>")
def materials_of_course(course_code):

    if "student_id" not in session:
        return redirect(url_for("index"))
    code = (course_code or "").upper()
    # 这里现在不查资料，先显示空页面
    return render_template("materials.html", code=code)

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
            # ✅ 关键：写入 session，后续受保护页面才能识别已登录
            session.permanent = True
            session["student_id"] = row["student_id"]

            # 两种选一：
            # 1) 若你已在 welcome.html 放了“请选择课程”按钮，就跳到 welcome：
            return render_template("welcome.html", identifier=row["student_id"] or row["email"])
            # 2) 或者直接去选课页（更顺畅）：
            # return redirect(url_for("choose_courses"))
        else:
            return render_template("index.html", message="密码错误。")

    except UnicodeEncodeError:
        return render_template(
            "index.html",
            message="数据库连接失败：请将 MySQL 登录密码改为仅包含 ASCII 的字符（英⽂/数字/常见符号）。"
        )
    except Exception as e:
        print("[LOGIN ERROR]", repr(e))
        return render_template("index.html", message="登录失败：服务器内部错误，请检查后端日志。")

if __name__ == "__main__":
    # 生产环境不要用 debug=True；本地开发可以开
    app.run(host="127.0.0.1", port=5000, debug=True)
