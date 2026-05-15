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
# pip install flask flask_sqlalchemy flask_login
# pip install psycopg2-binary pymysql
# pip install pandas openpyxl
#
# RUN:
# python main.py
#
# LOGIN:
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
from sqlalchemy import inspect
from flask import jsonify
import os
import pandas as pd
from io import BytesIO
from flask import send_file
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
    'postgresql://postgres:password_postgres@localhost/sqlmanager'
)
# MySQL
# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     'mysql+pymysql://root:password_postgres@localhost/sqlmanager'
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
    return db.session.get(User, int(user_id))
# =========================================================
# INITIALIZE DATABASE
# =========================================================
with app.app_context():
    db.create_all()
    existing_user = User.query.filter_by(
        username="admin"
    ).first()
    if not existing_user:
        admin = User(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin already exists!")
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
    <a href="/tables">
        <button type="button">
            Open Table Browser
        </button>
    </a>
    <br>
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
TABLE_BROWSER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Table Browser</title>
    <style>
        body{
            margin:0;
            font-family:Arial;
            background:#f4f4f4;
        }
        .layout{
            display:flex;
            height:100vh;
        }
        .sidebar{
            width:250px;
            background:#1f2937;
            color:white;
            overflow:auto;
        }
        .sidebar h2{
            padding:20px;
            margin:0;
            background:#111827;
        }
        .table-link{
            display:block;
            color:white;
            padding:12px 20px;
            text-decoration:none;
            border-bottom:1px solid rgba(255,255,255,0.05);
        }
        .table-link:hover{
            background:#374151;
        }
        .content{
            flex:1;
            padding:20px;
            overflow:auto;
        }
        table{
            width:100%;
            border-collapse:collapse;
            background:white;
        }
        th, td{
            border:1px solid #ddd;
            padding:10px;
            text-align:left;
        }
        th{
            background:#2563eb;
            color:white;
        }
        tr:nth-child(even){
            background:#f9f9f9;
        }
        input{
            width:100%;
            padding:8px;
            box-sizing:border-box;
        }
        button{
            padding:8px 14px;
            border:none;
            cursor:pointer;
            border-radius:4px;
        }
        .btn-save{
            background:#10b981;
            color:white;
        }
        .btn-delete{
            background:#ef4444;
            color:white;
        }
        .btn-add{
            background:#2563eb;
            color:white;
            margin-bottom:20px;
        }
        .topbar{
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:20px;
        }
        .logout{
            background:red;
            color:white;
            padding:10px;
            text-decoration:none;
        }
        .message{
            background:#d1fae5;
            color:#065f46;
            padding:10px;
            margin-bottom:20px;
        }
    </style>
</head>
<body>
<div class="layout">
    <div class="sidebar">
        <h2>Tables</h2>
        {% for table in tables %}
            <a class="table-link"
               href="/table/{{ table }}">
               {{ table }}
            </a>
        {% endfor %}
    </div>
    <div class="content">
        <div class="topbar">
            <div>
                <h1>{{ selected_table }}</h1>
                <div style="margin-bottom:20px;">
                    <a href="/table/{{ selected_table }}/export/csv">
                        <button type="button">
                            Export CSV
                        </button>
                    </a>
                    <a href="/table/{{ selected_table }}/export/excel">
                        <button type="button">
                            Export Excel
                        </button>
                    </a>
                    <form
                        action="/table/{{ selected_table }}/import/csv"
                        method="POST"
                        enctype="multipart/form-data"
                        style="display:inline;"
                    >
                        <input type="file"
                        name="file"
                        accept=".csv"
                        required>
                        <button type="submit">
                            Import CSV
                        </button>
                    </form>
                    <form
                        action="/table/{{ selected_table }}/import/excel"
                        method="POST"
                        enctype="multipart/form-data"
                        style="display:inline;"
                    >
                        <input type="file"
                        name="file"
                        accept=".xlsx"
                        required>
                        <button type="submit">
                            Import Excel
                        </button>
                    </form>
                </div>
            </div>
            <div>
                Logged in as:
                <strong>{{ user.username }}</strong>
                <a href="/dashboard">
                    <button type="button">
                            Dashboard
                    </button>
                </a>
                <br>
                <a href="/logout"
                   class="logout">
                   Logout
                </a>
            </div>
        </div>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                    <div class="message">
                        {{ msg }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% if selected_table %}
        <form method="POST"
              action="/table/{{ selected_table }}/add">
            <table>
                <tr>
                    {% for col in columns %}
                        <th>{{ col }}</th>
                    {% endfor %}
                    <th>Action</th>
                </tr>
                <tr>
                    {% for col in columns %}
                        <td>
                            <input type="text"
                                   name="{{ col }}">
                        </td>
                    {% endfor %}
                    <td>
                        <button class="btn-add"
                                type="submit">
                            Add Row
                        </button>
                    </td>
                </tr>
            </table>
        </form>
        <br>
        <table>
            <tr>
                {% for col in columns %}
                    <th>{{ col }}</th>
                {% endfor %}
                <th>Actions</th>
            </tr>
            {% for row in rows %}
            <form method="POST"
                  action="/table/{{ selected_table }}/update/{{ row[primary_key] }}">
            <tr>
                {% for col in columns %}
                    <td>
                        <input type="text"
                               name="{{ col }}"
                               value="{{ row[col] }}">
                    </td>
                {% endfor %}
                <td>
                    <button class="btn-save"
                            type="submit">
                        Save
                    </button>
                    <a href="/table/{{ selected_table }}/delete/{{ row[primary_key] }}"
                       onclick="return confirm('Delete row?')">
                        <button type="button"
                                class="btn-delete">
                            Delete
                        </button>
                    </a>
                </td>
            </tr>
            </form>
            {% endfor %}
        </table>
        {% endif %}
    </div>
</div>
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
# TABLE BROWSER HOME
# =========================================================
@app.route("/tables")
@login_required
def tables():
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    return render_template_string(
        TABLE_BROWSER_TEMPLATE,
        tables=table_names,
        selected_table=None,
        rows=[],
        columns=[],
        user=current_user,
        primary_key="id"
    )
# =========================================================
# VIEW TABLE
# =========================================================
@app.route("/table/<table_name>")
@login_required
def view_table(table_name):
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    if table_name not in table_names:
        flash("Table not found")
        return redirect("/tables")
    result = db.session.execute(
        text(f"SELECT * FROM {table_name} LIMIT 100")
    )
    rows = [dict(row._mapping) for row in result]
    columns = result.keys()
    primary_key = inspector.get_pk_constraint(
        table_name
    )["constrained_columns"][0]
    return render_template_string(
        TABLE_BROWSER_TEMPLATE,
        tables=table_names,
        selected_table=table_name,
        rows=rows,
        columns=columns,
        user=current_user,
        primary_key=primary_key
    )
# =========================================================
# ADD ROW
# =========================================================
@app.route("/table/<table_name>/add", methods=["POST"])
@login_required
def add_row(table_name):
    inspector = inspect(db.engine)
    columns_info = inspector.get_columns(table_name)
    data = {}
    for col in columns_info:
        name = col["name"]
        value = request.form.get(name)
        if value != "":
            data[name] = value
    if data:
        cols = ", ".join(data.keys())
        vals = ", ".join([f":{k}" for k in data.keys()])
        query = text(
            f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"
        )
        db.session.execute(query, data)
        db.session.commit()
        flash("Row added successfully")
    return redirect(f"/table/{table_name}")
# =========================================================
# UPDATE ROW
# =========================================================
@app.route(
    "/table/<table_name>/update/<row_id>",
    methods=["POST"]
)
@login_required
def update_row(table_name, row_id):
    inspector = inspect(db.engine)
    columns_info = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(
        table_name
    )["constrained_columns"][0]
    data = {}
    sets = []
    for col in columns_info:
        name = col["name"]
        value = request.form.get(name)
        data[name] = value
        if name != pk:
            sets.append(f"{name}=:{name}")
    data["pk"] = row_id
    query = text(
        f"""
        UPDATE {table_name}
        SET {", ".join(sets)}
        WHERE {pk}=:pk
        """
    )
    db.session.execute(query, data)
    db.session.commit()
    flash("Row updated")
    return redirect(f"/table/{table_name}")
# =========================================================
# DELETE ROW
# =========================================================
@app.route(
    "/table/<table_name>/delete/<row_id>"
)
@login_required
def delete_row(table_name, row_id):
    inspector = inspect(db.engine)
    pk = inspector.get_pk_constraint(
        table_name
    )["constrained_columns"][0]
    query = text(
        f"DELETE FROM {table_name} WHERE {pk}=:pk"
    )
    db.session.execute(query, {"pk": row_id})
    db.session.commit()
    flash("Row deleted")
    return redirect(f"/table/{table_name}")
# =========================================================
# EXPORT CSV
# =========================================================
@app.route("/table/<table_name>/export/csv")
@login_required
def export_csv(table_name):
    df = pd.read_sql(
        f"SELECT * FROM {table_name}",
        db.engine
    )
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{table_name}.csv"
    )
# =========================================================
# EXPORT EXCEL
# =========================================================
@app.route("/table/<table_name>/export/excel")
@login_required
def export_excel(table_name):
    df = pd.read_sql(
        f"SELECT * FROM {table_name}",
        db.engine
    )
    output = BytesIO()
    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name=table_name
        )
    output.seek(0)
    return send_file(
        output,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        as_attachment=True,
        download_name=f"{table_name}.xlsx"
    )
# =========================================================
# IMPORT CSV
# =========================================================
@app.route(
    "/table/<table_name>/import/csv",
    methods=["POST"]
)
@login_required
def import_csv(table_name):
    file = request.files["file"]
    if not file:
        flash("No file selected")
        return redirect(f"/table/{table_name}")
    try:
        df = pd.read_csv(file)
        df.to_sql(
            table_name,
            con=db.engine,
            if_exists="append",
            index=False
        )
        flash("CSV imported successfully")
    except Exception as e:
        flash(str(e))
    return redirect(f"/table/{table_name}")
# =========================================================
# IMPORT EXCEL
# =========================================================
@app.route(
    "/table/<table_name>/import/excel",
    methods=["POST"]
)
@login_required
def import_excel(table_name):
    file = request.files["file"]
    if not file:
        flash("No file selected")
        return redirect(f"/table/{table_name}")
    try:
        df = pd.read_excel(file)
        df.to_sql(
            table_name,
            con=db.engine,
            if_exists="append",
            index=False
        )
        flash("Excel imported successfully")
    except Exception as e:
        flash(str(e))
    return redirect(f"/table/{table_name}")
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
    if __name__ == "__main__":
        app.run(
            debug=True,
            host="127.0.0.1",
            port=9000
        )