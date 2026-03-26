#   https://www.youtube.com/watch?v=nh0Jeclyvt8

from tkinter import *

#   Ventana. 

ventana = Tk()
ventana.title("Calculadora")

#   Indice --> string en la posición 0.

i = 0

#   Label para introducir texto.

e_texto = Entry(ventana, font = ("Calibri 20"))
e_texto.grid(row = 0, column = 0, columnspan = 4, padx = 50, pady = 5)

#   Funciones.

def clic_boton(valor):

    #   Al pulsar un botón recogemos su valor en la siguiente posición del string.

    global i
    e_texto.insert(i, valor)
    i += 1

def borrar():

    #   Al pulsar el botón de borrar se borra el string y se devuelve a la posición 0.

    e_texto.delete(0, END)
    i = 0

def operacion():

    #   Al pulsar el botón de igual llamamos a la función eval para que procese la operación del string.

    ecuacion = e_texto.get()
    resultado = eval(ecuacion)
    e_texto.delete(0, END)
    e_texto.insert(0, resultado)
    i = 0
    
#   Botones. LLamamos a las funciones según corresponda con lambda.

boton1 = Button(ventana, text = "1", width = 5, height = 2, command = lambda: clic_boton(1))
boton2 = Button(ventana, text = "2", width = 5, height = 2, command = lambda: clic_boton(2))
boton3 = Button(ventana, text = "3", width = 5, height = 2, command = lambda: clic_boton(3))
boton4 = Button(ventana, text = "4", width = 5, height = 2, command = lambda: clic_boton(4))
boton5 = Button(ventana, text = "5", width = 5, height = 2, command = lambda: clic_boton(5))
boton6 = Button(ventana, text = "6", width = 5, height = 2, command = lambda: clic_boton(6))
boton7 = Button(ventana, text = "7", width = 5, height = 2, command = lambda: clic_boton(7))
boton8 = Button(ventana, text = "8", width = 5, height = 2, command = lambda: clic_boton(8))
boton9 = Button(ventana, text = "9", width = 5, height = 2, command = lambda: clic_boton(9))
boton0 = Button(ventana, text = "0", width = 13, height = 2, command = lambda: clic_boton(0))

boton_borrar = Button(ventana, text = "AC", width = 5, height = 2, command = lambda: borrar())
boton_parentesis1 = Button(ventana, text = "(", width = 5, height = 2, command = lambda: clic_boton("("))
boton_parentesis2 = Button(ventana, text = ")", width = 5, height = 2, command = lambda: clic_boton(")"))
boton_punto = Button(ventana, text = ".", width = 5, height = 2, command = lambda: clic_boton("."))

boton_division = Button(ventana, text = "/", width = 5, height = 2, command = lambda: clic_boton("/"))
boton_multiplicacion = Button(ventana, text = "x", width = 5, height = 2, command = lambda: clic_boton("*"))
boton_suma = Button(ventana, text = "+", width = 5, height = 2, command = lambda: clic_boton("+"))
boton_resta = Button(ventana, text = "-", width = 5, height = 2, command = lambda: clic_boton("-"))
boton_igual = Button(ventana, text = "=", width = 5, height = 2, command = lambda: operacion())

#   Ordenamos los botones en pantalla usando grid.

    #   Fila 1.

boton_borrar.grid(row = 1, column = 0, padx = 5, pady = 5)
boton_parentesis1.grid(row = 1, column = 1, padx = 5, pady = 5)
boton_parentesis2.grid(row = 1, column = 2, padx = 5, pady = 5)
boton_division.grid(row = 1, column = 3, padx = 5, pady = 5)

    #   Fila 2.

boton7.grid(row = 2, column = 0, padx = 5, pady = 5)
boton8.grid(row = 2, column = 1, padx = 5, pady = 5)
boton9.grid(row = 2, column = 2, padx = 5, pady = 5)
boton_multiplicacion.grid(row = 2, column = 3, padx = 5, pady = 5)

    #   Fila 3.

boton4.grid(row = 3, column = 0, padx = 5, pady = 5)
boton5.grid(row = 3, column = 1, padx = 5, pady = 5)
boton6.grid(row = 3, column = 2, padx = 5, pady = 5)
boton_suma.grid(row = 3, column = 3, padx = 5, pady = 5)

    #   Fila 4.

boton1.grid(row = 4, column = 0, padx = 5, pady = 5)
boton2.grid(row = 4, column = 1, padx = 5, pady = 5)
boton3.grid(row = 4, column = 2, padx = 5, pady = 5)
boton_resta.grid(row = 4, column = 3, padx = 5, pady = 5)

    #   Fila 5.

boton0.grid(row = 5, column = 0, columnspan = 2, padx = 5, pady = 5)
boton_punto.grid(row = 5, column = 2, padx = 5, pady = 5)
boton_igual.grid(row = 5, column = 3, padx = 5, pady = 5)

#   Reconoce todos los eventos.

ventana.mainloop()
