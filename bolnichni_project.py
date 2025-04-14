from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()
app = Flask(__name__)
app.secret_key = 'secret_key'
app.permanent_session_lifetime = timedelta(minutes=10)

app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT"))
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/home')
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['email']
            session['name'] = user['name']
            session['personal_number'] = user['personal_number']
            return redirect('/home')
        flash("Грешен имейл или парола")
    return render_template("login.html")

@app.route('/home', methods=['GET'])
def home():
    if 'user_id' not in session: return redirect('/')
    return render_template("index.html", name=session['name'])

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session: return redirect('/')
    if request.method == 'POST':
        new = request.form['new_password']
        confirm = request.form['confirm_password']
        if new != confirm:
            flash("Паролите не съвпадат.")
            return redirect('/change_password')
        db = get_db()
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                   (generate_password_hash(new), session['user_id']))
        db.commit()
        flash("Паролата е променена.")
        return redirect('/home')
    return render_template("change_password.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Излязохте от системата.")
    return redirect('/')

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or session.get('username') != 'admin':
        flash("Нямате достъп до тази страница.")
        return redirect('/')
    return render_template("admin.html")

@app.route('/submit_sick_leave', methods=['POST'])
def submit_sick_leave():
    if 'user_id' not in session: return redirect('/')
    
    from_date = request.form['from_date']
    to_date = request.form['to_date']
    days = request.form['days']
    note = request.form['note']
    file = request.files['file']

    csv_path = f"sick_leave_{session['personal_number']}.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Име,Персонален номер,От дата,До дата,Дни,Забележка\n")
        f.write(f"{session['name']},{session['personal_number']},{from_date},{to_date},{days},{note}\n")

    msg = Message("Болничен от " + session['name'],
                  sender=os.getenv("MAIL_USERNAME"),
                  recipients=["svetoslav.ivanov@katek-group.com"])
    msg.body = f"Болничен за {days} дни от {from_date} до {to_date}.\nЗабележка: {note}"
    msg.attach(file.filename, file.content_type, file.read())
    with open(csv_path, "rb") as f:
        msg.attach(csv_path, "text/csv", f.read())
    
    mail.send(msg)
    flash("Болничният беше изпратен успешно.")
    return redirect('/home')
