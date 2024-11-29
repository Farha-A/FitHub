from flask import Flask, render_template, request, session, flash, redirect, url_for
import sqlite3

DATABASE = 'FitHub_DB.sqlite'

app = Flask(__name__)
app.secret_key = 'keyyy'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/', methods=['GET', 'POST'])
def home_page():
    if 'Email' in session:
        Email = session['Email']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE email = ?', (Email,)).fetchone()
        conn.close()
        return render_template("home_page.html", user=user)
    return redirect(url_for('login'))


@app.route('/signUp', methods=['GET', 'POST'])
def role_choice():
    return render_template("role.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Email = request.form['Email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE Email = ? AND password = ?',
                            (Email, password)).fetchone()
        conn.close()
        if user:
            session['Email'] = Email
            return redirect(url_for('home_page'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template("login.html")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('Email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/trainee', methods=["GET", "POST"])
def traineeSignUp():
    # EL INTERESTS YA BET
    if request.method == 'POST':
        role = "Trainee"
        username = request.form['username']
        email = request.form['email']
        age = request.form['age']
        weight = request.form['weight']
        height = request.form['height']
        gender = request.form['gender']
        exercise = request.form['exercise']
        password = request.form['password']
        bmi = round(int(weight) / (float(height) ** 2), 2)

        conn = get_db_connection()
        userid_count = conn.execute('SELECT COUNT(*) FROM User').fetchone()
        userid = userid_count[0] + 1

        conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, Role) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (userid, username, email, age, gender, password, role))

        conn.execute('INSERT INTO Trainee (Trainee_ID, Weight_kg, Height_m, BMI, Exercise_Level) '
                     'VALUES (?, ?, ?, ?, ?)',
                     (userid, weight, height, bmi, exercise))

        conn.commit()
        conn.close()
        return redirect(url_for('role_choice'))
    return render_template("traineeSignUp.html")


@app.route('/coach', methods=["GET", "POST"])
def coachSignUp():
    # EL INTERESTS YA BET
    if request.method == 'POST':
        role = "Coach"
        verified = "FALSE"
        username = request.form['username']
        email = request.form['email']
        age = request.form['age']
        expYears = request.form['expYears']
        expDesc = request.form['expDesc']
        gender = request.form['gender']
        certificates = request.form['certificates']
        password = request.form['password']

        conn = get_db_connection()
        userid_count = conn.execute('SELECT COUNT(*) FROM User').fetchone()
        userid = userid_count[0] + 1

        conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, Role) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (userid, username, email, age, gender, password, role))

        conn.execute('INSERT INTO Coach (Coach_ID, Verified, Description, Experience, Certificates) '
                     'VALUES (?, ?, ?, ?, ?)',
                     (userid, verified, expDesc, expYears, certificates))

        conn.commit()
        conn.close()
        return redirect(url_for('role_choice'))
    return render_template("coachSignUp.html")


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
