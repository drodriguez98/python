# Clonar todas las notificaciones de la entidad raíz en las demás entidades existentes en GLPI.

import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        # Configura los parámetros de conexión
        connection = mysql.connector.connect(
            host='localhost',       # Dirección IP del contenedor de MariaDB
            port=3306,              # Puerto por defecto para MariaDB/MySQL
            user='glpi',            # Usuario de la base de datos
            password='abc123.',     # Contraseña del usuario
            database='glpi'         # Nombre de la base de datos
        )

        if connection.is_connected():
            print("Conexión exitosa a la base de datos")
            cursor = connection.cursor()

            # Identificador de la entidad raíz
            root_entity_id = 0

            # Obtener todas las entidades diferentes a la entidad raíz
            cursor.execute("SELECT id FROM glpi_entities WHERE id != %s;", (root_entity_id,))
            other_entities = cursor.fetchall()

            # Obtener todas las notificaciones de la entidad raíz
            cursor.execute("SELECT * FROM glpi_notifications WHERE entities_id = %s;", (root_entity_id,))
            notifications = cursor.fetchall()

            for notification in notifications:
                # Insertar la notificación para cada entidad
                insert_notification_query = """
                INSERT INTO glpi_notifications (name, entities_id, itemtype, event, comment, is_recursive, is_active, date_mod, date_creation, allow_response)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """

                for entity_id in other_entities:
                    entity_id = entity_id[0]
                    values = (notification[1], entity_id, notification[3], notification[4], notification[5], notification[6], notification[7], notification[8], notification[9], notification[10])
                    cursor.execute(insert_notification_query, values)
                    new_notification_id = cursor.lastrowid

                    # Insertar en glpi_notifications_notificationtemplates
                    cursor.execute("SELECT * FROM glpi_notifications_notificationtemplates WHERE notifications_id = %s;", (notification[0],))
                    templates = cursor.fetchall()
                    insert_template_query = """
                    INSERT INTO glpi_notifications_notificationtemplates (notifications_id, mode, notificationtemplates_id)
                    VALUES (%s, %s, %s);
                    """
                    for template in templates:
                        cursor.execute(insert_template_query, (new_notification_id, template[2], template[3]))

                    # Insertar en glpi_notificationtargets
                    cursor.execute("SELECT * FROM glpi_notificationtargets WHERE notifications_id = %s;", (notification[0],))
                    targets = cursor.fetchall()
                    insert_target_query = """
                    INSERT INTO glpi_notificationtargets (items_id, type, notifications_id)
                    VALUES (%s, %s, %s);
                    """
                    for target in targets:
                        cursor.execute(insert_target_query, (target[0], target[1], new_notification_id))

                    # Insertar en glpi_notificationtemplates
                    cursor.execute("SELECT * FROM glpi_notificationtemplates WHERE id IN (SELECT notificationtemplates_id FROM glpi_notifications_notificationtemplates WHERE notifications_id = %s);", (notification[0],))
                    notification_templates = cursor.fetchall()
                    insert_notification_template_query = """
                    INSERT INTO glpi_notificationtemplates (name, itemtype, date_mod, comment, css, date_creation)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """
                    for nt in notification_templates:
                        cursor.execute(insert_notification_template_query, (nt[1], nt[2], nt[3], nt[4], nt[5], nt[6]))
                        new_template_id = cursor.lastrowid

                        # Insertar en glpi_notificationtemplatetranslations
                        cursor.execute("SELECT * FROM glpi_notificationtemplatetranslations WHERE notificationtemplates_id = %s;", (nt[0],))
                        translations = cursor.fetchall()
                        insert_translation_query = """
                        INSERT INTO glpi_notificationtemplatetranslations (notificationtemplates_id, language, subject, content_text, content_html)
                        VALUES (%s, %s, %s, %s, %s);
                        """
                        for translation in translations:
                            cursor.execute(insert_translation_query, (new_template_id, translation[1], translation[2], translation[3], translation[4]))

            connection.commit()
            print("Notificaciones duplicadas exitosamente.")

    except Error as e:
        print(f"Error al conectar a la base de datos o al realizar operaciones: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    connect_to_database()