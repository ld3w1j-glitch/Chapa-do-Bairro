from app.extensions import db

class DeliveryZone(db.Model):
    __tablename__ = "delivery_zones"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    fee = db.Column(db.Float, nullable=False, default=0)
    estimated_time = db.Column(db.String(40), nullable=True, default="25 a 40 min")
    active = db.Column(db.Boolean, default=True)

    def fee_br(self):
        return f"R$ {self.fee:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
