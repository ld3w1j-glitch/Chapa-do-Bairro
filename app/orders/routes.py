from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.product import Product
from app.services.order_service import create_order_from_form

orders_bp = Blueprint("orders", __name__)

@orders_bp.route("/novo", methods=["GET", "POST"])
def new_order():
    produtos = Product.query.filter_by(active=True).order_by(Product.name).all()

    if request.method == "POST":
        try:
            order = create_order_from_form(request.form)
            flash(f"Pedido #{order.id} criado com sucesso.", "success")
            return redirect(url_for("orders.order_success", order_id=order.id))
        except Exception as e:
            flash(str(e), "error")

    return render_template("orders/new.html", produtos=produtos)

@orders_bp.route("/sucesso/<int:order_id>")
def order_success(order_id):
    return render_template("orders/success.html", order_id=order_id)
