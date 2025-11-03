from flask import session, redirect, url_for
from functools import wraps

def login_requerido(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "usuario" not in session or not session["usuario"]:
            return redirect(url_for("home"))
        return func(*args, **kwargs)
    return wrapper
