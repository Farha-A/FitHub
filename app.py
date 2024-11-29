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
    return redirect(url_for('home_page'))


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
        return redirect(url_for('login'))
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
        expYears = str(request.form['expYears']) + " years"
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
        return redirect(url_for('login'))
    return render_template("coachSignUp.html")


@app.route('/admin', methods=["GET", "POST"])
def unverifiedCoaches():
    conn = get_db_connection()
    unverifiedCoaches = conn.execute('SELECT * FROM Coach JOIN User ON User_ID=Coach_ID '
                                     'WHERE Verified = "FALSE"').fetchall()
    conn.close()
    return render_template("verifyCoaches.html", coaches=unverifiedCoaches)


@app.route('/verify', methods=["GET", "POST"])
def verifyCoach():
    coachID = request.form['verify']
    conn = get_db_connection()
    conn.execute('UPDATE Coach SET Verified = "TRUE" WHERE Coach_ID=?', (coachID,))
    conn.commit()
    conn.close()
    return redirect(url_for('unverifiedCoaches'))


@app.route('/deny', methods=["GET", "POST"])
def denyCoach():
    coachID = request.form['deny']
    conn = get_db_connection()
    conn.execute('DELETE FROM Coach WHERE Coach_ID=?', (coachID,))
    conn.execute('DELETE FROM User WHERE User_ID=?', (coachID,))
    conn.commit()
    conn.close()
    return redirect(url_for('unverifiedCoaches'))

import random

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'User_ID' not in session:
        return redirect(url_for('login'))  # Redirect to login if no User_ID in session
    
    User_ID = str(session['User_ID'])  # Convert session User_ID to string
    
    if request.method == 'POST':
        # Get values from the form fields
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
            # Generate a random Recipe_ID
            random_recipe_id = random.randint(1000, 9999)

            print(f"Generated random Recipe_ID: {random_recipe_id}")

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Recipe (Recipe_ID, Coach_ID, Recipe_Name, Meal_Type, Nutrition_Information, Media, Steps, Ingredients)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (random_recipe_id, User_ID, recipe_name, meal_type, nutrition_info, media, steps, ingredients))

            conn.commit()

            # Print the new Recipe_ID for debugging
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
    recipes_data = [{"Recipe_ID": row[0], "Coach_ID": row[1], "Meal_Type": row[2], "Recipe_Name": row[3],"Media":row[4],'Ingredients':row[5],
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
    coaches_data = [{"Coach_ID": row[0], "Verified": row[1], "Description": row[2], "Experience": row[3],"Certificates":row[4],
                    } for row in result]

    return render_template('coaches.html', coaches=coaches_data)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
