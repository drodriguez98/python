#   https://www.youtube.com/watch?v=fxavwHPJ36o

from flask import Flask, render_template


app = Flask(__name__)

@app.route('/')

def home():
    return render_template('home.html')

@app.route('/about')

def about():
    return render_template('about.html')

#   Modo de prueba: los cambios se aplican sin tener que reiniciar el servidor

if __name__ == '__main__':
    app.run(debug=True)

#   Es para entender. En el vídeo usa bootstrap para dar estilo.