from datetime import datetime
from urllib.parse import quote_plus
from app.extensions import db

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(40), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    delivery_type = db.Column(db.String(40), nullable=False, default="retirada")
    status = db.Column(db.String(40), nullable=False, default="recebido")
    notes = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(60), nullable=True)
    cash_change_for = db.Column(db.String(40), nullable=True)
    delivery_neighborhood = db.Column(db.String(120), nullable=True)
    delivery_fee = db.Column(db.Float, nullable=False, default=0)
    total = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def total_br(self):
        return f"R$ {self.total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def whatsapp_message(self):
        linhas = [
            f"Olá! Quero confirmar o pedido #{self.id}.",
            "",
            "Itens do pedido:",
        ]
        for item in self.items:
            linhas.append(f"{item.quantity}x {item.product.name} - R$ {item.subtotal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        linhas.extend([
            "",
            f"Taxa de entrega: R$ {self.delivery_fee:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            f"Total: {self.total_br()}",
            "",
            f"Nome: {self.customer_name}",
            f"Telefone: {self.customer_phone}",
            f"Tipo: {self.delivery_type}",
        ])
        if self.delivery_type == "entrega" and self.delivery_neighborhood:
            linhas.append(f"Bairro: {self.delivery_neighborhood}")
        if self.delivery_type == "entrega" and self.address:
            linhas.append(f"Endereço: {self.address}")
        if self.payment_method:
            linhas.extend(["", f"Forma de pagamento: {self.payment_method}"])
        if self.cash_change_for:
            linhas.append(f"Troco para: R$ {self.cash_change_for}")
        if self.notes:
            linhas.extend(["", f"Observações: {self.notes}"])
        return "\n".join(linhas)

    def status_label(self, status=None):
        labels = {
            "recebido": "Recebido",
            "em preparo": "Em preparo",
            "saiu para entrega": "Saiu para entrega",
            "finalizado": "Finalizado",
            "cancelado": "Cancelado",
        }
        return labels.get(status or self.status, status or self.status)

    def status_message(self, status=None):
        status = status or self.status
        mensagens = {
            "recebido": f"Olá, {self.customer_name}! Seu pedido #{self.id} foi recebido pela Chapa do Bairro. 🍔",
            "em preparo": f"Olá, {self.customer_name}! Seu pedido #{self.id} já está em preparo. 🔥",
            "saiu para entrega": f"Olá, {self.customer_name}! Seu pedido #{self.id} saiu para entrega. 🛵",
            "finalizado": f"Olá, {self.customer_name}! Seu pedido #{self.id} foi finalizado. Obrigado pela preferência! ✅",
            "cancelado": f"Olá, {self.customer_name}. Seu pedido #{self.id} foi cancelado. Caso tenha dúvida, fale com a gente.",
        }
        linhas = [mensagens.get(status, f"Olá, {self.customer_name}! Status do pedido #{self.id}: {self.status_label(status)}.")]
        linhas.append(f"Total: {self.total_br()}")
        if self.delivery_type == "entrega" and self.address:
            linhas.append(f"Endereço: {self.address}")
        return "\n".join(linhas)

    def whatsapp_status_url(self, status=None):
        return f"https://wa.me/{self.customer_phone}?text={quote_plus(self.status_message(status))}"

class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")
