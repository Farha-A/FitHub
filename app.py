# importing necessary libraries
from flask import Flask, render_template, request, session, flash, redirect, url_for
import sqlite3
import random
from datetime import datetime
from flask_mail import Mail, Message
import numpy as np

# database path
DATABASE = 'FitHub_DB.sqlite'

# app initialization
app = Flask(__name__)
app.secret_key = 'suchasecurekey'


# function to connect to database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# load homepage
@app.route('/', methods=['GET', 'POST'])
def home_page():
    # check if a user is logged in
    if 'User_ID' in session:
        User_ID = session['User_ID']
        # returns logged-in user from the database
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE User_ID = ?', (User_ID,)).fetchone()
        conn.close()
        # send the user to the homepage
        return redirect("posts")
    # if there's no user logged in, redirects them to the login page
    return redirect(url_for('login'))


# sign up page where the new user decides if they're a coach or a trainee to
# get redirected to the appropriate sign-up page
@app.route('/signUp', methods=['GET', 'POST'])
def role_choice():
    return render_template("role.html")


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # save email & password entered
        Email = request.form['Email']
        password = request.form['password']

        # save user if a user with teh entered email and password exists
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM User WHERE Email = ? AND password = ?',
                            (Email, password)).fetchone()
        conn.close()
        # if a user is found save the id in the session to be used across pages
        if user:
            session['User_ID'] = user[0]
            return redirect(url_for('redirectPerRole'))
        # if user isn't found a message is shown to inform that the credentials are invalid
        else:
            flash('Invalid email or password', 'danger')

    return render_template("login.html")


@app.route('/forgotPW', methods=['GET', 'POST'])
def forgotPW():
    if 'fp_email' not in session:
        session['fp_email'] = None
    if 'security_question' not in session:
        session["security_question"] = None
    if "show_pw_change" not in session:
        session["show_pw_change"] = False
    show_sq = False

    if request.method == 'POST':
        if (session['fp_email'] and session['security_question'] and session["show_pw_change"] is True
                and 'new_pw' in request.form):
            new_pw = request.form['new_pw']
            conn = get_db_connection()
            userid = conn.execute('SELECT User_ID FROM User WHERE Email = ?', (session["fp_email"],)).fetchone()
            conn.execute('UPDATE User SET Password = ? WHERE User_ID = ?', (new_pw, userid[0]))
            conn.commit()
            conn.close()
            session.pop('fp_email', None)
            session.pop('security_question', None)
            session.pop('show_pw_change', None)
            return redirect(url_for("login"))

        elif session['fp_email']:
            if 'answer' in request.form:
                answer = request.form['answer'].lower()
                if session["security_question"] and answer == session["security_question"][1].lower():
                    session["show_pw_change"] = True
                else:
                    flash("Incorrect security answer. Try again.", "error")
        elif 'email' in request.form and request.form['email']:
            email = request.form['email']
            session['fp_email'] = email
            conn = get_db_connection()
            user_sq = conn.execute('SELECT Security_Question FROM User WHERE Email = ?', (email,)).fetchone()
            conn.close()

            if user_sq:
                session["security_question"] = user_sq[0].split(",")
                show_sq = True
            else:
                flash("Invalid email. Try again.", "error")
                session['fp_email'] = None
                session['security_question'] = None

    if session['fp_email'] and session["security_question"]:
        show_sq = True
    return render_template(
        "forgotPW.html", show_sq=show_sq,
        security_question=session["security_question"][0] if session["security_question"]
        else "", show_pw_change=session["show_pw_change"])


# user redirection per user role
@app.route('/redirect', methods=['GET', 'POST'])
def redirectPerRole():
    User_ID = str(session['User_ID'])
    conn = get_db_connection()
    # save logged in user's role
    role = conn.execute('SELECT Role FROM User WHERE User_ID = ?', (User_ID,)).fetchone()
    conn.close()
    role = role[0]
    # direct to admin's page
    if role == "Admin":
        return redirect(url_for('unverifiedCoaches'))
    elif role == "Coach":
        conn = get_db_connection()
        verification = conn.execute('SELECT Verified FROM Coach WHERE Coach_ID = ?', (User_ID,)).fetchone()
        verification = verification[0]
        conn.close()
        # if a coach is verified direct to homepage
        if verification == "TRUE":
            return redirect(url_for('posts'))
        session.pop('User_ID', None)
        return render_template("await_verification.html")
    return redirect(url_for('posts'))


# log out users
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # remove the saved userid
    session.pop('User_ID', None)
    # inform the user they logged out
    flash('You have been logged out.', 'info')
    # redirect to login page
    return redirect(url_for('login'))


# trainee sign-up
@app.route('/trainee', methods=["GET", "POST"])
def traineeSignUp():
    email_exists = False
    questions = ["What was your dream job as a child?", "What was the name of your first stuffed animal?",
                 "What was the color of your favorite childhood blanket?"]
    security_question = questions[np.random.randint(0, len(questions))]
    # save the trainee's information based on their input
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
        security_answer = request.form['sec_ans']

        conn = get_db_connection()
        # save interests entered by their names
        interests = ""
        for intr in interests_id:
            inter = conn.execute('SELECT Name FROM Interest WHERE Interest_ID = ?', (intr,)).fetchone()
            interests += inter[0] + ","
        interests = interests[:-1]
        # calculate new userid
        userid_count = conn.execute('SELECT COUNT(*) FROM User').fetchone()
        userid = str(userid_count[0] + 1)

        # check if email already used for another user
        email_check = conn.execute('SELECT * FROM User WHERE Email = ?', (email,)).fetchone()
        if not email_check:
            sec_qa = security_question + "," + security_answer
            # add trainee to user table
            conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, '
                         'Role, Interests, Security_Question) '
                         'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         (userid, username, email, age, gender, password, role, interests, sec_qa))

            # add trainee to trainee table
            conn.execute('INSERT INTO Trainee (Trainee_ID, Weight_kg, Height_m, BMI, Exercise_Level) '
                         'VALUES (?, ?, ?, ?, ?)',
                         (userid, weight, height, bmi, exercise))

            # calculate new planid
            planid_count = conn.execute('SELECT COUNT(*) FROM Plan').fetchone()
            planid = str(planid_count[0] + 1)

            # add basic plan based on gender
            if gender == "Female":
                init_plan = conn.execute('SELECT Plan FROM Plan WHERE Trainee_ID = ?', ("2",)).fetchone()
                conn.execute('INSERT INTO Plan (Plan_ID, Trainee_ID, Plan) VALUES (?, ?, ?)',
                             (planid, userid, init_plan[0]))
            else:
                init_plan = conn.execute('SELECT Plan FROM Plan WHERE Trainee_ID = ?', ("38",)).fetchone()
                print(init_plan)
                conn.execute('INSERT INTO Plan (Plan_ID, Trainee_ID, Plan) VALUES (?, ?, ?)',
                             (planid, userid, init_plan[0]))
            conn.commit()
            conn.close()
            # return user to login page
            return redirect(url_for('login'))
        email_exists = True
    # get all interests from database to show in form
    conn = get_db_connection()
    all_interests = conn.execute('SELECT * FROM Interest').fetchall()
    conn.close()
    return render_template("traineeSignUp.html", interests=all_interests, email_exists=email_exists,
                           security_question=security_question)


# coach sign-up
@app.route('/coach', methods=["GET", "POST"])
def coachSignUp():
    email_exists = False
    questions = ["What was your dream job as a child?", "What was the name of your first stuffed animal?",
                 "What was the color of your favorite childhood blanket?"]
    security_question = questions[np.random.randint(0, len(questions))]
    # save the coach's information based on their input
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
        security_answer = request.form['sec_ans']

        conn = get_db_connection()
        # save interests entered by their names
        interests = ""
        for intr in interests_id:
            inter = conn.execute('SELECT Name FROM Interest WHERE Interest_ID = ?', (intr,)).fetchone()
            interests += inter[0] + ","
        interests = interests[:-1]
        # calculate new userid
        userid_count = conn.execute('SELECT COUNT(*) FROM User').fetchone()
        userid = str(userid_count[0] + 1)

        # add coach to user table
        sec_qa = security_question + "," + security_answer
        # add trainee to user table
        conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, '
                     'Role, Interests, Security_Question) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (userid, username, email, age, gender, password, role, interests, sec_qa))

        # add coach to coach table
        conn.execute('INSERT INTO Coach (Coach_ID, Verified, Description, Experience, Certificates) '
                     'VALUES (?, ?, ?, ?, ?)',
                     (userid, verified, expDesc, expYears, certificates))

        conn.commit()
        conn.close()
        # return user to login page
        return redirect(url_for('login'))
    # get all interests from database to show in form
    conn = get_db_connection()
    all_interests = conn.execute('SELECT * FROM Interest').fetchall()
    conn.close()
    return render_template("traineeSignUp.html", interests=all_interests, email_exists=email_exists,
                           security_question=security_question)


# admin page
@app.route('/admin', methods=["GET", "POST"])
def unverifiedCoaches():
    conn = get_db_connection()
    # get all unverified coaches
    unverified_Coaches = conn.execute('SELECT * FROM Coach JOIN User ON User_ID=Coach_ID '
                                      'WHERE Verified = "FALSE"').fetchall()
    conn.close()
    return render_template("verifyCoaches.html", coaches=unverified_Coaches)


# logic for coach verification
@app.route('/verify_coach', methods=["GET", "POST"])
def verifyCoach():
    # gets coachID
    coachID = request.form['verify_coach']
    conn = get_db_connection()
    # updates coach status to verified
    coach_mail = conn.execute('SELECT Email From User WHERE User_ID=?', (coachID,)).fetchone()[0]
    conn.execute('UPDATE Coach SET Verified = "TRUE" WHERE Coach_ID=?', (coachID,))
    conn.commit()
    conn.close()
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = '*******'
    app.config['MAIL_PASSWORD'] = '******'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail = Mail(app)
    msg = Message('FitHub Verification', sender='******', recipients=[coach_mail])
    msg.body = "Congratulation! You got verified, you can now access our site as a coach :D"
    mail.send(msg)
    # return to admin page
    return redirect(url_for('unverifiedCoaches'))


# logic for coach denial
@app.route('/deny_coach', methods=["GET", "POST"])
def denyCoach():
    # gets coachID
    coachID = request.form['deny_coach']
    conn = get_db_connection()
    # delete coach from coach & user tables
    conn.execute('DELETE FROM Coach WHERE Coach_ID=?', (coachID,))
    conn.execute('DELETE FROM User WHERE User_ID=?', (coachID,))
    conn.commit()
    conn.close()
    # return to admin page
    return redirect(url_for('unverifiedCoaches'))


# route to display and create posts
@app.route('/posts', methods=['GET', 'POST'])
def posts():
    # check if a user is logged in
    if 'User_ID' in session:
        User_ID = session['User_ID']  # get user id from session
        conn = get_db_connection()  # connect to database

        # fetch user information from the database
        user = conn.execute('SELECT * FROM User WHERE User_ID = ?', (User_ID,)).fetchone()

        # fetch all available interests from the database
        all_interests = conn.execute('SELECT * FROM Interest').fetchall()

        # handle post submission
        if request.method == 'POST':
            post_content = request.form['content']  # get post content
            post_media = request.form.get('media')  # get post media (to be handled)
            selected_tags = request.form.getlist('tags')  # get selected tags as a list

            # calculate new post id
            postid_count = conn.execute('SELECT COUNT(*) FROM Post').fetchone()
            postid = postid_count[0] + 1  # increment post count for unique id

            # get current datetime in standardized format
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

            # save post to database with tags as a slash-separated string
            tags_str = '/'.join(selected_tags)
            conn.execute(
                '''INSERT INTO Post (Post_ID, User_ID, Content, Time_Stamp, Media, Tags)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (postid, user['User_ID'], post_content, current_time, post_media, tags_str)
            )
            conn.commit()  # commit changes to database

        # get user interests as a list
        user_interests = user['Interests'].split(',') if user['Interests'] else []
        posts_by_interest = []  # initialize posts matching user interests

        # fetch posts matching user interests
        if user_interests:
            placeholders = ', '.join(['?'] * len(user_interests))  # placeholders for query
            posts_by_interest = conn.execute(
                f'''SELECT Post.*, User.Name AS Username
                    FROM Post
                    JOIN User ON Post.User_ID = User.User_ID
                    WHERE EXISTS (
                        SELECT 1 FROM Interest
                        WHERE Interest.Name IN ({placeholders})
                          AND Post.Tags LIKE '%' || Interest.Interest_ID || '%'
                    )
                    ORDER BY Post.Time_Stamp DESC''',
                tuple(user_interests)
            ).fetchall()

        # fetch remaining posts not matching user interests
        remaining_posts = conn.execute(
            '''SELECT Post.*, User.Name AS Username
               FROM Post
               JOIN User ON Post.User_ID = User.User_ID
               WHERE Post.Post_ID NOT IN (
                   SELECT Post.Post_ID
                   FROM Post
                   JOIN Interest
                   ON Post.Tags LIKE '%' || Interest.Interest_ID || '%'
                   WHERE Interest.Name IN ({}))
               ORDER BY Post.Time_Stamp DESC'''.format(', '.join(['?'] * len(user_interests))),
            tuple(user_interests)
        ).fetchall() if user_interests else conn.execute(
            '''SELECT Post.*, User.Name AS Username
               FROM Post
               JOIN User ON Post.User_ID = User.User_ID
               ORDER BY Post.Time_Stamp DESC'''
        ).fetchall()

        # combine and sort all posts by timestamp
        all_posts = sorted(posts_by_interest + remaining_posts, key=lambda x: x['Time_Stamp'], reverse=True)

        # fetch all comments with usernames
        comments_with_usernames = conn.execute('''
            SELECT Comment.*, User.Name AS Username
            FROM Comment
            JOIN User ON Comment.User_ID = User.User_ID
        ''').fetchall()

        # combine posts with their respective comments
        posts_with_comments = []
        for post in all_posts:
            post_comments = [
                {'Username': comment['Username'], 'Content': comment['Content']}
                for comment in comments_with_usernames
                if comment['Post_ID'] == post['Post_ID']
            ]
            posts_with_comments.append({
                'post': {
                    'Post_ID': post['Post_ID'],
                    'Content': post['Content'],
                    'Media': post['Media'],
                    'Username': post['Username'],
                    'User_ID': post['User_ID'],
                    'Time_Stamp': post['Time_Stamp']
                },
                'comments': post_comments
            })

        conn.close()  # close database connection
        # render posts page with user, posts, and interests
        return render_template("posts.html", user=user, posts_with_comments=posts_with_comments,
                               interests=all_interests)

    # redirect to login page if no user is logged in
    return redirect(url_for('login'))


# route to add a comment to a post
@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    # check if a user is logged in
    if 'User_ID' in session:
        User_ID = session['User_ID']  # get user id from session
        conn = get_db_connection()  # connect to database

        # calculate new comment id
        commentid_count = conn.execute('SELECT COUNT(*) FROM Comment').fetchone()
        commentid = commentid_count[0] + 1  # increment comment count for unique id

        # get comment content from form
        comment_content = request.form['comment_content']

        # get current datetime in standardized format
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # save comment to database
        conn.execute(
            'INSERT INTO Comment (Comment_ID, Post_ID, User_ID, Content, Time_Stamp) VALUES (?, ?, ?, ?, ?)',
            (commentid, post_id, User_ID, comment_content, current_time)
        )
        conn.commit()  # commit changes to database
        conn.close()  # close database connection

        # redirect back to posts page
        return redirect(url_for('posts'))

    # redirect to login page if no user is logged in
    return redirect(url_for('login'))


# Coach can add new recipes
@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'User_ID' not in session:
        return redirect(url_for('login'))

    User_ID = str(session['User_ID'])
    if request.method == 'POST':
        recipe_name = request.form.get('Recipe_Name')
        meal_type = request.form.get('Meal_Type')
        nutrition_info = request.form.get('Nutrition_Information')
        media = request.form.get('Media')
        steps = request.form.get('Steps')
        ingredients = request.form.get('Ingredients')

        # Validate form data
        if not recipe_name or not meal_type or not nutrition_info or not media or not steps or not ingredients:
            return "All fields are required!"

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Find the max Recipe_ID and increment it
            cursor.execute("SELECT MAX(CAST(Recipe_ID AS INTEGER)) FROM Recipe")
            max_id = cursor.fetchone()[0]
            new_recipe_id = str((max_id + 1) if max_id is not None else 1)  # Handle case where table is empty

            print(f"Generated new Recipe_ID: {new_recipe_id}")

            # Insert the new recipe
            cursor.execute("""
                INSERT INTO Recipe (Recipe_ID, Coach_ID, Recipe_Name, Meal_Type,
                Nutrition_Information, Media, Steps, Ingredients)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_recipe_id, User_ID, recipe_name, meal_type, nutrition_info, media, steps, ingredients))

            conn.commit()

            print(f"New Recipe added successfully with ID: {new_recipe_id}")

        except Exception as e:
            print(f"Error occurred while adding recipe: {str(e)}")
            return f"An error occurred: {str(e)}. Please try again later."

        return redirect(url_for('GetRecipes'))

    return render_template('add_recipe.html')


# Show all recipes to user
@app.route('/recipes', methods=['GET'])
def GetRecipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Recipe")
    recipes = cursor.fetchall()

    recipes_data = [{
        'Recipe_ID': str(row[0]),
        'Recipe_Name': row[3],
        'Meal_Type': row[2],
        'Media': row[4],
        'Ingredients': row[5],
        'Steps': row[6],
        'Nutrition_Information': row[7]
    } for row in recipes]

    return render_template('recipes.html', recipes=recipes_data)


# Show recipes details when the user click on more details
@app.route('/recipes/<recipe_id>', methods=['GET'])
def GetRecipeDetails(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Recipe WHERE Recipe_ID = ?", (recipe_id,))
    recipe = cursor.fetchone()

    if recipe is None:
        return "Recipe not found", 404

    recipe_data = {
        'Recipe_ID': str(recipe[0]),
        'Recipe_Name': recipe[3],
        'Meal_Type': recipe[2],
        'Media': recipe[4],
        'Ingredients': recipe[5],
        'Steps': recipe[6],
        'Nutrition_Information': recipe[7]
    }

    return render_template('recipes_detailed.html', recipe=recipe_data)


# Show coach details for trainee so that he can add the suitable coach for him
@app.route('/coaches', methods=['GET'])
def GetCoach():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT  Coach_ID, Verified, Description, Experience, Certificates
    FROM Coach
    """
    cursor.execute(query)
    result = cursor.fetchall()
    coaches_data = [
        {"Coach_ID": row[0], "Verified": row[1], "Description": row[2], "Experience": row[3], "Certificates": row[4],
         } for row in result]

    return render_template('coaches_details.html', coaches=coaches_data)


# show exercises for users
@app.route('/exercises', methods=['GET'])
def GetExercises():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Exercise")
        Exercises_data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        # Filter out entries with None Exercise_ID
        valid_exercises = [exercise for exercise in Exercises_data if exercise['Exercise_ID'] is not None]

        return render_template('exercises.html', Exercises=valid_exercises)
    except Exception as e:
        print(f"Error fetching exercises: {e}")
        return "Error fetching exercises", 500


# Show more details for user about the clicked exercises
@app.route('/exercise/<int:exercise_id>', methods=['GET'])
def GetExerciseDetails(exercise_id):
    print(f"Received exercise_id: {exercise_id}")
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT Exercise_ID, Coach_ID, Name, Media, Duration,Equipment,Description,Muscles_Targeted
        FROM Exercise
        WHERE CAST(Exercise_ID AS TEXT) = ?
    """
    cursor.execute(query, (str(exercise_id),))
    result = cursor.fetchone()
    if result:
        exercise_details = {
            "Exercise_ID": result["Exercise_ID"],
            "Coach_ID": result["Coach_ID"],
            "Name": result["Name"],
            "Media": result["Media"],
            "Duration": result["Duration"],
            "Description": result["Description"],
            "Equipment": result["Equipment"],
            "Muscles_Targeted": result["Muscles_Targeted"]
        }
        return render_template('exercises_detailed.html', exercise=exercise_details)
    else:
        print("No exercise found with this ID.")
        return "Exercise not found", 404


# Coach can add new exercises
@app.route('/add_exercises', methods=['GET', 'POST'])
def AddExercises():
    if 'User_ID' not in session:
        return redirect(url_for('login'))

    User_ID = str(session['User_ID'])

    if request.method == 'POST':
        name = request.form['Name']
        media = request.form['Media']
        duration = request.form['Duration']
        equipment = request.form['Equipment']
        description = request.form['Description']
        muscles_targeted = request.form['Muscles_Targeted']

        # Validate form data
        if not name or not media or not duration or not equipment or not description or not muscles_targeted:
            flash("All fields are required!", 'error')
            return redirect(url_for('AddExercises'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            while True:  # add a new random exercise id
                random_exercise_id = random.randint(1000, 9999)
                cursor.execute("SELECT 1 FROM Exercise WHERE Exercise_ID = ?", (random_exercise_id,))
                if not cursor.fetchone():
                    break

            cursor.execute("""
                INSERT INTO Exercise (Exercise_ID, Coach_ID, Name, Media,
                Duration, Equipment, Description, Muscles_Targeted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (random_exercise_id, User_ID, name, media, duration, equipment, description, muscles_targeted))

            conn.commit()
            conn.close()

            flash(f"Exercise added successfully with ID: {random_exercise_id}!", 'success')
            return redirect(url_for('GetExerciseDetails', exercise_id=random_exercise_id))

        except Exception as e:
            print(f"Error occurred while adding exercise: {str(e)}")
            flash(f"An error occurred: {str(e)}. Please try again later.", 'error')
            return redirect(url_for('AddExercises'))

    return render_template('add_exercise.html')


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
