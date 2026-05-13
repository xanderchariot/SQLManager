# Advanced SQL Database Manager
# Features:
# - User Authentication/Login
# - PostgreSQL Support
# - MySQL Support
# - SQLite Support
# - SQLAlchemy ORM
# - Admin Dashboard
# - CRUD Operations
# - Execute Custom SQL
#
# INSTALL:
#
# pip install flask flask_sqlalchemy flask_login
# pip install psycopg2-binary pymysql
#
# RUN:
#
# python main.py
#
# DEFAULT LOGIN:
# username: admin
# password: admin123
from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from sqlalchemy import text
import os
# =========================================================
# CONFIG
# =========================================================
app = Flask(__name__)
app.secret_key = "super-secret-key"
# =========================================================
# DATABASE CONFIGURATION
# =========================================================
# Choose ONE:
# SQLite
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://postgres:password@localhost/sqlmanager'
)
# MySQL
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     'mysql+pymysql://root:password@localhost/sqlmanager'
# )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# =========================================================
# LOGIN MANAGER
# =========================================================
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)
# =========================================================
# USER MODEL
# =========================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(255),
        nullable=False
    )
# =========================================================
# LOGIN LOADER
# =========================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# =========================================================
# INITIALIZE DATABASE
# =========================================================
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        hashed_password = generate_password_hash("admin123")
        admin = User(
            username="admin",
            password=hashed_password
        )
        db.session.add(admin)
        db.session.commit()
# =========================================================
# HTML TEMPLATES
# =========================================================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body{
            font-family: Arial;
            background:#f5f5f5;
        }
        .container{
            width:400px;
            margin:100px auto;
            background:white;
            padding:30px;
            border-radius:10px;
            box-shadow:0 0 10px rgba(0,0,0,0.1);
        }
        input{
            width:100%;
            padding:10px;
            margin-top:10px;
        }
        button{
            margin-top:20px;
            width:100%;
            padding:12px;
            background:#007bff;
            color:white;
            border:none;
        }
        .flash{
            color:red;
        }
    </style>
</head>
<body>
<div class="container">
<h2>Login</h2>
{% with messages = get_flashed_messages() %}
    {% if messages %}
        {% for msg in messages %}
            <p class="flash">{{ msg }}</p>
        {% endfor %}
    {% endif %}
{% endwith %}
<form method="POST">
<input type="text"
       name="username"
       placeholder="Username"
       required>
<input type="password"
       name="password"
       placeholder="Password"
       required>
<button type="submit">
    Login
</button>
</form>
</div>
</body>
</html>
"""
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body{
            font-family:Arial;
            background:#f5f5f5;
            padding:20px;
        }
        textarea{
            width:100%;
            height:200px;
            margin-top:10px;
        }
        button{
            padding:10px 20px;
            margin-top:10px;
        }
        table{
            width:100%;
            border-collapse: collapse;
            margin-top:20px;
            background:white;
        }
        th, td{
            border:1px solid #ddd;
            padding:10px;
        }
        th{
            background:#007bff;
            color:white;
        }
        .topbar{
            display:flex;
            justify-content:space-between;
            align-items:center;
        }
        .logout{
            background:red;
            color:white;
            padding:10px;
            text-decoration:none;
        }
    </style>
</head>
<body>
<div class="topbar">
    <h1>SQL Manager Dashboard</h1>
    <div>
        Logged in as:
        <strong>{{ user.username }}</strong>
        <a href="/logout" class="logout">
            Logout
        </a>
    </div>
</div>
<h2>Execute SQL Query</h2>
<form method="POST" action="/execute">
<textarea name="query"
placeholder="Write SQL query here..."
required></textarea>
<br>
<button type="submit">
    Execute Query
</button>
</form>
{% if columns %}
    <table>
    <tr>
        {% for col in columns %}
            <th>{{ col }}</th>
        {% endfor %}
    </tr>
    {% for row in rows %}
        <tr>
        {% for value in row %}
            <td>{{ value }}</td>
        {% endfor %}
        </tr>
    {% endfor %}
    </table>
{% endif %}
</body>
</html>
"""
# =========================================================
# LOGIN ROUTE
# =========================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(
            username=username
        ).first()
        if user and check_password_hash(
            user.password,
            password
        ):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password")
    return render_template_string(LOGIN_TEMPLATE)
# =========================================================
# DASHBOARD
# =========================================================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=current_user,
        rows=None,
        columns=None
    )
# =========================================================
# EXECUTE SQL
# =========================================================
@app.route("/execute", methods=["POST"])
@login_required
def execute():
    query = request.form["query"]
    try:
        result = db.session.execute(text(query))
        db.session.commit()
        rows = []
        columns = []
        if result.returns_rows:
            rows = result.fetchall()
            columns = result.keys()
        return render_template_string(
            DASHBOARD_TEMPLATE,
            user=current_user,
            rows=rows,
            columns=columns
        )
    except Exception as e:
        flash(str(e))
        return redirect(url_for("dashboard"))
# =========================================================
# LOGOUT
# =========================================================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
# =========================================================
# START SERVER
# =========================================================
if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )