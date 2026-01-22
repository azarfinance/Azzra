from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "azar_secret_2026")

DB = "azar.db"

# ------------------ DATABASE ------------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        status TEXT,
        created_at TEXT
    )
    """)
    db.commit()

init_db()

# ------------------ TEMPLATES ------------------
LOGIN_HTML = """
<h2>Azar Finance Login</h2>
<form method="post">
Phone:<br><input name="phone"><br>
Password:<br><input type="password" name="password"><br><br>
<button>Login</button>
</form>
<a href="/signup">Create account</a>
"""

SIGNUP_HTML = """
<h2>Azar Finance Signup</h2>
<form method="post">
Name:<br><input name="name"><br>
Phone:<br><input name="phone"><br>
Password:<br><input type="password" name="password"><br>
Role:
<select name="role">
<option value="client">Client</option>
<option value="collector">Collector</option>
<option value="admin">Admin</option>
</select><br><br>
<button>Signup</button>
</form>
"""

DASHBOARD_HTML = """
<h2>{{role|upper}} DASHBOARD</h2>
<p>Welcome {{name}}</p>

{% if role == 'client' %}
<form method="post" action="/apply">
Loan Amount: <input name="amount"><br>
<button>Apply Loan</button>
</form>
{% endif %}

<h3>Loans</h3>
<ul>
{% for loan in loans %}
<li>{{loan['amount']}} - {{loan['status']}}</li>
{% endfor %}
</ul>

<a href="/logout">Logout</a>
"""

# ------------------ ROUTES ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        return "Invalid login"
    return render_template_string(LOGIN_HTML)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, phone, password, role) VALUES (?,?,?,?)",
                (
                    request.form["name"],
                    request.form["phone"],
                    generate_password_hash(request.form["password"]),
                    request.form["role"]
                )
            )
            db.commit()
            return redirect("/")
        except:
            return "User already exists"
    return render_template_string(SIGNUP_HTML)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    loans = db.execute("SELECT * FROM loans").fetchall() if user["role"] != "client" else \
            db.execute("SELECT * FROM loans WHERE user_id=?", (user["id"],)).fetchall()
    return render_template_string(
        DASHBOARD_HTML,
        name=user["name"],
        role=user["role"],
        loans=loans
    )

@app.route("/apply", methods=["POST"])
def apply():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    db.execute(
        "INSERT INTO loans (user_id, amount, status, created_at) VALUES (?,?,?,?)",
        (
            session["user_id"],
            request.form["amount"],
            "pending",
            datetime.datetime.now().isoformat()
        )
    )
    db.commit()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ------------------ RENDER PORT FIX ------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
