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
    if 'User_ID' in session:
        User_ID = session['User_ID']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE User_ID = ?', (User_ID,)).fetchone()
        conn.close()
        return render_template("homepage.html", user=user)
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
            session['User_ID'] = user[0]
            return redirect(url_for('redirectPerRole'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template("login.html")


@app.route('/redirect', methods=['GET', 'POST'])
def redirectPerRole():
    User_ID = str(session['User_ID'])
    conn = get_db_connection()
    role = conn.execute('SELECT Role FROM User WHERE User_ID = ?', (User_ID,)).fetchone()
    conn.close()
    role = role[0]
    if role == "Admin":
        return redirect(url_for('unverifiedCoaches'))
    elif role == "Coach":
        conn = get_db_connection()
        verification = conn.execute('SELECT Verified FROM Coach WHERE Coach_ID = ?', (User_ID,)).fetchone()
        verification = verification[0]
        conn.close()
        if verification == "TRUE":
            return redirect(url_for('home_page'))
        return "Please wait to be verified :)"
    return redirect(url_for('home_page'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('Email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/trainee', methods=["GET", "POST"])
def traineeSignUp():
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
        interests_id = request.form.getlist('interests')

        conn = get_db_connection()
        interests = ""
        for intr in interests_id:
            inter = conn.execute('SELECT Name FROM Interest WHERE Interest_ID = ?', (intr,)).fetchone()
            interests += inter[0] + ","
        interests = interests[:-1]
        userid_count = conn.execute('SELECT COUNT(*) FROM User').fetchone()
        userid = str(userid_count[0] + 1)

        conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, Role, Interests) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (userid, username, email, age, gender, password, role, interests))

        conn.execute('INSERT INTO Trainee (Trainee_ID, Weight_kg, Height_m, BMI, Exercise_Level) '
                     'VALUES (?, ?, ?, ?, ?)',
                     (userid, weight, height, bmi, exercise))

        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    conn = get_db_connection()
    all_interests = conn.execute('SELECT * FROM Interest').fetchall()
    conn.close()
    return render_template("traineeSignUp.html", interests=all_interests)


@app.route('/coach', methods=["GET", "POST"])
def coachSignUp():
    if request.method == 'POST':
        role = "Coach"
        verified = "FALSE"
        username = request.form['username']
        email = request.form['email']
        age = request.form['age']
        expYears = str(request.form['expYears']) + " years"
        expDesc = request.form['expDesc']
        gender = request.form['gender']
        certificates = request.form['certificates']
        password = request.form['password']
        interests_id = request.form.getlist('interests')

        conn = get_db_connection()
        interests = ""
        for intr in interests_id:
            inter = conn.execute('SELECT Name FROM Interest WHERE Interest_ID = ?', (intr,)).fetchone()
            interests += inter[0] + ","
        interests = interests[:-1]
        userid_count = conn.execute('SELECT COUNT(*) FROM User').fetchone()
        userid = str(userid_count[0] + 1)

        conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, Role, Interests) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (userid, username, email, age, gender, password, role, interests))

        conn.execute('INSERT INTO Coach (Coach_ID, Verified, Description, Experience, Certificates) '
                     'VALUES (?, ?, ?, ?, ?)',
                     (userid, verified, expDesc, expYears, certificates))

        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    conn = get_db_connection()
    all_interests = conn.execute('SELECT * FROM Interest').fetchall()
    conn.close()
    return render_template("coachSignUp.html", interests=all_interests)


@app.route('/admin', methods=["GET", "POST"])
def unverifiedCoaches():
    conn = get_db_connection()
    unverifiedCoaches = conn.execute('SELECT * FROM Coach JOIN User ON User_ID=Coach_ID '
                                     'WHERE Verified = "FALSE"').fetchall()
    conn.close()
    return render_template("verifyCoaches.html", coaches=unverifiedCoaches)


@app.route('/verify_coach', methods=["GET", "POST"])
def verifyCoach():
    print("getting verified")
    coachID = request.form['verify_coach']
    print(coachID)
    conn = get_db_connection()
    conn.execute('UPDATE Coach SET Verified = "TRUE" WHERE Coach_ID=?', (coachID,))
    conn.commit()
    conn.close()
    return redirect(url_for('unverifiedCoaches'))


@app.route('/deny_coach', methods=["GET", "POST"])
def denyCoach():
    print("getting kicked out")
    coachID = request.form['deny_coach']
    print(coachID)
    conn = get_db_connection()
    conn.execute('DELETE FROM Coach WHERE Coach_ID=?', (coachID,))
    conn.execute('DELETE FROM User WHERE User_ID=?', (coachID,))
    conn.commit()
    conn.close()
    return redirect(url_for('unverifiedCoaches'))


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
