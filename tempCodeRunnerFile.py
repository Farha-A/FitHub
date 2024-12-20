# show exercises for users
@app.route('/exercises', methods=['GET'])
def GetExercises():
    try:
        # Fetch exercises from SQL database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Exercise")
        Exercises_data = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Authenticate with Google Drive
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)

        # Fetch images from Google Drive folder
        results = service.files().list(
            q=f"'{MAIN_FOLDER_ID}' in parents and trashed=false",
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get('files', [])
        if not files:
            print("No images found in Google Drive folder.")

        # Prepare a mapping of exercise images
        exercise_images = {}
        for file in files:
            # Check if the file name matches the exercise image naming convention
            for exercise in Exercises_data:
                exercise_id = exercise['Exercise_ID']
                if f"exercise{exercise_id}" in file['name']:
                    exercise_images[exercise_id] = get_file_url(file['id'])

        # Combine exercise metadata with image URLs
        for exercise in Exercises_data:
            exercise_id = exercise['Exercise_ID']
            exercise['Image_URL'] = exercise_images.get(exercise_id, None)

        return render_template('exercises.html', Exercises=Exercises_data)
    except Exception as e:
        print(f"Error fetching exercises: {e}")
        return "Error fetching exercises", 500
