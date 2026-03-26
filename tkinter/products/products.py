# Ejecutar previamente init_db.py para crear la base de datos.

#   Importamos las librerías

from tkinter import ttk
from tkinter import *
import sqlite3

#   Clase que contiene mi aplicación

class Producto: 

    db_name = 'database.db'


    #   Función que muestra la ventana principal del programa

    def __init__(self, ventana):

        self.ventana = ventana
        self.ventana.title('Aplicación de productos')

        #   Contenedor de elementos

        frame = LabelFrame(self.ventana, text= 'Registrar un nuevo producto')
        frame.grid(row = 0, column = 0, columnspan = 3, pady = 20)

        #   Input para el nombre

        Label(frame, text = 'Nombre: ').grid(row = 1, column = 0)
        self.nombre = Entry(frame)
        self.nombre.focus()
        self.nombre.grid(row = 1, column = 1)

        #   Input para el precio

        Label(frame, text = 'Precio: ').grid(row = 2 , column = 0)
        self.precio = Entry(frame)
        self.precio.grid(row = 2, column = 1)

        #   Botón para añadir un producto

        ttk.Button(frame, text = 'Añadir', command = self.añadir_producto).grid(row = 3, columnspan = 2, sticky = W + E)

        #   Mensajes de salida

        self.message = Label(text = '', fg = 'red')
        self.message.grid(row = 3, column = 0, columnspan = 2, sticky = W + E)

        #   Tabla

        self.tree = ttk.Treeview(height = 10, columns = 2)  
        self.tree.grid(row = 4, column = 0, columnspan = 2)
        self.tree.heading('#0', text = 'Nombre', anchor = CENTER)
        self.tree.heading('#1', text = 'Precio', anchor = CENTER)

        #   Rellenar la fila --> revisar si va aquí

        self.mostrar_productos()

        #   Botón para editar un producto   
        
        ttk.Button(text = 'Editar', command = self.editar_producto).grid(row = 5, column = 0, sticky = W + E)

        #   Botón para borrar un producto

        ttk.Button(text = 'Borrar', command = self.borrar_producto).grid(row = 5, column = 1, sticky = W + E)


    #   Función para hacer consultas SQL a nuestra base de datos 

    def hacer_consulta(self, query, parametros = ()):

        with sqlite3.connect(self.db_name) as conn:

            cursor = conn.cursor()
            result = cursor.execute(query, parametros)
            conn.commit()

        return result


    #   Función para mostrar el resultado de las consultas. Limpiamos la tabla, hacemos la consulta y rellenamos la tabla con los datos.

    def mostrar_productos(self):

        #   Limpiar tabla

        registros = self.tree.get_children()

        for elemento in registros:

            self.tree.delete(elemento)

        #   Consultar datos

        query = 'SELECT * FROM producto ORDER BY precio DESC'
        db_filas = self.hacer_consulta(query)

        #   Rellenar tabla
        
        for fila in db_filas:
            
            self.tree.insert('', 0, text = fila[1], values = fila[2])
    

    #   Función para validar que los campos nombre y precios no están vacíos al añadir un producto.

    def validacion(self):

        return len(self.nombre.get()) != 0 and len(self.precio.get()) != 0

    
    #   Función para añadir un producto. Si se cumple la validación añadimos el registro a la base de datos y mostramos un mensaje para confirmar. Si no se cumple lanzamos un mensaje de error.

    def añadir_producto(self):

        if self.validacion(): 

            query = 'INSERT INTO producto VALUES (NULL, ?, ?)'
            parametros = (self.nombre.get(), self.precio.get())
            self.hacer_consulta(query, parametros)
            self.nombre.delete(0, END)
            self.precio.delete(0, END)
            self.message['text'] = 'Registro añadido correctamente'

        else:
            
            self.message['text'] = 'Los campos nombre y precio son obligatorios'
        
        self.mostrar_productos()


    #   Función para borrar un producto. Si no se seleccionó ningún producto lanzamos un error. Si se borra correctamente mostramos un mensaje para confirmar y llamamos a la función mostrar_productos para actualizar los datos que se muestran en pantalla.
    
    def borrar_producto(self):

        self.message['text'] = ''

        try:
            
            self.tree.item(self.tree.selection())['text'][0]

        except IndexError as e:

            self.message['text'] = 'Por favor, selecciona un registro'

            return 
        
        nombre = self.tree.item(self.tree.selection())['text']
        query = 'DELETE FROM producto where nombre = ?'
        self.hacer_consulta(query, (nombre, ))
        self.message['text'] = 'Registro borrado correctamente'
        self.mostrar_productos()

    
    #   Función para editar un producto. Se abre una ventana nueva que muestra los valores anteriores y dos input para introducir los nuevos valores. Cuando el usuario pulsa el botón 'Actualizar' llamamos a la función editar_registros que cambia los valores en la base de datos.

    def editar_producto(self):

        self.message['text'] = ''

        try:
            
            self.tree.item(self.tree.selection())['text'][0]

        except IndexError as e:

            self.message['text'] = 'Por favor, selecciona un registro'
            
            return 

        nombre_anterior = self.tree.item(self.tree.selection())['text']
        precio_anterior = self.tree.item(self.tree.selection())['values'][0]

        #   Ventana nueva

        self.editar_ventana = Toplevel()
        self.editar_ventana.title = 'Editar producto'

        #   Nombre anterior

        Label(self.editar_ventana, text = 'Nombre anterior: ').grid(row = 0, column = 1)
        Entry(self.editar_ventana, textvariable = StringVar(self.editar_ventana, value = nombre_anterior), state = 'readonly').grid(row = 0, column = 2)
        
        #   Nombre nuevo

        Label(self.editar_ventana, text = 'Nombre nuevo: ').grid(row = 1, column = 1)
        nombre_nuevo = Entry(self.editar_ventana)
        nombre_nuevo.grid(row = 1, column = 2)

        #   Precio anterior

        Label(self.editar_ventana, text = 'Precio anterior: ').grid(row = 2, column = 1)
        Entry(self.editar_ventana, textvariable = StringVar(self.editar_ventana, value = precio_anterior), state = 'readonly').grid(row = 2, column = 2)
        
        #   Precio nuevo

        Label(self.editar_ventana, text = 'Precio nuevo: ').grid(row = 3, column = 1)
        precio_nuevo = Entry(self.editar_ventana)
        precio_nuevo.grid(row = 3, column = 2)

        Button(self.editar_ventana, text = 'Actualizar', command = lambda: self.editar_registros(nombre_nuevo.get(), nombre_anterior, precio_nuevo.get(), precio_anterior)).grid(row = 4, column = 2, sticky = W + E)

    
    #   Función para actualizar los registros en la base de datos con los valores introducidos por el usuario.
    
    def editar_registros(self, nombre_nuevo, nombre_anterior, precio_nuevo, precio_anterior):

        query = 'UPDATE producto set nombre = ?, precio = ? where nombre = ? and precio = ?'
        parametros = (nombre_nuevo, precio_nuevo, nombre_anterior, precio_anterior)
        self.hacer_consulta(query, parametros)
        self.editar_ventana.destroy()
        self.message['text'] = 'Registro actualizado correctamente'
        self.mostrar_productos()


#   Comprobar que este es el archivo main. Si lo es, mostramos la ventana principal de nuestra aplicación.

if __name__ == '__main__':

    ventana = Tk()
    aplicacion = Producto(ventana)
    ventana.mainloop()
    
