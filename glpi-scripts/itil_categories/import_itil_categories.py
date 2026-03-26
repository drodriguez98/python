import mysql.connector
import csv

# Database connection configuration
db_config = {
    'host': 'localhost',  # Change to your host
    'user': 'glpi',  # Change to your username
    'password': 'abc123.',  # Change to your password
    'database': 'glpi'  # Change to your database
}

# Function to convert "Yes/No" to 1/0
def yes_no_to_binary(value):
    return 1 if value.lower() == 'sí' else 0

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # SQL query to insert data into the table, including the completename field
    sql_insert = """
    INSERT INTO glpi_itilcategories (entities_id, is_recursive, name, completename, is_incident, is_request, is_problem, is_change)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Open the CSV file and insert data row by row
    with open('itil_categories_to_import.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Insert each row from the CSV into the database
            cursor.execute(
                sql_insert,
                (
                    0,  # entities_id is always 0 for the root entity
                    yes_no_to_binary(row['is_recursive']),  # is_recursive
                    row['name'],  # name
                    row['name'],  # completename, which is the same as name
                    yes_no_to_binary(row['is_incident']),  # is_incident
                    yes_no_to_binary(row['is_request']),  # is_request
                    yes_no_to_binary(row['is_problem']),  # is_problem
                    yes_no_to_binary(row['is_change'])  # is_change
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
