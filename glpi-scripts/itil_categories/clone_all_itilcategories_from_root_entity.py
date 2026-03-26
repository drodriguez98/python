# Clonar todas las categorías ITIL de la entidad raíz en las demás entidades existentes en GLPI.

import mysql.connector
from mysql.connector import Error

def clone_itil_categories_to_entities():
    try:
        # Conexión a la base de datos
        connection = mysql.connector.connect(
            host='localhost',       # Dirección IP del contenedor de MariaDB
            port=3306,              # Puerto por defecto para MariaDB/MySQL
            user='glpi',            # Usuario de la base de datos
            password='abc123.',     # Contraseña del usuario
            database='glpi'         # Nombre de la base de datos
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # Obtener la entidad raíz (suponiendo que es la entidad con id 0 o cualquier otro id que represente la entidad raíz)
            root_entity_id = 0

            # Obtener todas las categorías ITIL de la entidad raíz
            query_get_itil_categories = """
            SELECT * FROM glpi_itilcategories WHERE entities_id = %s
            """
            cursor.execute(query_get_itil_categories, (root_entity_id,))
            itil_categories = cursor.fetchall()

            if not itil_categories:
                print("No se encontraron categorías ITIL en la entidad raíz.")
                return

            # Obtener todas las entidades (excepto la raíz)
            query_get_entities = """
            SELECT id FROM glpi_entities WHERE id != %s
            """
            cursor.execute(query_get_entities, (root_entity_id,))
            entities = cursor.fetchall()

            if not entities:
                print("No se encontraron entidades en la base de datos.")
                return

            # Clonar las categorías ITIL a cada entidad
            query_clone_itil_category = """
            INSERT INTO glpi_itilcategories (
                entities_id, is_recursive, itilcategories_id, name, completename,
                comment, level, knowbaseitemcategories_id, users_id, groups_id,
                code, ancestors_cache, sons_cache, is_helpdeskvisible,
                tickettemplates_id_incident, tickettemplates_id_demand,
                changetemplates_id, problemtemplates_id, is_incident,
                is_request, is_problem, is_change, date_mod, date_creation
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """

            for entity in entities:
                entity_id = entity['id']

                for category in itil_categories:
                    # Clonamos la categoría ITIL para la nueva entidad
                    cursor.execute(query_clone_itil_category, (
                        entity_id,
                        category['is_recursive'],
                        category['itilcategories_id'],
                        category['name'],
                        category['completename'],
                        category['comment'],
                        category['level'],
                        category['knowbaseitemcategories_id'],
                        category['users_id'],
                        category['groups_id'],
                        category['code'],
                        category['ancestors_cache'],
                        category['sons_cache'],
                        category['is_helpdeskvisible'],
                        category['tickettemplates_id_incident'],
                        category['tickettemplates_id_demand'],
                        category['changetemplates_id'],
                        category['problemtemplates_id'],
                        category['is_incident'],
                        category['is_request'],
                        category['is_problem'],
                        category['is_change']
                    ))

            # Confirmar cambios
            connection.commit()
            print("Categorías ITIL clonadas correctamente a todas las entidades.")

    except Error as e:
        print(f"Error: {e}")
        if connection.is_connected():
            connection.rollback()
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada.")

# Ejecutar el script
clone_itil_categories_to_entities()