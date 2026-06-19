from datetime import datetime, timedelta
from urllib.parse import quote_plus
import csv
import io
import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, Response, session
from app.core.security import login_required
from app.extensions import db
from sqlalchemy import func
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.ingredient import Ingredient
from app.models.coupon import Coupon
from app.models.customer import Customer
from app.models.delivery_zone import DeliveryZone
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.upload_service import save_upload

admin_bp = Blueprint("admin", __name__)

ALLOWED_ORDER_STATUSES = ["recebido", "em preparo", "saiu para entrega", "finalizado", "cancelado"]

def _admin_name():
    return session.get("admin_user") or "admin"

def _audit(action, entity=None, entity_id=None, details=None, commit=False):
    log = AuditLog(username=_admin_name(), action=action, entity=entity, entity_id=str(entity_id) if entity_id is not None else None, details=details)
    db.session.add(log)
    if commit:
        db.session.commit()
    return log


@admin_bp.route("/")
@login_required
def dashboard():
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())

    total_products = Product.query.count()
    active_products = Product.query.filter_by(active=True).count()
    orders_today = Order.query.filter(Order.created_at >= start).count()
    orders_today_list = Order.query.filter(Order.created_at >= start).all()
    revenue_today = sum(o.total for o in orders_today_list if o.status != "cancelado")
    completed_today = len([o for o in orders_today_list if o.status == "finalizado"])
    avg_ticket = (revenue_today / orders_today) if orders_today else 0

    latest_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    pending_orders = Order.query.filter(Order.status.in_(["recebido", "em preparo", "saiu para entrega"])).count()
    canceled_today = len([o for o in orders_today_list if o.status == "cancelado"])
    cancel_rate = (canceled_today / orders_today * 100) if orders_today else 0
    low_stock = Ingredient.query.filter(Ingredient.current_stock <= Ingredient.minimum_stock, Ingredient.active == True).count()
    total_customers = Customer.query.count()
    vip_customers = Customer.query.filter(Customer.total_orders >= 10).count()
    blocked_customers = Customer.query.filter_by(blocked=True).count()
    audit_today = AuditLog.query.filter(AuditLog.created_at >= start).count()

    best_sellers = (
        db.session.query(Product.name, func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status != "cancelado")
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    peak_hour_rows = (
        db.session.query(func.strftime('%H', Order.created_at).label('hour'), func.count(Order.id))
        .filter(Order.status != "cancelado")
        .group_by('hour')
        .order_by(func.count(Order.id).desc())
        .limit(1)
        .all()
    )
    peak_hour = f"{peak_hour_rows[0][0]}h" if peak_hour_rows else "-"

    week_sales = []
    max_week_revenue = 1
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        day_orders = Order.query.filter(Order.created_at >= day_start, Order.created_at < day_end, Order.status != "cancelado").all()
        day_revenue = sum(o.total for o in day_orders)
        max_week_revenue = max(max_week_revenue, day_revenue)
        week_sales.append({
            "label": day.strftime("%d/%m"),
            "orders": len(day_orders),
            "revenue": day_revenue,
        })

    for item in week_sales:
        item["height"] = int((item["revenue"] / max_week_revenue) * 100) if max_week_revenue else 0

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        active_products=active_products,
        orders_today=orders_today,
        revenue_today=revenue_today,
        completed_today=completed_today,
        avg_ticket=avg_ticket,
        latest_orders=latest_orders,
        pending_orders=pending_orders,
        low_stock=low_stock,
        week_sales=week_sales,
        best_sellers=best_sellers,
        peak_hour=peak_hour,
        cancel_rate=cancel_rate,
        total_customers=total_customers,
        vip_customers=vip_customers,
        blocked_customers=blocked_customers,
        audit_today=audit_today
    )


def _settings_path():
    return os.path.join(current_app.static_folder, "site_settings.json")

def _load_site_settings():
    defaults = {
        "store_name": current_app.config.get("STORE_NAME", "Chapa do Bairro"),
        "slogan": current_app.config.get("STORE_SLOGAN", "Chapa quente, hambúrguer de verdade."),
        "primary_color": "#D96A1B",
        "delivery_time": "25 a 40 min",
        "open_message": "Estamos abertos para pedidos!",
        "pix_key": "",
        "pix_owner": "Chapa do Bairro",
        "pix_city": "MONTES CLAROS",
        "store_address": "",
        "instagram": "",
        "opening_hours": "Terça a domingo, 18h às 23h",
        "closed_message": "Estamos fechados no momento. Volte no nosso horário de atendimento!",
        "minimum_order": "0",
        "service_fee": "0",
        "allow_pickup": "on",
        "allow_coupon": "on",
        "require_notes": "",
        "allow_out_of_stock": "",
        "hero_title": "CHAPA QUENTE, HAMBÚRGUER DE VERDADE.",
        "hero_badge": "🔥 Mais pedido do bairro",
        "hero_video_enabled": "on",
        "dark_mode": "on",
        "kitchen_sound": "on",
        "kitchen_autorefresh": "15",
        "kitchen_fullscreen": "",
        "auto_print_ticket": "",
        "floating_ticket_enabled": "on",
        "floating_ticket_style": "horizontal",
        "floating_ticket_coupon": "CHAPA10",
        "floating_ticket_reward_product_id": "",
        "floating_ticket_text": "Ganhe desconto especial no seu primeiro pedido!",
        "whatsapp_received": "Olá! Recebemos seu pedido na Chapa do Bairro. Em breve ele entra em preparo. 🍔🔥",
        "whatsapp_preparing": "Seu pedido já está em preparo na chapa. 🔥",
        "whatsapp_delivery": "Seu pedido saiu para entrega. 🛵",
        "whatsapp_pickup_ready": "Seu pedido está pronto para retirada. 🍔",
        "whatsapp_done": "Pedido entregue! Obrigado por comprar com a Chapa do Bairro. ⭐"
    }
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            defaults.update(json.load(f))
    except Exception:
        pass
    return defaults

def _save_site_settings(data):
    with open(_settings_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@admin_bp.route("/fretes", methods=["GET", "POST"])
@login_required
def delivery_zones():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Informe o nome do bairro.", "error")
            return redirect(url_for("admin.delivery_zones"))
        zone_id = request.form.get("zone_id")
        zone = DeliveryZone.query.get(int(zone_id)) if zone_id else DeliveryZone(name=name)
        zone.name = name
        zone.fee = float((request.form.get("fee") or "0").replace(",", "."))
        zone.estimated_time = request.form.get("estimated_time", "").strip() or "25 a 40 min"
        zone.active = request.form.get("active") == "on"
        db.session.add(zone)
        db.session.commit()
        flash("Bairro e taxa de entrega salvos.", "success")
        return redirect(url_for("admin.delivery_zones"))

    zonas = DeliveryZone.query.order_by(DeliveryZone.active.desc(), DeliveryZone.name).all()
    return render_template("admin/delivery_zones.html", zonas=zonas)

@admin_bp.route("/fretes/<int:zone_id>/toggle", methods=["POST"])
@login_required
def toggle_delivery_zone(zone_id):
    zone = DeliveryZone.query.get_or_404(zone_id)
    zone.active = not zone.active
    db.session.commit()
    flash("Bairro atualizado.", "success")
    return redirect(url_for("admin.delivery_zones"))

@admin_bp.route("/fretes/<int:zone_id>/excluir", methods=["POST"])
@login_required
def delete_delivery_zone(zone_id):
    zone = DeliveryZone.query.get_or_404(zone_id)
    db.session.delete(zone)
    db.session.commit()
    flash("Bairro removido.", "success")
    return redirect(url_for("admin.delivery_zones"))

@admin_bp.route("/configuracoes", methods=["GET", "POST"])
@login_required
def settings():
    settings = _load_site_settings()
    if request.method == "POST":
        settings.update({
            "store_name": request.form.get("store_name", settings["store_name"]).strip(),
            "slogan": request.form.get("slogan", settings["slogan"]).strip(),
            "primary_color": request.form.get("primary_color", settings["primary_color"]).strip() or "#D96A1B",
            "delivery_time": request.form.get("delivery_time", settings["delivery_time"]).strip(),
            "open_message": request.form.get("open_message", settings["open_message"]).strip(),
            "pix_key": request.form.get("pix_key", settings.get("pix_key", "")).strip(),
            "pix_owner": request.form.get("pix_owner", settings.get("pix_owner", "Chapa do Bairro")).strip(),
            "pix_city": request.form.get("pix_city", settings.get("pix_city", "MONTES CLAROS")).strip() or "MONTES CLAROS",
            "store_address": request.form.get("store_address", settings.get("store_address", "")).strip(),
            "instagram": request.form.get("instagram", settings.get("instagram", "")).strip(),
            "opening_hours": request.form.get("opening_hours", settings.get("opening_hours", "")).strip(),
            "closed_message": request.form.get("closed_message", settings.get("closed_message", "")).strip(),
            "minimum_order": request.form.get("minimum_order", settings.get("minimum_order", "0")).strip() or "0",
            "service_fee": request.form.get("service_fee", settings.get("service_fee", "0")).strip() or "0",
            "allow_pickup": "on" if request.form.get("allow_pickup") == "on" else "",
            "allow_coupon": "on" if request.form.get("allow_coupon") == "on" else "",
            "require_notes": "on" if request.form.get("require_notes") == "on" else "",
            "allow_out_of_stock": "on" if request.form.get("allow_out_of_stock") == "on" else "",
            "hero_title": request.form.get("hero_title", settings.get("hero_title", "")).strip(),
            "hero_badge": request.form.get("hero_badge", settings.get("hero_badge", "")).strip(),
            "hero_video_enabled": "on" if request.form.get("hero_video_enabled") == "on" else "",
            "dark_mode": "on" if request.form.get("dark_mode") == "on" else "",
            "kitchen_sound": "on" if request.form.get("kitchen_sound") == "on" else "",
            "kitchen_autorefresh": request.form.get("kitchen_autorefresh", settings.get("kitchen_autorefresh", "15")).strip() or "15",
            "kitchen_fullscreen": "on" if request.form.get("kitchen_fullscreen") == "on" else "",
            "auto_print_ticket": "on" if request.form.get("auto_print_ticket") == "on" else "",
            "floating_ticket_enabled": "on" if request.form.get("floating_ticket_enabled") == "on" else "",
            "floating_ticket_style": request.form.get("floating_ticket_style", settings.get("floating_ticket_style", "horizontal")).strip() or "horizontal",
            "floating_ticket_coupon": request.form.get("floating_ticket_coupon", settings.get("floating_ticket_coupon", "CHAPA10")).strip().upper() or "CHAPA10",
            "floating_ticket_reward_product_id": request.form.get("floating_ticket_reward_product_id", settings.get("floating_ticket_reward_product_id", "")).strip(),
            "floating_ticket_text": request.form.get("floating_ticket_text", settings.get("floating_ticket_text", "")).strip(),
            "whatsapp_received": request.form.get("whatsapp_received", settings.get("whatsapp_received", "")).strip(),
            "whatsapp_preparing": request.form.get("whatsapp_preparing", settings.get("whatsapp_preparing", "")).strip(),
            "whatsapp_delivery": request.form.get("whatsapp_delivery", settings.get("whatsapp_delivery", "")).strip(),
            "whatsapp_pickup_ready": request.form.get("whatsapp_pickup_ready", settings.get("whatsapp_pickup_ready", "")).strip(),
            "whatsapp_done": request.form.get("whatsapp_done", settings.get("whatsapp_done", "")).strip(),
        })
        _save_site_settings(settings)
        _audit("Atualizou configurações", "configuracoes", None, "Painel de configurações")
        db.session.commit()
        flash("Configurações atualizadas com sucesso.", "success")
        return redirect(url_for("admin.settings"))
    produtos = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template("admin/settings.html", settings=settings, produtos=produtos)

@admin_bp.route("/campanhas")
@login_required
def campaigns():
    cutoff = datetime.utcnow() - timedelta(days=15)
    rows = (
        db.session.query(Order.customer_name, Order.customer_phone, func.max(Order.created_at).label("last_order"), func.count(Order.id).label("total_orders"))
        .filter(Order.status == "finalizado")
        .group_by(Order.customer_phone, Order.customer_name)
        .having(func.max(Order.created_at) < cutoff)
        .order_by(func.max(Order.created_at).asc())
        .limit(30)
        .all()
    )
    cupom = "VOLTE10"
    mensagem = "Sentimos sua falta na Chapa do Bairro! Use o cupom VOLTE10 e ganhe 10% OFF no próximo pedido. 🍔🔥"
    return render_template("admin/campaigns.html", clientes=rows, cupom=cupom, mensagem=mensagem)

@admin_bp.route("/cupons", methods=["GET", "POST"])
@login_required
def coupons():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        if not code:
            flash("Informe o código do cupom.", "error")
            return redirect(url_for("admin.coupons"))
        coupon = Coupon.query.filter_by(code=code).first() or Coupon(code=code)
        coupon.description = request.form.get("description", "").strip()
        coupon.discount_type = request.form.get("discount_type", "percent")
        coupon.value = float((request.form.get("value") or "0").replace(",", "."))
        coupon.minimum_total = float((request.form.get("minimum_total") or "0").replace(",", "."))
        coupon.active = request.form.get("active") == "on"
        db.session.add(coupon)
        db.session.commit()
        _audit("Salvou cupom", "cupom", coupon.id, coupon.code)
        db.session.commit()
        flash("Cupom salvo com sucesso.", "success")
        return redirect(url_for("admin.coupons"))
    cupons = Coupon.query.order_by(Coupon.active.desc(), Coupon.code).all()
    return render_template("admin/coupons.html", cupons=cupons)

@admin_bp.route("/cupons/<int:coupon_id>/toggle", methods=["POST"])
@login_required
def toggle_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.active = not coupon.active
    db.session.commit()
    flash("Cupom atualizado.", "success")
    return redirect(url_for("admin.coupons"))

@admin_bp.route("/clientes")
@login_required
def customers():
    clientes = Customer.query.order_by(Customer.blocked.asc(), Customer.total_spent.desc()).all()
    return render_template("admin/customers.html", clientes=clientes)

@admin_bp.route("/clientes/<int:customer_id>/editar", methods=["POST"])
@login_required
def update_customer(customer_id):
    cliente = Customer.query.get_or_404(customer_id)
    cliente.tags = request.form.get("tags", "").strip()
    cliente.notes = request.form.get("notes", "").strip()
    db.session.commit()
    _audit("Atualizou cliente", "cliente", cliente.id, f"Tags: {cliente.tags}", commit=True)
    flash("Cliente atualizado.", "success")
    return redirect(url_for("admin.customers"))

@admin_bp.route("/clientes/<int:customer_id>/bloquear", methods=["POST"])
@login_required
def toggle_customer_block(customer_id):
    cliente = Customer.query.get_or_404(customer_id)
    cliente.blocked = not cliente.blocked
    action = "Bloqueou cliente" if cliente.blocked else "Desbloqueou cliente"
    _audit(action, "cliente", cliente.id, f"{cliente.name} / {cliente.phone}")
    db.session.commit()
    flash("Status do cliente atualizado.", "success")
    return redirect(url_for("admin.customers"))

@admin_bp.route("/clientes/<int:customer_id>/excluir", methods=["POST"])
@login_required
def delete_customer(customer_id):
    admin_password = request.form.get("admin_password", "")
    admin_username = session.get("admin_user")

    admin_user = None
    if admin_username:
        admin_user = User.query.filter_by(username=admin_username, active=True).first()
    if not admin_user:
        admin_user = User.query.filter_by(role="admin", active=True).first()

    if not admin_user or not admin_user.check_password(admin_password):
        flash("Senha do admin incorreta. Cliente não foi excluído.", "error")
        return redirect(url_for("admin.customers"))

    cliente = Customer.query.get_or_404(customer_id)
    nome = cliente.name or cliente.phone or f"Cliente #{cliente.id}"
    _audit("Excluiu cliente", "cliente", cliente.id, f"{nome} / {cliente.phone}")
    db.session.delete(cliente)
    db.session.commit()
    flash(f"Cliente {nome} excluído com sucesso.", "success")
    return redirect(url_for("admin.customers"))

@admin_bp.route("/relatorios/exportar")
@login_required
def export_reports_csv():
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Pedido", "Cliente", "Telefone", "Status", "Pagamento", "Entrega", "Total", "Data"])
    pedidos = Order.query.order_by(Order.created_at.desc()).all()
    for p in pedidos:
        writer.writerow([p.id, p.customer_name, p.customer_phone, p.status, p.payment_method or "", p.delivery_type, f"{p.total:.2f}", p.created_at.strftime("%d/%m/%Y %H:%M")])
    return Response(output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=relatorio_chapa_do_bairro.csv"})


@admin_bp.route("/auditoria")
@login_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("admin/audit_logs.html", logs=logs)

@admin_bp.route("/backup/completo")
@login_required
def backup_full():
    data = {
        "exportado_em": datetime.utcnow().isoformat(),
        "produtos": [{"id": p.id, "nome": p.name, "preco": p.price, "ativo": p.active} for p in Product.query.order_by(Product.id).all()],
        "clientes": [{"id": c.id, "nome": c.name, "telefone": c.phone, "pedidos": c.total_orders, "gasto": c.total_spent, "pontos": c.loyalty_points, "bloqueado": c.blocked, "tags": c.tags} for c in Customer.query.order_by(Customer.id).all()],
        "pedidos": [{"id": o.id, "cliente": o.customer_name, "telefone": o.customer_phone, "status": o.status, "total": o.total, "data": o.created_at.isoformat() if o.created_at else None} for o in Order.query.order_by(Order.id).all()],
        "insumos": [{"id": i.id, "nome": i.name, "estoque": i.current_stock, "minimo": i.minimum_stock, "unidade": i.unit, "custo": i.cost_per_unit} for i in Ingredient.query.order_by(Ingredient.id).all()],
        "cupons": [{"codigo": c.code, "ativo": c.active, "valor": c.value, "tipo": c.discount_type} for c in Coupon.query.order_by(Coupon.id).all()],
    }
    _audit("Exportou backup completo", "backup", None, "JSON completo", commit=True)
    return Response(json.dumps(data, ensure_ascii=False, indent=2), mimetype="application/json; charset=utf-8", headers={"Content-Disposition": "attachment; filename=backup_chapa_do_bairro.json"})

@admin_bp.route("/categorias")
@login_required
def categories():
    categorias = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categorias=categorias)

@admin_bp.route("/categorias/nova", methods=["POST"])
@login_required
def create_category():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Informe o nome da categoria.", "error")
        return redirect(url_for("admin.categories"))

    if Category.query.filter_by(name=name).first():
        flash("Categoria já existe.", "error")
        return redirect(url_for("admin.categories"))

    db.session.add(Category(name=name, active=True))
    db.session.commit()
    flash("Categoria criada.", "success")
    return redirect(url_for("admin.categories"))

@admin_bp.route("/categorias/<int:category_id>/toggle", methods=["POST"])
@login_required
def toggle_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.active = not category.active
    db.session.commit()
    flash("Categoria atualizada.", "success")
    return redirect(url_for("admin.categories"))

@admin_bp.route("/produtos")
@login_required
def products():
    produtos = Product.query.order_by(Product.name).all()
    return render_template("admin/products.html", produtos=produtos)

@admin_bp.route("/produtos/novo", methods=["GET", "POST"])
@login_required
def create_product():
    categorias = Category.query.filter_by(active=True).order_by(Category.name).all()

    if request.method == "POST":
        try:
            image = save_upload(request.files.get("image"), current_app.config["UPLOAD_FOLDER"])
            product = Product(
                name=request.form["name"],
                description=request.form["description"],
                price=float(request.form["price"].replace(",", ".")),
                category_id=int(request.form["category_id"]),
                image=image,
                active=request.form.get("active") == "on",
                featured=request.form.get("featured") == "on",
            )
            db.session.add(product)
            db.session.commit()
            _audit("Criou produto", "produto", product.id, product.name)
            db.session.commit()
            flash("Produto criado com sucesso.", "success")
            return redirect(url_for("admin.products"))
        except Exception as e:
            flash(str(e), "error")

    return render_template("admin/product_form.html", produto=None, categorias=categorias)

@admin_bp.route("/produtos/<int:product_id>/editar", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    produto = Product.query.get_or_404(product_id)
    categorias = Category.query.filter_by(active=True).order_by(Category.name).all()

    if request.method == "POST":
        try:
            image = save_upload(request.files.get("image"), current_app.config["UPLOAD_FOLDER"])

            produto.name = request.form["name"]
            produto.description = request.form["description"]
            produto.price = float(request.form["price"].replace(",", "."))
            produto.category_id = int(request.form["category_id"])
            produto.active = request.form.get("active") == "on"
            produto.featured = request.form.get("featured") == "on"

            if image:
                produto.image = image

            db.session.commit()
            _audit("Atualizou produto", "produto", produto.id, produto.name)
            db.session.commit()
            flash("Produto atualizado com sucesso.", "success")
            return redirect(url_for("admin.products"))
        except Exception as e:
            flash(str(e), "error")

    return render_template("admin/product_form.html", produto=produto, categorias=categorias)

@admin_bp.route("/produtos/<int:product_id>/excluir", methods=["POST"])
@login_required
def delete_product(product_id):
    produto = Product.query.get_or_404(product_id)
    _audit("Excluiu produto", "produto", produto.id, produto.name)
    db.session.delete(produto)
    db.session.commit()
    flash("Produto excluído.", "success")
    return redirect(url_for("admin.products"))

@admin_bp.route("/pedidos")
@login_required
def orders():
    pedidos = Order.query.filter(Order.status != "finalizado").order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", pedidos=pedidos, title="Pedidos em aberto")

@admin_bp.route("/pedidos/historico")
@login_required
def order_history():
    pedidos = Order.query.filter_by(status="finalizado").order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", pedidos=pedidos, title="Histórico de pedidos finalizados")

@admin_bp.route("/financeiro/caixa")
@login_required
def cash_closing():
    """Fechamento de caixa do dia com separação por forma de pagamento."""
    date_str = request.args.get("date")
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
    except ValueError:
        selected_date = datetime.utcnow().date()

    start = datetime.combine(selected_date, datetime.min.time())
    end = start + timedelta(days=1)

    pedidos = Order.query.filter(Order.created_at >= start, Order.created_at < end).order_by(Order.created_at.asc()).all()
    valid_orders = [o for o in pedidos if o.status != "cancelado"]
    canceled_orders = [o for o in pedidos if o.status == "cancelado"]

    payment_rows = {}
    for order in valid_orders:
        key = (order.payment_method or "Não informado").strip() or "Não informado"
        payment_rows.setdefault(key, {"count": 0, "total": 0})
        payment_rows[key]["count"] += 1
        payment_rows[key]["total"] += order.total or 0

    delivery_total = sum(o.delivery_fee or 0 for o in valid_orders)
    gross_total = sum(o.total or 0 for o in valid_orders)
    orders_count = len(valid_orders)
    avg_ticket = (gross_total / orders_count) if orders_count else 0

    return render_template(
        "admin/cash_closing.html",
        selected_date=selected_date,
        pedidos=pedidos,
        payment_rows=payment_rows,
        delivery_total=delivery_total,
        gross_total=gross_total,
        orders_count=orders_count,
        avg_ticket=avg_ticket,
        canceled_count=len(canceled_orders),
        canceled_total=sum(o.total or 0 for o in canceled_orders),
    )

@admin_bp.route("/relatorios/lucro-produtos")
@login_required
def product_profit_report():
    """Relatório de custo, margem e lucro estimado por produto."""
    produtos = Product.query.order_by(Product.name).all()
    rows = []
    for produto in produtos:
        cost = produto.production_cost()
        profit = produto.estimated_profit()
        margin = (profit / produto.price * 100) if produto.price else 0
        rows.append({
            "produto": produto,
            "cost": cost,
            "profit": profit,
            "margin": margin,
            "possible": produto.max_possible_production(),
        })
    rows.sort(key=lambda r: r["profit"], reverse=True)
    return render_template("admin/product_profit_report.html", rows=rows)

@admin_bp.route("/relatorios")
@login_required
def reports():
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    month_start = datetime(today.year, today.month, 1)
    finalized = Order.query.filter_by(status="finalizado")
    revenue_today = finalized.filter(Order.created_at >= start).with_entities(func.coalesce(func.sum(Order.total), 0)).scalar() or 0
    revenue_month = finalized.filter(Order.created_at >= month_start).with_entities(func.coalesce(func.sum(Order.total), 0)).scalar() or 0
    orders_today = finalized.filter(Order.created_at >= start).count()
    orders_month = finalized.filter(Order.created_at >= month_start).count()
    avg_ticket = (revenue_month / orders_month) if orders_month else 0
    by_payment = db.session.query(Order.payment_method, func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).filter(Order.status == "finalizado").group_by(Order.payment_method).all()
    return render_template("admin/reports.html", revenue_today=revenue_today, revenue_month=revenue_month, orders_today=orders_today, orders_month=orders_month, avg_ticket=avg_ticket, by_payment=by_payment)


@admin_bp.route("/relatorios/imprimir")
@login_required
def print_reports():
    today = datetime.utcnow().date()
    month_start = datetime(today.year, today.month, 1)
    finalized = Order.query.filter_by(status="finalizado")
    orders = finalized.filter(Order.created_at >= month_start).order_by(Order.created_at.desc()).all()
    revenue_month = sum(o.total for o in orders)
    avg_ticket = (revenue_month / len(orders)) if orders else 0
    best_sellers = (
        db.session.query(Product.name, func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == "finalizado", Order.created_at >= month_start)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )
    return render_template("admin/report_print.html", orders=orders, revenue_month=revenue_month, avg_ticket=avg_ticket, best_sellers=best_sellers, today=today)


@admin_bp.route("/cozinha")
@login_required
def kitchen_panel():
    pedidos = Order.query.filter(Order.status.in_(["recebido", "em preparo", "saiu para entrega"])).order_by(Order.created_at.asc()).all()
    colunas = [
        ("recebido", "🟡 Recebidos"),
        ("em preparo", "🔵 Em preparo"),
        ("saiu para entrega", "🛵 Saiu para entrega"),
    ]
    return render_template("admin/kitchen.html", pedidos=pedidos, colunas=colunas)

@admin_bp.route("/entregadores")
@login_required
def delivery_team():
    entregadores = [
        {"nome": "João", "telefone": "(35) 99999-0001", "status": "Disponível"},
        {"nome": "Carlos", "telefone": "(35) 99999-0002", "status": "Em entrega"},
        {"nome": "Moto reserva", "telefone": "(35) 99999-0003", "status": "Aguardando"},
    ]
    pedidos_entrega = Order.query.filter(Order.status == "saiu para entrega").order_by(Order.created_at.desc()).all()
    return render_template("admin/delivery.html", entregadores=entregadores, pedidos_entrega=pedidos_entrega)

@admin_bp.route("/pedidos/<int:order_id>")
@login_required
def order_detail(order_id):
    pedido = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", pedido=pedido)


@admin_bp.route("/pedidos/<int:order_id>/comanda")
@login_required
def print_order_ticket(order_id):
    pedido = Order.query.get_or_404(order_id)
    return render_template("admin/order_ticket.html", pedido=pedido, now=datetime.utcnow())

@admin_bp.route("/pedidos/<int:order_id>/whatsapp")
@login_required
def order_whatsapp(order_id):
    pedido = Order.query.get_or_404(order_id)
    number = current_app.config["WHATSAPP_NUMBER"]
    mensagem = quote_plus(pedido.whatsapp_message())
    return redirect(f"https://wa.me/{number}?text={mensagem}")


@admin_bp.route("/pedidos/<int:order_id>/whatsapp/status")
@login_required
def order_whatsapp_status(order_id):
    pedido = Order.query.get_or_404(order_id)
    status = request.args.get("status", pedido.status).strip().lower()
    if status not in ALLOWED_ORDER_STATUSES:
        status = pedido.status
    return redirect(pedido.whatsapp_status_url(status))

def _restore_stock_for_order(pedido):
    """Devolve ao estoque os ingredientes consumidos por um pedido cancelado."""
    for item in pedido.items:
        product = item.product
        if not product:
            continue
        for recipe_item in product.recipe_items:
            ingredient = recipe_item.ingredient
            if not ingredient:
                continue
            returned_quantity = (recipe_item.quantity or 0) * (item.quantity or 0)
            if returned_quantity > 0:
                ingredient.current_stock = (ingredient.current_stock or 0) + returned_quantity


@admin_bp.route("/pedidos/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    pedido = Order.query.get_or_404(order_id)
    novo_status = request.form.get("status", "").strip().lower()
    if novo_status not in ALLOWED_ORDER_STATUSES:
        flash("Status inválido.", "error")
        return redirect(url_for("admin.order_detail", order_id=pedido.id))

    if novo_status == "cancelado":
        _restore_stock_for_order(pedido)
        _audit("Cancelou pedido", "pedido", pedido.id, f"Pedido cancelado e estoque devolvido")
        db.session.delete(pedido)
        db.session.commit()
        flash("Pedido cancelado, excluído e estoque devolvido.", "success")
        return redirect(url_for("admin.orders"))

    antigo_status = pedido.status
    pedido.status = novo_status
    _audit("Alterou status do pedido", "pedido", pedido.id, f"{antigo_status} -> {novo_status}")
    db.session.commit()
    flash("Status do pedido atualizado.", "success")
    return redirect(url_for("admin.order_detail", order_id=pedido.id))
