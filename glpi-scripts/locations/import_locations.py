import mysql.connector
import csv

# Database connection configuration
db_config = {
    'host': 'localhost',  # Change to your host
    'user': 'glpi',  # Change to your username
    'password': 'abc123.',  # Change to your password
    'database': 'glpi'  # Change to your database
}

def get_parent_id(cursor, parent_name):
    """Retrieve the ID of the parent location based on its name."""
    if not parent_name:
        return 0  # No parent
    query = "SELECT id FROM glpi_locations WHERE name = %s LIMIT 1"
    cursor.execute(query, (parent_name,))
    result = cursor.fetchone()
    return result[0] if result else 0

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # SQL query to insert data into the table
    sql_insert = """
    INSERT INTO glpi_locations (entities_id, is_recursive, name, completename, locations_id, address, postcode, town, state, country, building, room, latitude, longitude)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Open the CSV file and insert data row by row
    with open('locations_to_import.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Find the parent location ID
            parent_id = get_parent_id(cursor, row['parent_name'])

            # Insert each row from the CSV into the database
            cursor.execute(
                sql_insert,
                (
                    0,  # entities_id is always 0 for the root entity
                    1,  # is_recursive, default to 0 (No)
                    row['name'],  # name
                    row['completename'],  # completename
                    parent_id,  # locations_id (parent location ID)
                    row['address'],  # address
                    row['postcode'],  # postcode
                    row['town'],  # town
                    row['state'],  # state
                    row['country'],  # country
                    row['building'],  # building
                    row['room'],  # room
                    row['latitude'],  # latitude
                    row['longitude']  # longitude
                )
            )

    # Commit the changes
    conn.commit()
    print("Data inserted successfully.")

except mysql.connector.Error as err:
    print(f"Error: {err}")
    conn.rollback()
finally:
    # Close the connection
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("Database connection closed.")