from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username, active=True).first()

        if user and user.check_password(password):
            session["admin_logged_in"] = True
            session["admin_user"] = user.username
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Usuário ou senha inválidos.", "error")

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do painel.", "success")
    return redirect(url_for("auth.login"))
