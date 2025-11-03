from flask import Flask, session, redirect, url_for, render_template, request, jsonify
from datetime import timedelta
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from Controllers.auth_controller import auth_bp

app = Flask(__name__)
app.secret_key = 'Shirly2000'  # Cambia esto por una clave segura
app.permanent_session_lifetime = timedelta(hours=1)

# --- Endpoints de administración de usuarios (solo perfil 3) ---

@app.before_request
def make_session_permanent():
    session.permanent = True

def require_admin():
    perfil = session.get('perfil')
    # Acepta tanto int como str para perfil 3
    return 'usuario' not in session or str(perfil) != '3'

@app.route('/api/usuarios/datos')
def api_datos_usuario():
    if require_admin():
        return jsonify({'error': 'No autorizado'}), 403
    usuario = request.args.get('usuario', '').strip()
    if not usuario:
        return jsonify({'error': 'Usuario requerido'}), 400
    from services.sql_connection import ejecutar_consulta
    query = '''SELECT USU_NOMBRE, USU_PERFIL, USU_CODALMACEN, USU_ESTADO FROM PS_USUARIOS WHERE USU_CODUSUARIO = ?'''
    filas, _ = ejecutar_consulta(query, (usuario,))
    if not filas:
        return jsonify({'ok': False, 'usuario': None})
    nombre, perfil, almacen, estado = filas[0]
    return jsonify({'ok': True, 'usuario': {'nombre': nombre, 'perfil': str(perfil), 'almacen': almacen, 'estado': estado}})

# --- Endpoints de administración de usuarios (solo perfil 3) ---

def require_admin():
    perfil = session.get('perfil')
    return 'usuario' not in session or str(perfil) != '3'

@app.route('/api/usuarios/editar', methods=['POST'])
def api_editar_usuario():
    if require_admin():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    nombre_completo = data.get('nombre_completo', '').strip()
    perfil = data.get('perfil', '').strip()
    almacen = data.get('almacen', '').strip()
    estado = data.get('estado', '').strip()
    if not usuario or not nombre_completo or not almacen or not estado:
        return jsonify({'error': 'Todos los campos son requeridos'}), 400
    from services.sql_connection import ejecutar_consulta
    query = '''UPDATE PS_USUARIOS SET USU_NOMBRE = ?, USU_PERFIL = ?, USU_CODALMACEN = ?, USU_ESTADO = ? WHERE USU_CODUSUARIO = ?'''
    try:
        ejecutar_consulta(query, (nombre_completo, perfil, almacen, estado, usuario), modo="escritura")
        return jsonify({'ok': True})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/usuarios/crear', methods=['POST'])
def api_crear_usuario():
    if require_admin():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    nombre_completo = data.get('nombre_completo', '').strip()
    clave = data.get('clave', '').strip()
    almacen = data.get('almacen', '').strip()
    perfil = int(data.get('perfil', 1))
    estado = data.get('estado', 'A')
    if not usuario or not clave or not nombre_completo or not almacen or not estado:
        return jsonify({'error': 'Todos los campos son requeridos'}), 400
    from services.sql_connection import ejecutar_consulta
    import hashlib
    # Verificar si el usuario ya existe
    query_check = '''SELECT COUNT(*) FROM PS_USUARIOS WHERE USU_CODUSUARIO = ?'''
    rows, _ = ejecutar_consulta(query_check, (usuario,))
    if rows and rows[0][0] > 0:
        return jsonify({'error': 'El usuario ya existe'}), 409
    clave_bytes = clave.encode('utf-16le')
    hash_bytes = hashlib.sha256(clave_bytes).digest()
    # Ajusta el INSERT para guardar nombre y almacén
    codempresa = session.get('codempresa', 1)
    query = '''INSERT INTO PS_USUARIOS (USU_CODUSUARIO, USU_NOMBRE, USU_PWDWEB, USU_PERFIL, USU_CODALMACEN, USU_CODEMPRESA, USU_ESTADO) VALUES (?, ?, ?, ?, ?, ?, ?)'''
    try:
        ejecutar_consulta(query, (usuario, nombre_completo, hash_bytes, perfil, almacen, codempresa, 'A'), modo="escritura")
        return jsonify({'ok': True})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/usuarios/eliminar', methods=['POST'])
def api_eliminar_usuario():
    if require_admin():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    if not usuario:
        return jsonify({'error': 'Usuario requerido'}), 400
    from services.sql_connection import ejecutar_consulta
    query = '''DELETE FROM PS_USUARIOS WHERE USU_CODUSUARIO = ?'''
    try:
        ejecutar_consulta(query, (usuario,))
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/cambiar_clave', methods=['POST'])
def api_cambiar_clave():
    if require_admin():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    nueva_clave = data.get('nueva_clave', '').strip()
    if not usuario or not nueva_clave:
        return jsonify({'error': 'Usuario y nueva clave requeridos'}), 400
    from services.sql_connection import ejecutar_consulta
    import hashlib
    clave_bytes = nueva_clave.encode('utf-16le')
    hash_bytes = hashlib.sha256(clave_bytes).digest()
    query = '''UPDATE PS_USUARIOS SET USU_PWDWEB = ? WHERE USU_CODUSUARIO = ?'''
    try:
        ejecutar_consulta(query, (hash_bytes, usuario))
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin_usuarios')
def admin_usuarios():
    print('DEBUG perfil en sesión:', session.get('perfil'))
    if 'usuario' not in session or str(session.get('perfil')) != '3':
        return redirect(url_for('busqueda'))
    from services.sql_connection import ejecutar_consulta
    query = 'SELECT ALM_CODALMACEN, ALM_NOMALMACEN FROM PS_ALMACENES ORDER BY ALM_NOMALMACEN'
    almacenes, _ = ejecutar_consulta(query)
    return render_template('admin_usuarios.html', almacenes=almacenes)

# Página de búsqueda después del login
@app.route('/busqueda')
def busqueda():
    if 'usuario' not in session:
        return redirect(url_for('login_form'))
    codalmacen = session.get('almacen', '')
    print(f"[DEBUG] codalmacen en sesión: {codalmacen}")
    nomalmacen = session.get('nomalmacen', '')
    from services.sql_connection import ejecutar_consulta
    query = 'SELECT ALM_CODALMACEN, ALM_NOMALMACEN FROM PS_ALMACENES ORDER BY ALM_NOMALMACEN'
    almacenes, _ = ejecutar_consulta(query)
    return render_template('busqueda.html', codalmacen=codalmacen, nomalmacen=nomalmacen, almacenes=almacenes)

# Endpoint de búsqueda de productos (AJAX)
@app.route('/buscar_productos')
def buscar_productos():
    if 'usuario' not in session:
        return jsonify([])
    filtro = request.args.get('q', '').strip()
    codalmacen = request.args.get('almacen') or session.get('almacen', '')
    if not filtro:
        return jsonify([])
    from services.sql_connection import ejecutar_consulta
    print(f"🔎 Filtro: '{filtro}' | Almacén: '{codalmacen}'")
    if '@' in filtro:
        parte1, parte2 = filtro.split('@', 1)
        parte1 = parte1.strip()
        parte2 = parte2.strip()
        query = '''
            SELECT REFERENCIA, DESCRIPCION, MARCA
            FROM LISTAS_DE_PRECIOS
            WHERE DESCRIPCION LIKE ? AND DESCRIPCION LIKE ? AND CODALMACEN = ?
            ORDER BY DESCRIPCION
        '''
        filtro_sql1 = f'{parte1}%'
        filtro_sql2 = f'%{parte2}%'
        print(f"🔎 Filtro avanzado: comienza por '{parte1}', contiene '{parte2}'")
        filas, _ = ejecutar_consulta(query, (filtro_sql1, filtro_sql2, codalmacen))
    else:
        query = '''
            SELECT REFERENCIA, DESCRIPCION, MARCA
            FROM LISTAS_DE_PRECIOS
            WHERE DESCRIPCION LIKE ? AND CODALMACEN = ?
            ORDER BY DESCRIPCION
        '''
        filtro_sql = f'{filtro}%'
        print(f"🔎 Valor LIKE enviado: '{filtro_sql}' | Almacén: '{codalmacen}'")
        filas, _ = ejecutar_consulta(query, (filtro_sql, codalmacen))
    print(f"🔎 Resultado consulta: {filas}")
    productos = [
        {'referencia': f[0], 'descripcion': f[1], 'marca': f[2]} for f in filas
    ] if filas else []
    return jsonify(productos)

# Endpoint para detalle de producto
@app.route('/detalle_producto/<path:referencia>')
def detalle_producto(referencia):
    if 'usuario' not in session:
        return redirect(url_for('login_form'))
    from services.sql_connection import ejecutar_consulta
    query = '''
        SELECT REFERENCIA, DESCRIPCION, MARCA, PRECIO, UBICACION, SALDO
        FROM LISTAS_DE_PRECIOS
        WHERE RTRIM(REFERENCIA) = RTRIM(?)
    '''
    filas, _ = ejecutar_consulta(query, (referencia,))
    if not filas:
        return 'Producto no encontrado', 404
    prod = filas[0]
    precio_fmt = '{:,.0f}'.format(prod[3]).replace(',', '.')
    saldo_fmt = '{:,.0f}'.format(prod[5]) if len(prod) > 5 and prod[5] is not None else '0'
    return render_template('detalle_producto.html', referencia=prod[0], descripcion=prod[1], marca=prod[2], precio=precio_fmt, ubicacion=prod[4], saldo=saldo_fmt)

# Registrar el blueprint de autenticación
app.register_blueprint(auth_bp)

# Redirige a /login si no está autenticado
@app.route('/')
def home():
    if 'usuario' in session:
        return redirect(url_for('busqueda'))
    return redirect(url_for('login_form'))

@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@app.context_processor
def inject_session():
    return dict(session=session)

if __name__ == '__main__':
    from services.sql_connection import conectar_sqlserver, is_connection_active
    print('🔎 Probando conexión a SQL Server...')
    conn = conectar_sqlserver()
    if conn and is_connection_active(conn):
        print('✅ Conexión a SQL Server activa.')
    else:
        print('❌ No se pudo conectar a SQL Server.')
    app.run(debug=False, host="0.0.0.0", port=8080)