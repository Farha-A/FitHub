import sqlite3
import requests

# Path to the SQLite database
db_path = 'F:/CSAI/3rd year/Fall/Introduction to Software Engineering/FitHub/FitHub_DB.sqlite'

def download_image_to_binary(url):
    """
    Downloads an image from a URL and converts it to binary data.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content  # Return binary content of the image
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def update_exercise_table_with_binary():
    """
    Updates the 'Media' column in the 'Exercise' table with binary data.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Fetch all rows from the Exercise table
        cursor.execute("SELECT Exercise_ID, Media FROM Exercise")
        rows = cursor.fetchall()

        for exercise_id, media_url in rows:
            if media_url:
                print(f"Processing Exercise_ID {exercise_id} with Media URL: {media_url}")
                binary_data = download_image_to_binary(media_url)
                if binary_data:
                    # Update the Media column with binary data
                    cursor.execute(
                        "UPDATE Exercise SET Media = ? WHERE Exercise_ID = ?",
                        (binary_data, exercise_id)
                    )
                    print(f"Updated Exercise_ID {exercise_id} with binary data.")
                else:
                    print(f"Failed to fetch image for Exercise_ID {exercise_id}.")
            else:
                print(f"No Media URL for Exercise_ID {exercise_id}.")

        conn.commit()
        print("Exercise table updated successfully with binary data.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# Execute the function
update_exercise_table_with_binary()
