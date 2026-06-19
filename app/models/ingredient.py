from app.extensions import db

class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    unit = db.Column(db.String(20), nullable=False, default="un")
    current_stock = db.Column(db.Float, nullable=False, default=0)
    minimum_stock = db.Column(db.Float, nullable=False, default=0)
    cost_per_unit = db.Column(db.Float, nullable=False, default=0)
    waste_percent = db.Column(db.Float, nullable=False, default=0)
    active = db.Column(db.Boolean, default=True)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    supplier = db.relationship("Supplier", back_populates="ingredients")

    recipes = db.relationship("RecipeItem", back_populates="ingredient", cascade="all, delete-orphan")

    def cost_br(self):
        return f"R$ {self.cost_per_unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def stock_label(self):
        return f"{self.current_stock:g} {self.unit}"

    def minimum_label(self):
        return f"{self.minimum_stock:g} {self.unit}"

    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock

    def suggested_purchase(self):
        if self.current_stock >= self.minimum_stock:
            return 0
        # sugestão simples: repor até 3x o estoque mínimo
        target = self.minimum_stock * 3
        return max(target - self.current_stock, 0)
