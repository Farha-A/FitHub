# importing necessary libraries
from flask import Flask, render_template, request, session, flash, redirect, url_for
import sqlite3
import random
from datetime import datetime


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
        return render_template("homepage.html", user=user)
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
            return redirect(url_for('home_page'))
        # if not flash a message to inform them they can't access the site yet
        return "Please wait to be verified :)"
    return redirect(url_for('home_page'))


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
            # add trainee to user table
            conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, Role, Interests) '
                         'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                         (userid, username, email, age, gender, password, role, interests))

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
    return render_template("traineeSignUp.html", interests=all_interests, email_exists=email_exists)


# coach sign-up
@app.route('/coach', methods=["GET", "POST"])
def coachSignUp():
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
        conn.execute('INSERT INTO User (User_ID, Name, Email, Age, Gender, Password, Role, Interests) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (userid, username, email, age, gender, password, role, interests))

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
    return render_template("coachSignUp.html", interests=all_interests)


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
    conn.execute('UPDATE Coach SET Verified = "TRUE" WHERE Coach_ID=?', (coachID,))
    conn.commit()
    conn.close()
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
        return render_template("posts.html", user=user, posts_with_comments=posts_with_comments, interests=all_interests)

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






#Coach can add new recipes
@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'User_ID' not in session:
        return redirect(url_for('login'))

    User_ID = str(session['User_ID'])
    
    if request.method == 'POST':
        # Get form data
        recipe_name = request.form.get('Recipe_Name')
        meal_type = request.form.get('Meal_Type')
        nutrition_info = request.form.get('Nutrition_Information')
        media = request.files.get('Media')
        steps = request.form.get('Steps')
        ingredients = request.form.get('Ingredients')
        if not (recipe_name and meal_type and nutrition_info and media and steps and ingredients):
            flash("All fields are required!", 'error')
            return redirect(url_for('add_recipe'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Generate a new Recipe_ID
            cursor.execute("SELECT MAX(CAST(Recipe_ID AS INTEGER)) FROM Recipe")
            max_id = cursor.fetchone()[0]
            new_recipe_id = str((max_id + 1) if max_id is not None else 1)  # Handle case where table is empty
            print(f"Generated new Recipe_ID: {new_recipe_id}")
            temp_path = f"uploads/{media.filename}"
            media.save(temp_path)

            # Upload media file and get its unique identifier
            drive_file_id = upload(temp_path, media.filename)
            if not drive_file_id:
                os.remove(temp_path) 
                flash("Failed to upload media file. Please try again.", 'error')
                return redirect(url_for('add_recipe'))
            
            os.remove(temp_path)
            print(f"Uploaded media file ID: {drive_file_id}")

            # Insert the new recipe details into the database
            cursor.execute("""
                INSERT INTO Recipe (Recipe_ID, Coach_ID, Recipe_Name, Meal_Type, Nutrition_Information, Media, Steps, Ingredients)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_recipe_id, User_ID, recipe_name, meal_type, nutrition_info, drive_file_id, steps, ingredients))

            conn.commit()
            conn.close()

            print(f"New Recipe added successfully with ID: {new_recipe_id}")
            flash(f"Recipe added successfully with ID: {new_recipe_id}!", 'success')
            return redirect(url_for('GetRecipes'))

        except Exception as e:
            print(f"Error occurred while adding recipe: {str(e)}")
            flash(f"An error occurred: {str(e)}. Please try again later.", 'error')
            return redirect(url_for('add_recipe'))

    return render_template('add_recipe.html')


#Show all recipes to user
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


#Show recipes details when the user click on more details 
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


#Show coach details for trainee so that he can add the suitable coach for him
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


#show exercises for users
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


@app.route('/add_exercise_to_trainee', methods=['POST'])
def add_exercise_to_trainee():
    if 'User_ID' not in session:
        flash("You need to be logged in to perform this action.", "danger")
        return redirect(url_for('login'))

    user_id = session['User_ID']
    exercise_id = request.form.get('exercise_id')

    conn = get_db_connection()

    try:
        # Verify the user is a trainee
        trainee = conn.execute('SELECT * FROM Trainee WHERE Trainee_ID = ?', (user_id,)).fetchone()
        if not trainee:
            flash("You are not authorized to add exercises.", "danger")
            return redirect(url_for('GetExercises'))

        # Verify the exercise exists
        exercise = conn.execute('SELECT * FROM Exercise WHERE Exercise_ID = ?', (exercise_id,)).fetchone()
        if not exercise:
            flash("Exercise not found.", "danger")
            return redirect(url_for('GetExercises'))

        # Fetch the current date
        today_date = datetime.now().strftime("%Y-%m-%d")

        # Check if the exercise already exists for the trainee on the current date
        existing_entry = conn.execute(
            """SELECT * FROM Trainee_Exercises 
               WHERE Trainee_ID = ? AND Exercise_ID = ? AND DATE(Timestamp) = ?""",
            (user_id, exercise_id, today_date)
        ).fetchone()

        if existing_entry:
            flash("You have already added this exercise for today.", "warning")
        else:
            # Insert a new entry
            conn.execute(
                """INSERT INTO Trainee_Exercises (Trainee_ID, Timestamp, Trainee_Calories_Burned, Exercise_ID)
                   VALUES (?, ?, ?, ?)""",
                (user_id, today_date, 0, exercise_id)  # Set Trainee_Calories_Burned to 0 or calculate if needed
            )
            conn.commit()
            flash("Exercise added successfully!", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for('GetExerciseDetails', exercise_id=exercise_id))

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)

    