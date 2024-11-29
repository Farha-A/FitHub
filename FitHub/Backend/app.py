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
    

@app.route('/posts', methods=['GET', 'POST'])
def posts_screen():
    if 'User_ID' in session:
        User_ID = session['User_ID']
        conn = get_db_connection()

        # user info
        user = conn.execute('SELECT * FROM User WHERE User_ID = ?', (User_ID,)).fetchone()

        #  available tags/Interests
        all_interests = conn.execute('SELECT * FROM Interest').fetchall()

        # Share post
        if request.method == 'POST':
            post_content = request.form['content']
            post_media = request.form.get('media')  # need modifing
            selected_tags = request.form.getlist('tags')  # Get selected tags"as list"

            # Post_ID
            postid_count = conn.execute('SELECT COUNT(*) FROM Post').fetchone()
            postid = postid_count[0] + 1

            # save the post to database
            tags_str = ','.join(selected_tags)  # save tags  "seperated by commas"
            conn.execute(
                '''INSERT INTO Post (Post_ID, User_ID, Content, Time_Stamp, Media, Tags) 
                   VALUES (?, ?, ?, datetime("now"), ?, ?)''',
                (postid, user['User_ID'], post_content, post_media, tags_str)
            )
            conn.commit()

        # user interests and corresponding posts
        user_interests = user['Interests'].split(',')
        placeholders = ', '.join(['?'] * len(user_interests))
        interest_ids = conn.execute(
            'SELECT Interest_ID FROM Interest WHERE Name IN (' + placeholders + ')',
            tuple(user_interests)
        ).fetchall()

        # list of Interest_IDs
        interest_ids = [str(row['Interest_ID']) for row in interest_ids]
        placeholders_for_interest_ids = ', '.join(['?'] * len(interest_ids))

        posts_by_interest = conn.execute(
            f'''SELECT * FROM Post WHERE EXISTS (
                SELECT 1 FROM Interest 
                WHERE Interest.Interest_ID IN ({placeholders_for_interest_ids}) 
                  AND Post.Tags LIKE '%' || Interest.Interest_ID || '%') 
                ORDER BY Time_Stamp DESC''',
            tuple(interest_ids)
        ).fetchall()

        remaining_posts = conn.execute(
            f'''SELECT * FROM Post WHERE Post_ID NOT IN (
                SELECT Post_ID FROM Post 
                WHERE EXISTS (
                    SELECT 1 FROM Interest 
                    WHERE Interest.Interest_ID IN ({placeholders_for_interest_ids}) 
                      AND Post.Tags LIKE '%' || Interest.Interest_ID || '%')) 
                ORDER BY Time_Stamp DESC''',
            tuple(interest_ids)
        ).fetchall()

        all_posts = posts_by_interest + remaining_posts

        # comments of the current post
        posts_with_comments = []
        for post in all_posts:
            comments = conn.execute(
                'SELECT * FROM Comment WHERE Post_ID = ? ORDER BY Time_Stamp DESC',
                (post['Post_ID'],)
            ).fetchall()
            posts_with_comments.append({
                'post': post,
                'comments': comments
            })

        conn.close()

        return render_template("posts_screen.html", user=user, posts_with_comments=posts_with_comments, interests=all_interests)

    return redirect(url_for('login'))


@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'User_ID' in session:
        User_ID = session['User_ID']
        conn = get_db_connection()

        commentid_count = conn.execute('SELECT COUNT(*) FROM Comment').fetchone()
        commentid = commentid_count[0] + 1

        # Comment_ID
        comment_content = request.form['comment_content']
        conn.execute(
            'INSERT INTO Comment (Comment_ID, Post_ID, User_ID, Content, Time_Stamp) VALUES (?, ?, ?, ?, datetime("now"))',
            (commentid, post_id, User_ID, comment_content)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('posts_screen'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
