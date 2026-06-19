from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("admin_logged_in"):
            flash("Faça login para acessar o painel.", "error")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view
