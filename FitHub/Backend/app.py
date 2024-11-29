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
    

@app.route('/', methods=['GET', 'POST'])
def posts_screen():
    if 'Email' in session:
        Email = session['Email']
        conn = get_db_connection()

        # fetch user data
        user = conn.execute('SELECT * FROM User WHERE Email = ?', (Email,)).fetchone()

# share post 
        if request.method == 'POST' and 'post_content' in request.form:
            post_content = request.form['post_content']
            post_media = request.form['media'] if 'media' in request.form else None  
            conn.execute(
                'INSERT INTO Posts (User_ID, Content, Time_Stamp, Tags, Media) VALUES (?, ?, datetime("now"), ?, ?)',
                (user['User_ID'], post_content, user['Interests'], post_media)
            )
            conn.commit()
# posts
        user_interests = user['Interests'].split(',')
        # map interest with their IDs
        placeholders = ', '.join(['?'] * len(user_interests))
        interest_ids = conn.execute('SELECT Interest_ID FROM Interest WHERE Name IN (' + placeholders + ')',
        user_interests).fetchall()

        # make alist of interests
        interest_ids = [str(row['Interest_ID']) for row in interest_ids] 

        placeholders = ', '.join(['?'] * len(interest_ids))
        posts_by_interest = conn.execute(
            '''SELECT * FROM Posts WHERE EXISTS (
                SELECT 1 FROM Interest 
                WHERE Interest.Interest_ID IN (' + placeholders_for_interest_ids + ') 
                  AND Posts.tags LIKE '%' || Interest.Interest_ID || '%') ORDER BY created_at DESC''', 
                  interest_ids).fetchall()
        
        remaining_posts = conn.execute(
            '''SELECT * FROM Posts WHERE id NOT IN (
                SELECT id FROM Posts 
                WHERE EXISTS (
                    SELECT 1 FROM Interest 
                    WHERE Interest.Interest_ID IN (' + placeholders_for_interest_ids + ') 
                      AND Posts.tags LIKE '%' || Interest.Interest_ID || '%')) ORDER BY created_at DESC''',
                    interest_ids).fetchall()
            
        all_posts = posts_by_interest + remaining_posts


        conn.close()

        return render_template("posts_screen.html", user=user, posts=all_posts)
    return redirect(url_for('login')) 

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
