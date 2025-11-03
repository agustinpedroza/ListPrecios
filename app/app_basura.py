from flask import Flask, session, redirect, url_for
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Controllers.auth_controller import auth_bp

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Cambia esto por una clave segura

# Registrar el blueprint de autenticación
app.register_blueprint(auth_bp)


# Redirige a /login si no está autenticado
@app.route('/')
def home():
    if 'usuario' in session:
        return f"Bienvenido, {session['usunombre']}!"
    return redirect(url_for('auth.login_form'))

# Formulario de login simple para pruebas
@app.route('/login', methods=['GET'])
def login_form():
    return '''
        <form method="post" action="/login">
            Usuario: <input type="text" name="usuario"><br>
            Contraseña (hex): <input type="text" name="password"><br>
            <input type="submit" value="Entrar">
        </form>
    '''

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)