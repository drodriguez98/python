# Importar usuarios en GLPI a partir de un CSV con las siguientes columnas en la cabecera: username,firstname,realname,email,entity,profile,group.

# Nota: Los usuarios se añaden en una entidad con un determinado perfil y opcionalmente a un grupo, pero los añade sin contraseña (de momento).

import csv
import mysql.connector
from mysql.connector import Error

# Configuración de la conexión a la base de datos
db_config = {
    'user': 'glpi',
    'password': 'abc123.',
    'host': 'localhost',
    'database': 'glpi',
    'port': 3306
}

def connect_db():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Conexión exitosa a la base de datos")
            return connection
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def get_entity_id(connection, entity_name):
    cursor = connection.cursor()
    query = "SELECT id FROM glpi_entities WHERE completename = %s"
    cursor.execute(query, (entity_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def get_profile_id(connection, profile_name):
    cursor = connection.cursor()
    query = "SELECT id FROM glpi_profiles WHERE name = %s"
    cursor.execute(query, (profile_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def get_group_id(connection, group_name):
    cursor = connection.cursor()
    query = "SELECT id FROM glpi_groups WHERE name = %s"
    cursor.execute(query, (group_name,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def insert_user(connection, username, firstname, realname, profile_id, entity_id):
    cursor = connection.cursor()
    query = """INSERT INTO glpi_users
               (name, realname, firstname, locations_id, profiles_id, entities_id, authtype, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(query, (username, realname, firstname, 0, profile_id, entity_id, 1, 1))
    connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id

def assign_user_to_group(connection, user_id, group_id):
    cursor = connection.cursor()
    query = """INSERT INTO glpi_groups_users (users_id, groups_id)
               VALUES (%s, %s)"""
    cursor.execute(query, (user_id, group_id))
    connection.commit()
    cursor.close()

def assign_profile_to_user(connection, user_id, profile_id, entity_id):
    cursor = connection.cursor()
    query = """INSERT INTO glpi_profiles_users (users_id, profiles_id, entities_id)
               VALUES (%s, %s, %s)"""
    cursor.execute(query, (user_id, profile_id, entity_id))
    connection.commit()
    cursor.close()

def insert_or_update_email(connection, user_id, email):
    cursor = connection.cursor()
    # Verificar si el email ya existe para el usuario
    query = "SELECT id FROM glpi_useremails WHERE users_id = %s AND email = %s"
    cursor.execute(query, (user_id, email))
    existing_email = cursor.fetchone()

    if existing_email:
        print(f"El email {email} ya está asociado al usuario {user_id}.")
    else:
        # Insertar nuevo email
        query = """INSERT INTO glpi_useremails (users_id, email, is_default, is_dynamic)
                   VALUES (%s, %s, %s, %s)"""
        cursor.execute(query, (user_id, email, 0, 0))
        connection.commit()
        print(f"Email {email} añadido para el usuario {user_id}.")

    cursor.close()

def main():
    connection = connect_db()
    if connection:
        with open('glpi_users.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                username = row['username']
                firstname = row['firstname']
                realname = row['realname']
                profile_name = row['profile']
                entity_name = row['entity']
                group_name = row['group']
                email = row.get('email')  # Añadido para capturar el email

                profile_id = get_profile_id(connection, profile_name)
                entity_id = get_entity_id(connection, entity_name)
                group_id = get_group_id(connection, group_name)

                if not profile_id:
                    print(f"Error: No se pudo encontrar el perfil '{profile_name}' para el usuario {username}")
                if not entity_id:
                    print(f"Error: No se pudo encontrar la entidad '{entity_name}' para el usuario {username}")
                if not group_id:
                    print(f"Error: No se pudo encontrar el grupo '{group_name}' para el usuario {username}")

                if profile_id and entity_id and group_id:
                    user_id = insert_user(connection, username, firstname, realname, profile_id, entity_id)
                    assign_user_to_group(connection, user_id, group_id)
                    assign_profile_to_user(connection, user_id, profile_id, entity_id)
                    if email:  # Añadido para añadir el email si está presente
                        insert_or_update_email(connection, user_id, email)
                    print(f"Usuario {username} importado exitosamente")
                else:
                    print(f"Error: No se pudo importar el usuario {username} debido a la falta de información")

        connection.close()

if __name__ == "__main__":
    main()