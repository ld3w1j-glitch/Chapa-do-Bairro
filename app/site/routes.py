from urllib.parse import quote_plus
import os
from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash, session, Response
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order
from app.services.order_service import normalize_customer_phone
from app.services.order_service import create_order_from_cart, get_delivery_fees, validate_product_stock
from app.services.pix_service import build_pix_payload

site_bp = Blueprint("site", __name__)

def get_cart():
    return session.get("cart", {})

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

def cart_items():
    cart = get_cart()
    items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if not product or not product.active:
            continue

        quantity = int(quantity)
        subtotal = product.price * quantity
        total += subtotal

        items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return items, total

def money_br(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@site_bp.route("/pix/qrcode")
def pix_qrcode():
    """Retorna um QR Code PIX PNG para o valor informado no checkout."""
    settings = {"pix_key": "", "pix_owner": "Chapa do Bairro", "pix_city": "MONTES CLAROS"}
    settings_path = os.path.join(current_app.static_folder, "site_settings.json")
    try:
        import json
        with open(settings_path, "r", encoding="utf-8") as f:
            settings.update(json.load(f))
    except Exception:
        pass

    try:
        amount = float(str(request.args.get("amount", "0")).replace(",", "."))
    except ValueError:
        amount = 0

    payload = build_pix_payload(
        pix_key=settings.get("pix_key", ""),
        amount=max(amount, 0),
        merchant_name=settings.get("pix_owner", "Chapa do Bairro"),
        merchant_city=settings.get("pix_city", "MONTES CLAROS"),
        txid=request.args.get("txid", "CHAPA") or "CHAPA",
    )
    if not payload:
        return Response("Chave Pix não configurada.", status=400)

    import io
    import qrcode
    img = qrcode.make(payload)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype="image/png")

@site_bp.route("/pix/copia-cola")
def pix_copia_cola():
    settings = {"pix_key": "", "pix_owner": "Chapa do Bairro", "pix_city": "MONTES CLAROS"}
    settings_path = os.path.join(current_app.static_folder, "site_settings.json")
    try:
        import json
        with open(settings_path, "r", encoding="utf-8") as f:
            settings.update(json.load(f))
    except Exception:
        pass
    try:
        amount = float(str(request.args.get("amount", "0")).replace(",", "."))
    except ValueError:
        amount = 0
    payload = build_pix_payload(
        pix_key=settings.get("pix_key", ""),
        amount=max(amount, 0),
        merchant_name=settings.get("pix_owner", "Chapa do Bairro"),
        merchant_city=settings.get("pix_city", "MONTES CLAROS"),
        txid=request.args.get("txid", "CHAPA") or "CHAPA",
    )
    return Response(payload, mimetype="text/plain; charset=utf-8")

@site_bp.route("/")
def home():
    destaques = Product.query.filter_by(active=True, featured=True).limit(4).all()
    items, total = cart_items()
    return render_template("site/home.html", destaques=destaques, cart_count=sum(i["quantity"] for i in items))

@site_bp.route("/acompanhar", methods=["GET", "POST"])
def acompanhar():
    pedidos = []
    telefone = ""
    if request.method == "POST":
        telefone = request.form.get("customer_phone", "")
        try:
            phone = normalize_customer_phone(telefone)
            pedidos = Order.query.filter_by(customer_phone=phone).order_by(Order.created_at.desc()).limit(10).all()
            if not pedidos:
                flash("Nenhum pedido encontrado para este celular.", "error")
        except Exception as e:
            flash(str(e), "error")
    return render_template("site/acompanhar.html", pedidos=pedidos, telefone=telefone)

@site_bp.route("/cardapio")
def cardapio():
    categorias = Category.query.filter_by(active=True).order_by(Category.name).all()
    items, total = cart_items()
    return render_template("site/cardapio.html", categorias=categorias, cart_count=sum(i["quantity"] for i in items))

@site_bp.route("/carrinho")
def carrinho():
    items, total = cart_items()
    return render_template("site/cart.html", items=items, total=total, money_br=money_br)

@site_bp.route("/carrinho/adicionar/<int:produto_id>", methods=["POST", "GET"])
def add_to_cart(produto_id):
    product = Product.query.get_or_404(produto_id)

    if not product.active:
        flash("Produto indisponível.", "error")
        return redirect(url_for("site.cardapio"))

    quantity = int(request.form.get("quantity", 1) or 1)
    if quantity < 1:
        quantity = 1

    cart = get_cart()
    key = str(produto_id)
    new_quantity = int(cart.get(key, 0)) + quantity
    try:
        validate_product_stock(product, new_quantity)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(request.referrer or url_for("site.cardapio"))

    cart[key] = new_quantity
    save_cart(cart)

    flash(f"{product.name} adicionado ao carrinho.", "success")
    return redirect(request.referrer or url_for("site.cardapio"))

@site_bp.route("/carrinho/atualizar", methods=["POST"])
def update_cart():
    cart = get_cart()

    for product_id, quantity in request.form.items():
        if not product_id.startswith("quantity_"):
            continue

        pid = product_id.replace("quantity_", "")
        qty = int(quantity or 0)

        if qty <= 0:
            cart.pop(pid, None)
        else:
            cart[pid] = qty

    save_cart(cart)
    flash("Carrinho atualizado.", "success")
    return redirect(url_for("site.carrinho"))

@site_bp.route("/carrinho/remover/<int:produto_id>", methods=["POST"])
def remove_from_cart(produto_id):
    cart = get_cart()
    cart.pop(str(produto_id), None)
    save_cart(cart)

    flash("Produto removido do carrinho.", "success")
    return redirect(url_for("site.carrinho"))

@site_bp.route("/carrinho/limpar", methods=["POST"])
def clear_cart():
    save_cart({})
    flash("Carrinho limpo.", "success")
    return redirect(url_for("site.cardapio"))

@site_bp.route("/checkout", methods=["GET", "POST"])
def checkout_cart():
    items, total = cart_items()

    if not items:
        flash("Seu carrinho está vazio.", "error")
        return redirect(url_for("site.cardapio"))

    if request.method == "POST":
        try:
            order = create_order_from_cart(items, request.form)
            mensagem = quote_plus(order.whatsapp_message())
            number = current_app.config["WHATSAPP_NUMBER"]
            save_cart({})
            flash(f"Pedido #{order.id} registrado. Você será direcionado para o WhatsApp.", "success")
            return redirect(f"https://wa.me/{number}?text={mensagem}")
        except Exception as e:
            flash(str(e), "error")
            return render_template("site/checkout_cart.html", items=items, total=total, money_br=money_br, delivery_fees=get_delivery_fees())

    return render_template("site/checkout_cart.html", items=items, total=total, money_br=money_br, delivery_fees=get_delivery_fees())

# Mantém compatibilidade com botões antigos.
@site_bp.route("/checkout/<int:produto_id>", methods=["GET", "POST"])
def checkout(produto_id):
    if request.method == "POST":
        return checkout_cart()

    cart = get_cart()
    key = str(produto_id)
    if key not in cart:
        cart[key] = 1
        save_cart(cart)

    return redirect(url_for("site.checkout_cart"))

@site_bp.route("/whatsapp/<int:produto_id>")
def whatsapp(produto_id):
    return redirect(url_for("site.checkout", produto_id=produto_id))
