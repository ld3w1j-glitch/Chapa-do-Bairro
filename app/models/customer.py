from datetime import datetime
from app.extensions import db

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), unique=True, nullable=False, index=True)
    total_orders = db.Column(db.Integer, nullable=False, default=0)
    total_spent = db.Column(db.Float, nullable=False, default=0)
    loyalty_points = db.Column(db.Integer, nullable=False, default=0)
    last_order_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    blocked = db.Column(db.Boolean, nullable=False, default=False)
    tags = db.Column(db.String(255), nullable=True, default="")
    notes = db.Column(db.Text, nullable=True)

    def level(self):
        if self.total_orders >= 10 or self.total_spent >= 500:
            return "VIP"
        if self.total_orders >= 4:
            return "Frequente"
        return "Novo"
