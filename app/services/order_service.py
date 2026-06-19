import re

from app.extensions import db
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.coupon import Coupon
from app.models.customer import Customer
from app.models.delivery_zone import DeliveryZone

DEFAULT_DELIVERY_FEES = {
    "Centro": 5.00,
    "Todos os Santos": 6.00,
    "Major Prates": 8.00,
    "Maristela": 10.00,
}



def normalize_customer_phone(phone):
    """Padroniza telefone para WhatsApp com região fixa: 55 + 35 + celular.

    No checkout o cliente digita apenas o celular com 9 dígitos.
    Exemplo: cliente digita 999999999 e o sistema salva 5535999999999.
    Mantém compatibilidade caso o número venha completo.
    """
    digits = re.sub(r"\D", "", phone or "")

    # Novo padrão do site: cliente informa apenas o celular.
    if len(digits) == 9 and digits.startswith("9"):
        digits = "5535" + digits

    # Compatibilidade: se vier DDD + celular, completa com 55.
    elif len(digits) == 11 and digits.startswith("35"):
        digits = "55" + digits

    # Compatibilidade: se vier sem o 9 inicial por algum navegador antigo, bloqueia.
    if not re.fullmatch(r"55359\d{8}", digits):
        raise ValueError("Telefone inválido. Digite apenas o celular com 9 dígitos. Ex: 999999999")

    return digits


def _money_br(value):
    return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def apply_coupon_discount(subtotal, coupon_code):
    code = (coupon_code or "").strip().upper()
    if not code:
        return 0, None
    coupon = Coupon.query.filter_by(code=code, active=True).first()
    if not coupon:
        raise ValueError("Cupom inválido ou inativo.")
    discount = coupon.discount_for(subtotal)
    if discount <= 0:
        raise ValueError(f"Cupom válido apenas para pedidos acima de {_money_br(coupon.minimum_total)}.")
    return discount, coupon

def update_customer_loyalty(order):
    customer = Customer.query.filter_by(phone=order.customer_phone).first()
    if not customer:
        customer = Customer(name=order.customer_name, phone=order.customer_phone)
        db.session.add(customer)
    customer.name = order.customer_name
    customer.total_orders = (customer.total_orders or 0) + 1
    customer.total_spent = (customer.total_spent or 0) + (order.total or 0)
    customer.loyalty_points = (customer.loyalty_points or 0) + int(order.total or 0)
    customer.last_order_at = order.created_at
    return customer

def _ensure_customer_can_order(phone):
    customer = Customer.query.filter_by(phone=phone).first()
    if customer and customer.blocked:
        raise ValueError("Este celular está bloqueado para novos pedidos. Entre em contato com a loja pelo WhatsApp.")
    return customer

def get_delivery_fees():
    zones = DeliveryZone.query.filter_by(active=True).order_by(DeliveryZone.name).all()
    if zones:
        return {zone.name: zone.fee for zone in zones}
    return DEFAULT_DELIVERY_FEES.copy()

def calculate_delivery_fee(delivery_type, neighborhood):
    if delivery_type != "entrega":
        return 0
    zone = DeliveryZone.query.filter_by(name=neighborhood, active=True).first()
    if zone:
        return zone.fee
    return DEFAULT_DELIVERY_FEES.get(neighborhood, 0)

def validate_product_stock(product, quantity):
    """Confere se a ficha técnica permite vender a quantidade solicitada."""
    if not product.recipe_items:
        return
    faltantes = []
    for recipe_item in product.recipe_items:
        ingredient = recipe_item.ingredient
        needed = (recipe_item.quantity or 0) * quantity
        available = ingredient.current_stock or 0
        if needed > available:
            faltantes.append(f"{ingredient.name}: precisa {needed:g} {ingredient.unit}, tem {available:g} {ingredient.unit}")
    if faltantes:
        raise ValueError(f"Estoque insuficiente para {product.name}. " + " | ".join(faltantes))

def _deduct_stock_for_item(product, quantity):
    """Baixa o estoque com base na ficha técnica do produto."""
    validate_product_stock(product, quantity)
    for recipe_item in product.recipe_items:
        ingredient = recipe_item.ingredient
        used_quantity = (recipe_item.quantity or 0) * quantity
        if used_quantity <= 0:
            continue
        ingredient.current_stock = max((ingredient.current_stock or 0) - used_quantity, 0)


def _add_product_to_order(order, product, quantity):
    subtotal = product.price * quantity
    item = OrderItem(
        product_id=product.id,
        quantity=quantity,
        unit_price=product.price,
        subtotal=subtotal
    )
    order.items.append(item)
    _deduct_stock_for_item(product, quantity)
    return subtotal


def create_order_from_form(form):
    product_ids = form.getlist("product_id")
    quantities = form.getlist("quantity")

    customer_phone = normalize_customer_phone(form.get("customer_phone"))
    _ensure_customer_can_order(customer_phone)

    delivery_type = form.get("delivery_type", "retirada")
    delivery_neighborhood = form.get("delivery_neighborhood", "").strip()
    delivery_fee = calculate_delivery_fee(delivery_type, delivery_neighborhood)

    order = Order(
        customer_name=form.get("customer_name"),
        customer_phone=customer_phone,
        address=form.get("address"),
        delivery_type=delivery_type,
        delivery_neighborhood=delivery_neighborhood,
        delivery_fee=delivery_fee,
        notes=form.get("notes"),
        payment_method=form.get("payment_method"),
        cash_change_for=form.get("cash_change_for"),
        status="recebido",
        total=0
    )

    total = 0

    for product_id, quantity in zip(product_ids, quantities):
        quantity = int(quantity or 0)
        if quantity <= 0:
            continue

        product = Product.query.get(int(product_id))
        if not product or not product.active:
            continue

        total += _add_product_to_order(order, product, quantity)

    if not order.items:
        raise ValueError("Selecione pelo menos um produto.")

    order.total = total + delivery_fee
    db.session.add(order)
    db.session.commit()
    return order


def create_order_from_cart(items, form):
    nome = form.get("customer_name", "").strip()
    telefone = normalize_customer_phone(form.get("customer_phone", ""))
    _ensure_customer_can_order(telefone)
    forma_pagamento = form.get("payment_method", "").strip()
    tipo_entrega = form.get("delivery_type", "retirada")
    endereco = form.get("address", "").strip()
    bairro = form.get("delivery_neighborhood", "").strip()
    troco_para = form.get("cash_change_for", "").strip()

    if not nome or not telefone or not forma_pagamento:
        raise ValueError("Preencha nome, telefone e forma de pagamento.")
    if tipo_entrega == "entrega" and not endereco:
        raise ValueError("Informe o endereço para entrega.")
    if tipo_entrega == "entrega" and not bairro:
        raise ValueError("Selecione o bairro para calcular a taxa de entrega.")
    if forma_pagamento == "Dinheiro" and not troco_para:
        raise ValueError("Informe para quanto precisa de troco.")

    order = Order(
        customer_name=nome,
        customer_phone=telefone,
        address=endereco,
        delivery_type=tipo_entrega,
        delivery_neighborhood=bairro,
        delivery_fee=calculate_delivery_fee(tipo_entrega, bairro),
        notes=form.get("notes", "").strip(),
        payment_method=forma_pagamento,
        cash_change_for=troco_para,
        status="recebido",
        total=0
    )

    total = 0
    for item in items:
        product = item["product"]
        quantity = int(item["quantity"] or 0)
        if quantity > 0 and product.active:
            total += _add_product_to_order(order, product, quantity)

    if not order.items:
        raise ValueError("Carrinho vazio ou produtos indisponíveis.")

    coupon_discount = 0
    coupon = None
    if form.get("coupon_code"):
        coupon_discount, coupon = apply_coupon_discount(total, form.get("coupon_code"))
        order.notes = (order.notes + "\n" if order.notes else "") + f"Cupom aplicado: {coupon.code} (-{_money_br(coupon_discount)})"

    order.total = max(total - coupon_discount, 0) + order.delivery_fee
    db.session.add(order)
    db.session.flush()
    update_customer_loyalty(order)
    db.session.commit()
    return order
