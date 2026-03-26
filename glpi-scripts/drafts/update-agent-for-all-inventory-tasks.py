# NO FUNCIONA. REVISAR ESTRUCTURA DE LA BBDD Y ARREGLAR.

import mysql.connector
from mysql.connector import Error

def update_task_actors_and_associations_by_deviceid(agent_deviceid):
    try:
        # Conectar a la base de datos
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

            # Obtener el ID y la entidad del agente usando deviceid
            cursor.execute("""
                SELECT id, entities_id FROM glpi_agents WHERE deviceid = %s
            """, (agent_deviceid,))
            result = cursor.fetchone()
            if result:
                agent_id, entity_id = result
                print(f"Agente encontrado: ID = {agent_id}, Entidad = {entity_id}")

                # Obtener las tareas de inventario para la entidad del agente
                cursor.execute("""
                    SELECT id, actors FROM glpi_plugin_glpiinventory_taskjobs
                    WHERE entities_id = %s
                """, (entity_id,))

                tasks = cursor.fetchall()

                for task_id, actors_json in tasks:
                    if actors_json:
                        # Convertir el JSON en una lista de diccionarios
                        actors = eval(actors_json)
                        # Verificar si el agente ya está en la lista de actores
                        if not any(agent['Agent'] == str(agent_id) for agent in actors):
                            actors.append({"Agent": str(agent_id)})
                    else:
                        actors = [{"Agent": str(agent_id)}]

                    # Actualizar la columna actors para la tarea
                    cursor.execute("""
                        UPDATE glpi_plugin_glpiinventory_taskjobs
                        SET actors = %s
                        WHERE id = %s
                    """, (str(actors), task_id))
                    print(f"Tarea {task_id} actualizada con el agente {agent_id}")

                # Actualizar la asociación de tareas de trabajo con la tarea principal
                cursor.execute("""
                    SELECT id FROM glpi_plugin_glpiinventory_tasks WHERE entities_id = %s
                """, (entity_id,))
                tasks = cursor.fetchall()

                for task_id, in tasks:
                    cursor.execute("""
                        UPDATE glpi_plugin_glpiinventory_taskjobs
                        SET plugin_glpiinventory_tasks_id = %s
                        WHERE entities_id = %s AND plugin_glpiinventory_tasks_id = 0
                    """, (task_id, entity_id))
                    print(f"Tarea de trabajo actualizada para la tarea principal {task_id}")

                connection.commit()
                print("Actualización completada.")

            else:
                print(f"No se encontró el agente con deviceid {agent_deviceid}")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    agent_deviceid = 'ubuntu-desktop-2024-09-11-20-53-39'  # Cambia esto por el deviceid del agente que deseas asignar
    update_task_actors_and_associations_by_deviceid(agent_deviceid)