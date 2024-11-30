# importing necessary libraries
from flask import Flask, render_template, request, session, flash, redirect, url_for
import sqlite3
import random

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
    # get all interests from database to show in form
    conn = get_db_connection()
    all_interests = conn.execute('SELECT * FROM Interest').fetchall()
    conn.close()
    return render_template("traineeSignUp.html", interests=all_interests)


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

@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if 'User_ID' in session:
        User_ID = session['User_ID']
        conn = get_db_connection()

        # user info
        user = conn.execute('SELECT * FROM User WHERE User_ID = ?', (User_ID,)).fetchone()

        # available tags/Interests
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
            tags_str = '/'.join(selected_tags)  # save tags  "seperated by slash"
            conn.execute(
                '''INSERT INTO Post (Post_ID, User_ID, Content, Time_Stamp, Media, Tags) 
                   VALUES (?, ?, ?, datetime("now"), ?, ?)''',
                (postid, user['User_ID'], post_content, post_media, tags_str)
            )
            conn.commit()

        # user interests and corresponding posts
        user_interests = user['Interests'].split(',')  # Get user interests as a list
        placeholders = ', '.join(['?'] * len(user_interests))
        interest_ids = conn.execute(
            'SELECT Interest_ID FROM Interest WHERE Name IN (' + placeholders + ')',
            tuple(user_interests)
        ).fetchall()

        # list of Interest_IDs
        interest_ids = [str(row['Interest_ID']) for row in interest_ids]
        placeholders_for_interest_ids = ', '.join(['?'] * len(interest_ids))

        # Fetch posts by interest with ORDER BY Time_Stamp DESC
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

        # Combine posts and ensure the final list is sorted by Time_Stamp
        all_posts = posts_by_interest + remaining_posts
        all_posts = sorted(all_posts, key=lambda x: x['Time_Stamp'], reverse=True)

        posts_with_usernames = conn.execute(''' 
            SELECT Post.*, User.Name 
            FROM Post 
            JOIN User ON Post.User_ID = User.User_ID
        ''').fetchall()

        posts_with_comments = []
        for post in posts_with_usernames:
            post_data = {
                'post': {
                    'Post_ID': post['Post_ID'],
                    'Content': post['Content'],
                    'Media': post['Media'],
                    'Username': post['Name'],  
                    'User_ID': post['User_ID']  
                }
            }
            
            # add comment for post
            comments = conn.execute('SELECT * FROM Comment WHERE Post_ID = ?', (post['Post_ID'],)).fetchall()
            post_data['comments'] = comments
            
            posts_with_comments.append(post_data)

        conn.close()

        return render_template("posts.html", user=user, posts_with_comments=posts_with_comments, interests=all_interests)

    return redirect(url_for('login'))


@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'User_ID' in session:
        User_ID = session['User_ID']
        conn = get_db_connection()

        # get the comment ID 
        commentid_count = conn.execute('SELECT COUNT(*) FROM Comment').fetchone()
        commentid = commentid_count[0] + 1

        # get comment content from the form
        comment_content = request.form['comment_content']

        # Insert comment into  database
        conn.execute(
            'INSERT INTO Comment (Comment_ID, Post_ID, User_ID, Content, Time_Stamp) VALUES (?, ?, ?, ?, datetime("now"))',
            (commentid, post_id, User_ID, comment_content)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('posts'))
    return redirect(url_for('login'))

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'User_ID' not in session:
        return redirect(url_for('login'))  # Redirect to log in if no User_ID in session

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
            random_recipe_id = random.randint(1000, 9999)

            print(f"Generated random Recipe_ID: {random_recipe_id}")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO Recipe (Recipe_ID, Coach_ID, Recipe_Name, Meal_Type, Nutrition_Information,
                                                        Media, Steps, Ingredients)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (random_recipe_id, User_ID, recipe_name, meal_type, nutrition_info, media, steps, ingredients))

            conn.commit()

            print(f"New Recipe added successfully with ID: {random_recipe_id}")

        except Exception as e:
            print(f"Error occurred while adding recipe: {str(e)}")
            return f"An error occurred: {str(e)}. Please try again later."

        return redirect(url_for('GetRecipes'))

    return render_template('add_recipe.html')


@app.route('/recipes', methods=['GET'])
def GetRecipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT Recipe_ID, Coach_ID, Meal_Type, Recipe_Name, Media, Ingredients, Steps, Nutrition_Information
    FROM Recipe
    """

    cursor.execute(query)
    result = cursor.fetchall()
    recipes_data = [
        {"Recipe_ID": row[0], "Coach_ID": row[1], "Meal_Type": row[2], "Recipe_Name": row[3], "Media": row[4],
         'Ingredients': row[5],
         "Steps": row[6], "Nutrition_Information": row[7]} for row in result]

    return render_template('recipes.html', recipes=recipes_data)


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

    return render_template('coaches.html', coaches=coaches_data)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
