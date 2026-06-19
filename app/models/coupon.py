from datetime import datetime
from app.extensions import db

class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    description = db.Column(db.String(160), nullable=True)
    discount_type = db.Column(db.String(20), nullable=False, default="percent")  # percent ou fixed
    value = db.Column(db.Float, nullable=False, default=0)
    minimum_total = db.Column(db.Float, nullable=False, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def code_clean(self):
        return (self.code or "").strip().upper()

    def value_label(self):
        if self.discount_type == "fixed":
            return f"R$ {self.value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{self.value:g}%"

    def discount_for(self, subtotal):
        subtotal = float(subtotal or 0)
        if not self.active or subtotal < (self.minimum_total or 0):
            return 0
        if self.discount_type == "fixed":
            return min(self.value or 0, subtotal)
        return min(subtotal * ((self.value or 0) / 100), subtotal)
