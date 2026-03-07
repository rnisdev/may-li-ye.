from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ======================
# UPLOAD FOLDER
# ======================

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ======================
# EMAIL CONFIG
# ======================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "rnissage9@gmail.com"
app.config['MAIL_PASSWORD'] = "hjvlehxmdnlrvyqx"

mail = Mail(app)


# ======================
# DATABASE INIT
# ======================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        service TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ======================
# HOME
# ======================

@app.route("/")
def home():
    return render_template("index.html")


# ======================
# SUBMIT CLIENT FORM
# ======================

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    service = request.form["service"]

    # send email
    msg = Message(
        "Nouvo kliyan",
        sender=app.config['MAIL_USERNAME'],
        recipients=[app.config['MAIL_USERNAME']]
    )

    msg.body = f"""
Nouvo kliyan sou sit la

Name: {name}
Email: {email}
Phone: {phone}
Service: {service}
"""

    mail.send(msg)

    # save to db
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO clients (name,email,phone,service) VALUES (?,?,?,?)",
        (name, email, phone, service)
    )

    conn.commit()
    conn.close()

    return "Mesaj ou anrejistre avèk siksè!"


# ======================
# ADMIN PANEL
# ======================

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    data = cursor.fetchall()
    conn.close()

    return render_template("admin.html", clients=data)


# ======================
# DELETE CLIENT
# ======================

@app.route("/delete/<int:id>")
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ======================
# EDIT CLIENT
# ======================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        service = request.form["service"]

        cursor.execute("""
        UPDATE clients
        SET name=?, email=?, phone=?, service=?
        WHERE id=?
        """, (name, email, phone, service, id))

        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    cursor.execute("SELECT * FROM clients WHERE id=?", (id,))
    client = cursor.fetchone()
    conn.close()

    return f"""
    <form method="POST">
        <input name="name" value="{client[1]}"><br>
        <input name="email" value="{client[2]}"><br>
        <input name="phone" value="{client[3]}"><br>
        <input name="service" value="{client[4]}"><br>
        <button>Update</button>
    </form>
    """


# ======================
# SIGNUP
# ======================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username,password)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("login"))

    return render_template("signup.html")


# ======================
# LOGIN
# ======================

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["admin"] = True
            return redirect(url_for("admin"))

    return render_template("login.html")


# ======================
# DOCUMENT UPLOAD
# ======================

@app.route("/upload-docs", methods=["POST"])
def upload_docs():
    name = request.form["name"]
    email = request.form["email"]

    passport = request.files["passport"]
    idcard = request.files["idcard"]
    photo = request.files["photo"]

    passport_name = secure_filename(passport.filename)
    id_name = secure_filename(idcard.filename)
    photo_name = secure_filename(photo.filename)

    passport_path = os.path.join(app.config["UPLOAD_FOLDER"], passport_name)
    id_path = os.path.join(app.config["UPLOAD_FOLDER"], id_name)
    photo_path = os.path.join(app.config["UPLOAD_FOLDER"], photo_name)

    passport.save(passport_path)
    idcard.save(id_path)
    photo.save(photo_path)

    msg = Message(
        "New Client Documents",
        sender=app.config['MAIL_USERNAME'],
        recipients=[app.config['MAIL_USERNAME']]
    )

    msg.body = f"""
New client uploaded documents

Name: {name}
Email: {email}
"""

    msg.attach(passport_name, "application/pdf", open(passport_path,"rb").read())
    msg.attach(id_name, "application/pdf", open(id_path,"rb").read())
    msg.attach(photo_name, "image/jpeg", open(photo_path,"rb").read())

    mail.send(msg)

    return "Documents sent successfully!"


# ======================
# RUN APP
# ======================

if __name__ == "__main__":
    app.run(debug=True)