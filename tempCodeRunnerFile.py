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

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    # Ensure that User_ID exists in the session
    if 'User_ID' not in session:
        return redirect(url_for('login'))  # Redirect to login if User_ID is not found in session

    User_ID = str(session['User_ID'])  # Convert User_ID to string

    if request.method == 'POST':
        # Extract form data
        Coach_ID = User_ID
        recipe_name = request.form['Recipe_Name']
        meal_type = request.form['Meal_Type']
        nutrition_info = request.form['Nutrition_Information']
        media = request.form['Media']
        steps = request.form['Steps']

        # Ensure that all form fields are filled
        if not recipe_name or not meal_type or not nutrition_info or not steps:
            return "All fields are required!"

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Prepare the SQL query to insert data into the Recipe table
        cursor.execute("""
            INSERT INTO Recipe (Coach_ID, Recipe_Name, Meal_Type, Nutrition_Information, Media, Steps)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (Coach_ID, recipe_name, meal_type, nutrition_info, media, steps))

        # Commit the transaction to the database
        conn.commit()

        # Redirect to the GetRecipes route after inserting the recipe
        return redirect(url_for('GetRecipes'))

    # Render the form template for GET requests
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
    recipes_data = [{"Recipe_ID": row[0], "Coach_ID": row[1], "Meal_Type": row[2], "Recipe_Name": row[3],"Media":row[4],
                     "Steps": row[5], "Nutrition_Information": row[6]} for row in result]

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
    recipes_data = [{"Coach_ID": row[0], "Verified": row[1], "Description": row[2], "Experience": row[3],"Certificates":row[4],
                    } for row in result]

    return render_template('coaches.html', recipes=recipes_data)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
