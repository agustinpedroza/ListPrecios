from flask import Blueprint, request, jsonify, session, current_app
import sys
from services.sql_connection import ejecutar_consulta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        usuario     = data.get("usuario", "").strip()
        password_hex= data.get("password", "").strip()    # ej. "a3f1..."

        # 1) convierte el hex string a bytes
        try:
            password_bytes = bytes.fromhex(password_hex)
        except ValueError:
            return jsonify({ "mensaje": "❌ Formato de contraseña inválido." })

        # 2) Recupera el hash guardado para este usuario (debug)
        sql_debug = """
          SELECT USU_PWDWEB
          FROM PS_USUARIOS
          WHERE USU_CODUSUARIO = ?
        """
        filas_debug, _ = ejecutar_consulta(sql_debug, (usuario,))
        if not filas_debug:
            return jsonify({ "mensaje": "❌ Usuario no existe." })

        stored_bytes = filas_debug[0][0]  # VARBINARY(32)
        print(f"DEBUG HASH » stored: {stored_bytes.hex()}  vs  computed: {password_hex}")

        # 3) Ahora sí hace la validación real con el binario
        query = """
          SELECT 
            USU_CODUSUARIO, USU_NOMBRE, USU_PERFIL, 
            USU_CODALMACEN, ALM_NOMALMACEN, EMP_NOMEMPRESA, EMP_CODEMPRESA
          FROM PS_USUARIOS
            JOIN PS_EMPRESAS   ON USU_CODEMPRESA = EMP_CODEMPRESA
            JOIN PS_ALMACENES ON USU_CODALMACEN  = ALM_CODALMACEN
          WHERE USU_CODUSUARIO = ? 
            AND USU_PWDWEB     = ?
        """
        filas, cols = ejecutar_consulta(query, (usuario, password_bytes))
        print("👉 Resultado SQL:", filas)

        if filas:
            codus, usunombre, perfil, alm, nomalm, nomemp, codempresa = filas[0]
            session['usuario']    = codus
            session['usunombre']  = usunombre
            session['perfil']     = perfil
            session['almacen']    = alm
            session['nomalmacen'] = nomalm
            session['nomempresa'] = nomemp
            session['codempresa'] = codempresa
            try:
                current_app.CODEMPRESA = codempresa
                app_module = sys.modules.get('app')
                if app_module is not None:
                    try:
                        setattr(app_module, 'CODEMPRESA', codempresa)
                    except Exception:
                        pass
            except Exception:
                pass
            return jsonify({
                "mensaje":   "✅ Autenticación exitosa",
                "usuario":   codus,
                "usunombre": usunombre,
                "perfil":    perfil,
                "almacen":   alm,
                "nomalmacen":nomalm,
                "nomempresa":nomemp,
                "codempresa":codempresa,
                "redirigir": "/busqueda"
            })
        else:
            return jsonify({ "mensaje": "❌ Usuario o contraseña incorrectos." })

    except Exception as e:
        print("⚠️ Error en /login:", e)
        return jsonify({ "mensaje": f"❌ Error interno: {e}" }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        usuario = session.get('usuario', 'desconocido')
        session.clear()
        print(f"🚪 Usuario {usuario} cerró sesión")
        return jsonify({ "mensaje": "✅ Sesión cerrada exitosamente" })
    except Exception as e:
        print("⚠️ Error en /logout:", e)
        return jsonify({ "mensaje": f"❌ Error cerrando sesión: {e}" }), 500
